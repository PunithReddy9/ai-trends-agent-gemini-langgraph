# src/services/search_service.py
import requests
import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
from urllib.parse import urlparse
import time
import re
import json

class GoogleSearchService:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_SEARCH_API_KEY')
        self.search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        
        # Require API keys - no mock data fallback
        if not self.api_key or not self.search_engine_id:
            logging.error("❌ Missing Google Search API credentials")
            logging.error("Required environment variables:")
            logging.error("  - GOOGLE_SEARCH_API_KEY")
            logging.error("  - GOOGLE_SEARCH_ENGINE_ID")
            raise ValueError(
                "Google Search API credentials are required. Please set:\n"
                "GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_ENGINE_ID in your .env file"
            )
        
        # Log API key info (safely)
        api_key_preview = f"{self.api_key[:8]}...{self.api_key[-4:]}" if len(self.api_key) > 12 else "***"
        engine_id_preview = f"{self.search_engine_id[:8]}...{self.search_engine_id[-4:]}" if len(self.search_engine_id) > 12 else "***"
        
        logging.info("🔑 Google Search Service initialized successfully")
        logging.info(f"   📋 API Key: {api_key_preview}")
        logging.info(f"   🔍 Search Engine ID: {engine_id_preview}")
        logging.info(f"   🌐 Base URL: {self.base_url}")
    
    def search_ai_content(self, query: str, days_back: int = 7) -> List[Dict]:
        """Search for AI content with enhanced recent news filtering"""
        search_start_time = time.time()
        
        logging.info(f"🔍 Starting search for query: '{query}'")
        logging.info(f"   📅 Time range: {days_back} days back")
        
        try:
            # Enhanced time constraint to focus on recent news
            current_date = datetime.now()
            start_date = current_date - timedelta(days=days_back)
            
            # Format dates for Google Search date filter
            date_range = f"after:{start_date.strftime('%Y-%m-%d')}"
            logging.info(f"   📅 Date filter: {date_range}")
            
            # Enhanced query with news focus
            enhanced_query = f"{query} {date_range}"
            logging.info(f"   🔍 Enhanced query: '{enhanced_query}'")
            
            # Improved search parameters for better news results
            params = {
                'key': self.api_key,
                'cx': self.search_engine_id,
                'q': enhanced_query,
                'num': 10,
                'sort': 'date',  # Sort by date for recent content
                'gl': 'us',      # Geolocation for US results
                'hl': 'en',      # Language
                'safe': 'off',   # Don't filter results
                'tbm': 'nws',    # Search news specifically
                'cr': 'countryUS',  # Country restriction
                'lr': 'lang_en'   # Language restriction
            }
            
            # Log search parameters (without API key)
            safe_params = {k: v for k, v in params.items() if k != 'key'}
            logging.info(f"   ⚙️  Search parameters: {json.dumps(safe_params, indent=2)}")
            
            # Make API request
            api_start_time = time.time()
            logging.info(f"   🌐 Making API request to: {self.base_url}")
            
            response = requests.get(self.base_url, params=params, timeout=15)
            
            api_duration = time.time() - api_start_time
            logging.info(f"   ⏱️  API response time: {api_duration:.2f}s")
            logging.info(f"   📊 Response status: {response.status_code}")
            logging.info(f"   📏 Response size: {len(response.content)} bytes")
            
            response.raise_for_status()
            
            data = response.json()
            
            # Log API response details
            total_results = data.get('searchInformation', {}).get('totalResults', 'unknown')
            search_time = data.get('searchInformation', {}).get('searchTime', 'unknown')
            
            logging.info(f"   📈 Google reported results: {total_results}")
            logging.info(f"   ⏱️  Google search time: {search_time}s")
            
            # Check for API errors or issues
            if 'error' in data:
                error_info = data['error']
                logging.error(f"   ❌ Google API error: {error_info}")
                return []
            
            # Parse initial results
            results = self._parse_search_results(data, query_context="news_search")
            logging.info(f"   ✅ Parsed {len(results)} results from news search")
            
            # If news search returns few results, try general search with news keywords
            if len(results) < 5:
                logging.warning(f"   ⚠️  Only {len(results)} results from news search, trying general search")
                
                params['tbm'] = None  # Remove news filter
                params['q'] = f"{query} news article blog post {date_range}"
                
                logging.info(f"   🔍 Fallback query: '{params['q']}'")
                
                fallback_start_time = time.time()
                response = requests.get(self.base_url, params=params, timeout=15)
                
                fallback_duration = time.time() - fallback_start_time
                logging.info(f"   ⏱️  Fallback API response time: {fallback_duration:.2f}s")
                logging.info(f"   📊 Fallback response status: {response.status_code}")
                
                response.raise_for_status()
                
                data = response.json()
                general_results = self._parse_search_results(data, query_context="general_search")
                results.extend(general_results)
                
                logging.info(f"   ➕ Added {len(general_results)} results from general search")
            
            search_duration = time.time() - search_start_time
            logging.info(f"✅ Search completed in {search_duration:.2f}s")
            logging.info(f"   📊 Total results: {len(results)}")
            
            return results
            
        except requests.Timeout as e:
            logging.error(f"❌ Timeout error for query '{query}': {e}")
            logging.error(f"   ⏱️  Request exceeded 15 second timeout")
            return []
        except requests.ConnectionError as e:
            logging.error(f"❌ Connection error for query '{query}': {e}")
            logging.error(f"   🌐 Failed to connect to Google Search API")
            return []
        except requests.HTTPError as e:
            logging.error(f"❌ HTTP error for query '{query}': {e}")
            logging.error(f"   📊 Response status code: {e.response.status_code if e.response else 'unknown'}")
            if e.response:
                try:
                    error_data = e.response.json()
                    logging.error(f"   📄 Error details: {json.dumps(error_data, indent=2)}")
                except:
                    logging.error(f"   📄 Raw error response: {e.response.text[:500]}")
            return []
        except requests.RequestException as e:
            logging.error(f"❌ Request error for query '{query}': {e}")
            return []
        except json.JSONDecodeError as e:
            logging.error(f"❌ JSON decode error for query '{query}': {e}")
            logging.error(f"   📄 Invalid JSON response from Google API")
            return []
        except Exception as e:
            logging.error(f"❌ Unexpected error in search for query '{query}': {e}")
            logging.error(f"   🔍 Error type: {type(e).__name__}")
            import traceback
            logging.error(f"   📚 Full traceback: {traceback.format_exc()}")
            return []

    def search_recent_ai_news(self, base_query: str, days_back: int = 7) -> List[Dict]:
        """Enhanced search specifically for recent AI news from quality sources"""
        search_start_time = time.time()
        
        logging.info(f"🔍 Starting enhanced AI news search")
        logging.info(f"   📝 Base query: '{base_query}'")
        logging.info(f"   📅 Days back: {days_back}")
        
        all_results = []
        
        # Define high-quality news sources for AI
        news_sources = [
            "techcrunch.com",
            "venturebeat.com", 
            "theverge.com",
            "wired.com",
            "arstechnica.com",
            "reuters.com",
            "zdnet.com",
            "infoworld.com",
            "technologyreview.mit.edu"
        ]
        
        # Define official AI company blogs
        ai_company_blogs = [
            "openai.com",
            "blog.anthropic.com",
            "ai.googleblog.com",
            "blogs.microsoft.com",
            "ai.meta.com",
            "research.google.com",
            "developer.nvidia.com",
            "huggingface.co"
        ]
        
        current_date = datetime.now()
        date_filter = f"after:{(current_date - timedelta(days=days_back)).strftime('%Y-%m-%d')}"
        
        logging.info(f"   📅 Date filter: {date_filter}")
        logging.info(f"   🏢 Official sources to search: {len(ai_company_blogs[:4])}")
        logging.info(f"   📰 News sources to search: {len(news_sources[:5])}")
        
        # Search official AI company sources first (highest priority)
        official_results = 0
        for i, source in enumerate(ai_company_blogs[:4], 1):  # Limit to avoid rate limits
            try:
                logging.info(f"   🏢 Searching official source {i}/4: {source}")
                
                # Simplified query - removed overly restrictive terms
                site_query = f"site:{source} {base_query} {date_filter}"
                results = self._execute_single_search(site_query, source_type="official")
                
                logging.info(f"      ✅ Retrieved {len(results)} results from {source}")
                
                all_results.extend(results)
                official_results += len(results)
                time.sleep(0.3)
            except Exception as e:
                logging.warning(f"      ❌ Failed to search {source}: {e}")
                continue
        
        logging.info(f"   📊 Total official source results: {official_results}")
        
        # Search news sources (medium priority)
        news_results = 0
        for i, source in enumerate(news_sources[:5], 1):  # Limit to top news sources
            try:
                logging.info(f"   📰 Searching news source {i}/5: {source}")
                
                # Simplified query for news sources
                site_query = f"site:{source} {base_query} {date_filter}"
                results = self._execute_single_search(site_query, source_type="news")
                
                logging.info(f"      ✅ Retrieved {len(results)} results from {source}")
                
                all_results.extend(results)
                news_results += len(results)
                time.sleep(0.3)
            except Exception as e:
                logging.warning(f"      ❌ Failed to search {source}: {e}")
                continue
        
        logging.info(f"   📊 Total news source results: {news_results}")
        
        # General enhanced search for broader coverage
        try:
            logging.info(f"   🌐 Performing general enhanced search")
            enhanced_query = f'{base_query} {date_filter}'
            general_results = self._execute_single_search(enhanced_query, source_type="general")
            
            logging.info(f"      ✅ Retrieved {len(general_results)} general results")
            all_results.extend(general_results)
        except Exception as e:
            logging.warning(f"      ❌ General search failed: {e}")
        
        logging.info(f"   📊 Total raw results before filtering: {len(all_results)}")
        
        # Filter and rank results
        logging.info(f"   🔧 Starting result filtering and ranking")
        filtered_results = self._filter_and_enhance_results(all_results)
        
        search_duration = time.time() - search_start_time
        
        logging.info(f"✅ Enhanced search completed in {search_duration:.2f}s")
        logging.info(f"   📊 Final results: {len(filtered_results)}")
        logging.info(f"   📈 Filtering efficiency: {len(filtered_results)}/{len(all_results)} ({(len(filtered_results)/max(len(all_results), 1)*100):.1f}%)")
        
        return filtered_results

    def _execute_single_search(self, query: str, source_type: str = "general") -> List[Dict]:
        """Execute a single search with enhanced parameters"""
        try:
            params = {
                'key': self.api_key,
                'cx': self.search_engine_id,
                'q': query,
                'num': 10,
                'sort': 'date',
                'gl': 'us',
                'hl': 'en',
                'safe': 'off'
            }
            
            # Use news search for news sources
            if source_type == "news":
                params['tbm'] = 'nws'
            
            response = requests.get(self.base_url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            results = self._parse_search_results(data, query_context=f"{source_type}_search")
            
            # Mark results with source type
            for result in results:
                result['source_type'] = source_type
                result['search_query'] = query
            
            return results
            
        except Exception as e:
            logging.error(f"Search execution failed for query '{query}': {e}")
            return []

    def _filter_and_enhance_results(self, results: List[Dict]) -> List[Dict]:
        """Enhanced filtering for article quality and relevance with detailed logging"""
        filter_start_time = time.time()
        
        logging.info(f"      🔧 Starting enhanced result filtering")
        logging.info(f"         📊 Input results: {len(results)}")
        
        filtered_results = []
        seen_urls = set()
        domain_counts = {}
        
        # Track filtering statistics
        filter_stats = {
            'duplicates': 0,
            'invalid_urls': 0,
            'domain_limits': 0,
            'quality_enhanced': 0,
            'total_processed': 0
        }
        
        # Sort by source type priority and date
        def sort_priority(result):
            source_type = result.get('source_type', 'general')
            priority_map = {'official': 0, 'news': 1, 'general': 2}
            
            # Parse date for sorting
            try:
                date_str = result.get('date', '')
                if date_str:
                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    return (priority_map.get(source_type, 3), -date_obj.timestamp())
            except:
                pass
            
            return (priority_map.get(source_type, 3), 0)
        
        logging.info(f"         🔄 Sorting results by priority...")
        sorted_results = sorted(results, key=sort_priority)
        
        # Analyze source type distribution before filtering
        source_type_dist = {}
        for result in sorted_results:
            source_type = result.get('source_type', 'unknown')
            source_type_dist[source_type] = source_type_dist.get(source_type, 0) + 1
        
        logging.info(f"         📊 Source type distribution:")
        for source_type, count in source_type_dist.items():
            logging.info(f"            {source_type}: {count}")
        
        for i, result in enumerate(sorted_results):
            filter_stats['total_processed'] += 1
            
            url = result.get('url', '')
            domain = result.get('source', '').lower()
            source_type = result.get('source_type', 'unknown')
            
            if i < 5:  # Log first 5 items in detail
                logging.debug(f"         🔍 Processing item {i+1}: {result.get('title', 'No title')[:40]}...")
                logging.debug(f"            URL: {url}")
                logging.debug(f"            Domain: {domain}")
                logging.debug(f"            Source type: {source_type}")
            
            # Skip duplicates
            if url in seen_urls:
                if i < 5:
                    logging.debug(f"            ❌ Duplicate URL")
                filter_stats['duplicates'] += 1
                continue
            
            # Validate URL is an actual article
            if not self._is_valid_article_url(url):
                if i < 5:
                    logging.debug(f"            ❌ Invalid article URL")
                filter_stats['invalid_urls'] += 1
                continue
            
            # Limit results per domain for diversity
            domain_count = domain_counts.get(domain, 0)
            max_per_domain = 3 if result.get('source_type') == 'official' else 2
            
            if domain_count >= max_per_domain:
                if i < 5:
                    logging.debug(f"            ❌ Domain limit reached ({domain_count}/{max_per_domain})")
                filter_stats['domain_limits'] += 1
                continue
            
            # Enhance result with quality metrics
            url_quality = self._assess_url_quality(url)
            relevance_score = self._calculate_relevance_score(result)
            
            result['url_quality'] = url_quality
            result['relevance_score'] = relevance_score
            
            if i < 5:
                logging.debug(f"            ✅ Enhanced with quality: {url_quality}, relevance: {relevance_score:.1f}")
            
            filter_stats['quality_enhanced'] += 1
            
            seen_urls.add(url)
            domain_counts[domain] = domain_count + 1
            filtered_results.append(result)
            
            # Limit total results
            if len(filtered_results) >= 50:
                logging.info(f"         ⚠️  Reached maximum result limit (50)")
                break
        
        filter_duration = time.time() - filter_start_time
        
        # Log final statistics
        logging.info(f"      ✅ Filtering completed in {filter_duration:.3f}s")
        logging.info(f"         📊 Filtering statistics:")
        logging.info(f"            Total processed: {filter_stats['total_processed']}")
        logging.info(f"            Quality enhanced: {filter_stats['quality_enhanced']}")
        logging.info(f"            Filtered out - duplicates: {filter_stats['duplicates']}")
        logging.info(f"            Filtered out - invalid URLs: {filter_stats['invalid_urls']}")
        logging.info(f"            Filtered out - domain limits: {filter_stats['domain_limits']}")
        logging.info(f"            Final results: {len(filtered_results)}")
        logging.info(f"            Unique domains: {len(domain_counts)}")
        
        # Log top domains
        top_domains = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        logging.info(f"         🏆 Top domains:")
        for domain, count in top_domains:
            logging.info(f"            {domain}: {count}")
        
        return filtered_results

    def _is_valid_article_url(self, url: str) -> bool:
        """Enhanced validation for article URLs"""
        if not url or len(url) < 30:
            return False
        
        # Skip obvious non-article patterns
        skip_patterns = [
            r'/(category|categories|tag|tags)/',
            r'/(search|results)/',
            r'/page/\d+/?$',
            r'\?page=\d+',
            r'/(about|contact|privacy|terms)/?$',
            r'/feed/?$',
            r'\.pdf$',
            r'/jobs/?$',
            r'/careers/?$'
        ]
        
        for pattern in skip_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False
        
        # Must be a reasonable length and have path
        parsed = urlparse(url)
        if not parsed.path or parsed.path == '/':
            return False
        
        # Look for article indicators
        article_indicators = [
            r'/\d{4}/\d{2}/',          # Date pattern /2025/01/
            r'/\d{4}-\d{2}-\d{2}/',    # Date pattern /2025-01-15/
            r'/articles?/',            # Article section
            r'/blog/',                 # Blog posts
            r'/news/',                 # News section
            r'/post/',                 # Post section
            r'/story/',                # Story section
            r'/[a-z0-9-]{15,}/?$',     # Long slug (likely article)
            r'/p/[a-z0-9-]+',          # Medium-style posts
            r'/\d{10,}/',              # Timestamp pattern
        ]
        
        has_article_pattern = any(re.search(pattern, url) for pattern in article_indicators)
        
        # Additional validation for known quality domains
        quality_domains = [
            'openai.com', 'anthropic.com', 'googleblog.com', 'microsoft.com',
            'techcrunch.com', 'venturebeat.com', 'wired.com', 'arstechnica.com',
            'reuters.com', 'theverge.com', 'zdnet.com', 'technologyreview.mit.edu'
        ]
        
        is_quality_domain = any(domain in url.lower() for domain in quality_domains)
        
        return has_article_pattern or (is_quality_domain and len(parsed.path) > 10)

    def _assess_url_quality(self, url: str) -> str:
        """Assess the quality of a URL for content extraction"""
        # High quality: Official blogs and major tech news
        high_quality_domains = [
            'openai.com', 'anthropic.com', 'googleblog.com', 'research.google.com',
            'blogs.microsoft.com', 'ai.meta.com', 'techcrunch.com', 'venturebeat.com'
        ]
        
        # Medium quality: Tech news and analysis sites
        medium_quality_domains = [
            'theverge.com', 'wired.com', 'arstechnica.com', 'reuters.com',
            'zdnet.com', 'infoworld.com', 'technologyreview.mit.edu'
        ]
        
        domain = urlparse(url).netloc.lower()
        
        if any(d in domain for d in high_quality_domains):
            return 'high'
        elif any(d in domain for d in medium_quality_domains):
            return 'medium'
        else:
            return 'basic'

    def _calculate_relevance_score(self, result: Dict) -> float:
        """Calculate relevance score for ranking"""
        score = 0.0
        
        # Title relevance
        title = result.get('title', '').lower()
        ai_keywords = ['ai', 'artificial intelligence', 'machine learning', 'neural', 'llm', 'gpt', 'claude', 'gemini']
        score += sum(5 for keyword in ai_keywords if keyword in title)
        
        # Snippet relevance
        snippet = result.get('snippet', '').lower()
        score += sum(2 for keyword in ai_keywords if keyword in snippet)
        
        # Source type bonus
        source_type = result.get('source_type', 'general')
        if source_type == 'official':
            score += 20
        elif source_type == 'news':
            score += 10
        
        # URL quality bonus
        url_quality = result.get('url_quality', 'basic')
        if url_quality == 'high':
            score += 15
        elif url_quality == 'medium':
            score += 10
        
        # Recent date bonus
        try:
            date_str = result.get('date', '')
            if date_str:
                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                days_old = (datetime.now(date_obj.tzinfo) - date_obj).days
                if days_old <= 1:
                    score += 10
                elif days_old <= 3:
                    score += 5
        except:
            pass
        
        return score

    def search_with_diverse_sources(self, query: str, exclude_sources: List[str] = None) -> List[Dict]:
        """Legacy method - redirects to enhanced search"""
        return self.search_recent_ai_news(query)

    def search_with_site_filters(self, query: str, priority_sites: List[str]) -> List[Dict]:
        """Legacy method - redirects to enhanced search"""
        return self.search_recent_ai_news(query)

    def fetch_article_content(self, url: str, timeout: int = 10) -> Dict:
        """Fetch full content from article URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            
            # Extract structured content using BeautifulSoup
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style", "nav", "footer", "aside"]):
                    script.decompose()
                
                # Extract title, description, and main content
                title = None
                if soup.title:
                    title = soup.title.string.strip()
                
                # Try to find meta description
                description = None
                meta_desc = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
                if meta_desc:
                    description = meta_desc.get("content", "").strip()
                
                # Extract main text content
                # Try to find main content areas
                main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|article|post'))
                if main_content:
                    text_content = main_content.get_text()
                else:
                    text_content = soup.get_text()
                
                # Clean up whitespace
                lines = (line.strip() for line in text_content.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                clean_text = ' '.join(chunk for chunk in chunks if chunk)
                
                content = {
                    'title': title,
                    'description': description,
                    'text_content': clean_text[:3000],  # First 3000 chars
                    'content_length': len(clean_text),
                    'status_code': response.status_code,
                    'fetched_at': datetime.now().isoformat(),
                    'extraction_method': 'beautifulsoup',
                    'is_content_rich': len(clean_text) > 500
                }
                
            except ImportError:
                # Fallback to basic extraction if BeautifulSoup not available
                content = {
                    'raw_text': response.text[:5000],  # Truncate for storage
                    'status_code': response.status_code,
                    'content_length': len(response.text),
                    'fetched_at': datetime.now().isoformat(),
                    'extraction_method': 'basic',
                    'is_content_rich': False
                }
            
            logging.info(f"Successfully fetched content from: {url}")
            return content
            
        except Exception as e:
            logging.error(f"Failed to fetch content from {url}: {e}")
            return {
                'error': str(e),
                'fetched_at': datetime.now().isoformat(),
                'is_content_rich': False
            }

    def search_ai_content_with_full_fetch(self, query: str, days_back: int = 7) -> List[Dict]:
        """Search and fetch full content for high-quality results"""
        search_results = self.search_recent_ai_news(query, days_back)
        
        enhanced_results = []
        for result in search_results:
            url = result.get('url', '')
            url_quality = result.get('url_quality', 'basic')
            
            # Only fetch content for high and medium quality URLs
            if url and url_quality in ['high', 'medium']:
                content = self.fetch_article_content(url)
                result['full_content'] = content
                result['content_fetched'] = True
                result['has_rich_content'] = content.get('is_content_rich', False)
            else:
                result['content_fetched'] = False
                result['has_rich_content'] = False
            
            enhanced_results.append(result)
            
            # Rate limiting
            time.sleep(0.4)
        
        return enhanced_results

    def _get_date_filter(self, days_back: int) -> str:
        """Generate date filter for Google Search"""
        target_date = datetime.now() - timedelta(days=days_back)
        return target_date.strftime('%Y-%m-%d')
    
    def _parse_search_results(self, data: Dict, query_context: str = "unknown") -> List[Dict]:
        """Parse Google Search API response with enhanced validation and detailed logging"""
        parse_start_time = time.time()
        
        logging.info(f"   📝 Parsing search results (context: {query_context})")
        
        results = []
        
        items = data.get('items', [])
        
        if not items:
            # More informative logging for debugging
            if 'searchInformation' in data:
                search_info = data['searchInformation']
                total_results = search_info.get('totalResults', '0')
                search_time = search_info.get('searchTime', 'unknown')
                
                if total_results == '0':
                    logging.info(f"   ℹ️  No search results found for query (searched in {search_time}s)")
                    logging.info(f"      💡 Suggestion: Query may be too specific or recent")
                else:
                    logging.warning(f"   ⚠️  API returned {total_results} total results but no 'items' field")
                    logging.warning(f"      🔍 This might indicate API pagination or filtering issues")
            else:
                logging.warning("   ⚠️  No 'items' field in API response")
            
            # Log response structure for debugging
            response_keys = list(data.keys())
            logging.debug(f"   📋 Available response keys: {response_keys}")
            
            if 'error' in data:
                logging.error(f"   ❌ API returned error: {data['error']}")
            
            return results
        
        logging.info(f"   📊 Raw items from API: {len(items)}")
        
        skipped_reasons = {
            'missing_fields': 0,
            'invalid_url': 0,
            'non_https': 0,
            'validation_failed': 0
        }
        
        for i, item in enumerate(items):
            logging.debug(f"   🔍 Processing item {i+1}/{len(items)}")
            
            # Validate that we have required fields
            title = item.get('title', '').strip()
            link = item.get('link', '').strip()
            
            if not title or not link:
                logging.debug(f"   ❌ Item {i+1}: Missing title or link")
                logging.debug(f"      Title: {'✅' if title else '❌'}")
                logging.debug(f"      Link: {'✅' if link else '❌'}")
                skipped_reasons['missing_fields'] += 1
                continue
            
            url = link
            
            # Enhanced URL validation
            if not self._is_valid_article_url(url):
                logging.debug(f"   ❌ Item {i+1}: Invalid article URL: {url}")
                skipped_reasons['invalid_url'] += 1
                continue
            
            # Only include results with valid HTTPS URLs
            if not url.startswith('https://'):
                logging.debug(f"   ❌ Item {i+1}: Non-HTTPS URL: {url}")
                skipped_reasons['non_https'] += 1
                continue
            
            # Extract additional data
            snippet = item.get('snippet', '').strip()
            source = self._extract_domain(url)
            date = self._extract_date(item)
            display_url = item.get('displayLink', '').strip()
            
            result = {
                'title': title,
                'snippet': snippet,
                'url': url,
                'source': source,
                'date': date,
                'display_url': display_url
            }
            
            # Log successful parsing
            logging.debug(f"   ✅ Item {i+1}: Parsed successfully")
            logging.debug(f"      Title: {title[:50]}...")
            logging.debug(f"      Source: {source}")
            logging.debug(f"      URL: {url}")
            
            results.append(result)
        
        parse_duration = time.time() - parse_start_time
        
        # Log parsing summary
        logging.info(f"   📊 Parsing summary:")
        logging.info(f"      ✅ Successfully parsed: {len(results)}")
        logging.info(f"      ❌ Skipped - missing fields: {skipped_reasons['missing_fields']}")
        logging.info(f"      ❌ Skipped - invalid URL: {skipped_reasons['invalid_url']}")
        logging.info(f"      ❌ Skipped - non-HTTPS: {skipped_reasons['non_https']}")
        logging.info(f"      ⏱️  Parse time: {parse_duration:.3f}s")
        
        return results
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain name from URL"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.replace('www.', '')
            return domain if domain else 'Unknown'
        except:
            return 'Unknown'
    
    def _extract_date(self, item: Dict) -> str:
        """Extract publication date from search result"""
        # Try to get date from various fields
        if 'pagemap' in item:
            pagemap = item['pagemap']
            
            if 'metatags' in pagemap:
                for meta in pagemap['metatags']:
                    for date_field in ['article:published_time', 'datePublished', 'publishdate', 'date']:
                        if date_field in meta and meta[date_field]:
                            return meta[date_field]
            
            # Try other date sources
            if 'newsarticle' in pagemap:
                for article in pagemap['newsarticle']:
                    if 'datepublished' in article:
                        return article['datepublished']
        
        # Try to extract from snippet if it contains "ago" pattern
        snippet = item.get('snippet', '')
        if 'ago' in snippet.lower():
            # Look for patterns like "5 hours ago", "2 days ago"
            import re
            time_pattern = r'(\d+)\s+(hour|day|week)s?\s+ago'
            match = re.search(time_pattern, snippet, re.IGNORECASE)
            if match:
                number = int(match.group(1))
                unit = match.group(2).lower()
                
                current_time = datetime.now()
                if unit == 'hour':
                    estimated_date = current_time - timedelta(hours=number)
                elif unit == 'day':
                    estimated_date = current_time - timedelta(days=number)
                elif unit == 'week':
                    estimated_date = current_time - timedelta(weeks=number)
                else:
                    estimated_date = current_time
                
                return estimated_date.isoformat()
        
        # Fallback to current date
        return datetime.now().isoformat()
    
    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate results and ensure source diversity"""
        seen_urls = set()
        seen_domains = {}
        deduplicated = []
        
        # Sort by relevance score if available
        def sort_key(result):
            relevance = result.get('relevance_score', 0)
            source_type = result.get('source_type', 'general')
            type_priority = {'official': 3, 'news': 2, 'general': 1}
            return (type_priority.get(source_type, 0), relevance)
        
        sorted_results = sorted(results, key=sort_key, reverse=True)
        
        for result in sorted_results:
            url = result.get('url', '')
            domain = result.get('source', '').lower()
            
            # Skip duplicates
            if url in seen_urls:
                continue
            
            # Limit results per domain for diversity
            domain_count = seen_domains.get(domain, 0)
            max_per_domain = 4 if result.get('source_type') == 'official' else 2
            
            if domain_count >= max_per_domain:
                continue
            
            seen_urls.add(url)
            seen_domains[domain] = domain_count + 1
            deduplicated.append(result)
        
        logging.info(f"After enhanced deduplication: {len(deduplicated)} diverse results from {len(seen_domains)} sources")
        return deduplicated[:45]  # Limit total results