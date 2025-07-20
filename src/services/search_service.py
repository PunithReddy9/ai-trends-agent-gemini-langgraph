# src/services/search_service.py
import requests
import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
from urllib.parse import urlparse
import time

class GoogleSearchService:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_SEARCH_API_KEY')
        self.search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        
        # Require API keys - no mock data fallback
        if not self.api_key or not self.search_engine_id:
            raise ValueError(
                "Google Search API credentials are required. Please set:\n"
                "GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_ENGINE_ID in your .env file"
            )
        
        logging.info("Google Search Service initialized with real API credentials")
    
    def search_ai_content(self, query: str, days_back: int = 14) -> List[Dict]:
        """Search for AI content with time filtering - REAL DATA ONLY"""
        try:
            # Add time constraint to query for recent content
            time_query = f"{query} after:{self._get_date_filter(days_back)}"
            
            params = {
                'key': self.api_key,
                'cx': self.search_engine_id,
                'q': time_query,
                'num': 10,  # Number of results per query
                'sort': 'date',  # Sort by date
                'gl': 'us',  # Geolocation
                'hl': 'en'   # Language
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = self._parse_search_results(data)
            
            logging.info(f"Successfully retrieved {len(results)} real search results for: {query}")
            return results
            
        except requests.RequestException as e:
            logging.error(f"Google Search API error for query '{query}': {e}")
            # Don't return mock data - return empty list
            return []
        except Exception as e:
            logging.error(f"Unexpected error in search: {e}")
            return []
    
    def search_with_diverse_sources(self, query: str, exclude_sources: List[str] = None) -> List[Dict]:
        """Search with focus on diverse, high-quality sources using natural language terms"""
        if exclude_sources is None:
            exclude_sources = []
        
        # Natural language search terms for AI sources
        natural_search_terms = {
            # Technical/Research Sources
            "ai.googleblog.com": ["Google AI research", "Google AI blog", "Google artificial intelligence"],
            "openai.com": ["OpenAI research", "OpenAI announcements", "OpenAI ChatGPT updates"],
            "blog.anthropic.com": ["Anthropic AI research", "Anthropic Claude updates", "Anthropic safety research"],
            "research.microsoft.com": ["Microsoft AI research", "Microsoft research blog", "Microsoft AI announcements"],
            "ai.meta.com": ["Meta AI research", "Facebook AI research", "Meta AI announcements"],
            "deepmind.google": ["Google DeepMind research", "DeepMind AI research", "DeepMind announcements"],
            "news.mit.edu": ["MIT AI news", "MIT research news", "MIT artificial intelligence"],
            "the-decoder.com": ["AI news decoder", "AI industry news", "artificial intelligence news"],
            "knowentry.com": ["AI industry analysis", "AI research insights", "AI technology news"],
            # Development & Open Source
            "huggingface.co": ["Hugging Face AI models", "Hugging Face research", "Hugging Face announcements"],
            "github.com": ["GitHub AI projects", "GitHub research", "GitHub announcements"],
            # Research Sources
            "papers.nips.cc": ["NeurIPS papers", "NeurIPS research", "NeurIPS conference"],
            # Technical Journalism
            "technologyreview.mit.edu": ["MIT Technology Review", "AI technology analysis", "emerging technology news"],
            "spectrum.ieee.org": ["IEEE Spectrum AI", "engineering AI news", "technical AI news"],
            # Industry News
            "techcrunch.com": ["TechCrunch AI news", "startup AI news", "tech industry news"],
            "venturebeat.com": ["VentureBeat AI news", "enterprise AI news", "AI business news"],
            "theinformation.com": ["tech industry analysis", "AI business intelligence", "tech insider news"]
        }
        
        all_results = []
        
        # Search with natural language terms from various sources
        for source, search_terms in natural_search_terms.items():
            if source in exclude_sources:
                continue
                
            # Use first search term for each source
            for term in search_terms[:1]:
                try:
                    # Combine the query with the natural language term
                    combined_query = f"{query} {term}"
                    results = self.search_ai_content(combined_query)
                    all_results.extend(results)
                    
                    # Small delay to respect rate limits
                    time.sleep(0.3)
                    
                except Exception as e:
                    logging.warning(f"Failed to search with term '{term}': {e}")
                    continue
        
        # Add general search for broader coverage
        general_results = self.search_ai_content(query)
        all_results.extend(general_results)
        
        # Remove duplicates and return
        return self._deduplicate_results(all_results)
    
    def search_with_site_filters(self, query: str, priority_sites: List[str]) -> List[Dict]:
        """Search with priority given to specific sites"""
        all_results = []
        
        # Limit priority sites to avoid rate limiting
        for site in priority_sites[:3]:  # Top 3 priority sites only
            try:
                site_query = f"{query} site:{site}"
                results = self.search_ai_content(site_query)
                all_results.extend(results)
                
                # Rate limiting delay
                time.sleep(0.5)
                
            except Exception as e:
                logging.warning(f"Failed to search priority site {site}: {e}")
                continue
        
        # Add diverse source search for broader coverage
        diverse_results = self.search_with_diverse_sources(query, exclude_sources=priority_sites)
        all_results.extend(diverse_results)
        
        return self._deduplicate_results(all_results)
    
    def fetch_article_content(self, url: str, timeout: int = 10) -> Dict:
        """Fetch full content from article URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; AI-Trends-Agent/1.0)'
            }
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            
            # Extract structured content using BeautifulSoup
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Extract title, description, and main content
                title = None
                if soup.title:
                    title = soup.title.string.strip()
                
                # Try to find meta description
                description = None
                meta_desc = soup.find("meta", attrs={"name": "description"})
                if meta_desc:
                    description = meta_desc.get("content", "").strip()
                
                # Extract main text content
                text_content = soup.get_text()
                
                # Clean up whitespace
                lines = (line.strip() for line in text_content.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                clean_text = ' '.join(chunk for chunk in chunks if chunk)
                
                content = {
                    'title': title,
                    'description': description,
                    'text_content': clean_text[:2000],  # First 2000 chars
                    'content_length': len(clean_text),
                    'raw_html_preview': response.text[:1000],  # First 1000 chars of HTML
                    'status_code': response.status_code,
                    'fetched_at': datetime.now().isoformat(),
                    'extraction_method': 'beautifulsoup'
                }
                
            except ImportError:
                # Fallback to basic extraction if BeautifulSoup not available
                content = {
                    'raw_html': response.text[:5000],  # Truncate for storage
                    'status_code': response.status_code,
                    'content_length': len(response.text),
                    'fetched_at': datetime.now().isoformat(),
                    'extraction_method': 'basic'
                }
            
            logging.info(f"Successfully fetched content from: {url}")
            return content
            
        except Exception as e:
            logging.error(f"Failed to fetch content from {url}: {e}")
            return {
                'error': str(e),
                'fetched_at': datetime.now().isoformat()
            }

    def search_ai_content_with_full_fetch(self, query: str, days_back: int = 14) -> List[Dict]:
        """Search and fetch full content for high-quality results"""
        search_results = self.search_ai_content(query, days_back)
        
        enhanced_results = []
        for result in search_results:
            url = result.get('url', '')
            
            # Only fetch content for high-quality URLs
            if url and self._is_high_quality_url(url):
                content = self.fetch_article_content(url)
                result['full_content'] = content
                result['content_fetched'] = True
            else:
                result['content_fetched'] = False
            
            enhanced_results.append(result)
            
            # Rate limiting
            time.sleep(0.5)
        
        return enhanced_results

    def _is_high_quality_url(self, url: str) -> bool:
        """Check if URL is worth fetching full content"""
        if not url or len(url) < 20:
            return False
        
        # Skip category/landing pages and search pages
        category_patterns = [
            '/technology/artificial-intelligence/$',  # Reuters AI category
            '/category/', '/categories/', '/topics/',
            '/news/$', '/blog/$', '/articles/$',
            '/ai/$', '/ml/$', '/tech/$'
        ]
        
        import re
        for pattern in category_patterns:
            if re.search(pattern, url):
                return False
            
        # High-quality domains worth fetching
        quality_domains = [
            'googleblog.com', 'openai.com', 'anthropic.com', 'microsoft.com',
            'techcrunch.com', 'venturebeat.com', 'github.com', 'huggingface.co',
            'reuters.com', 'theverge.com', 'arstechnica.com', 'zdnet.com'
        ]
        
        # Check if URL has article-like pattern (date, slug, etc.)
        article_patterns = [
            r'/\d{4}/\d{2}/',  # Date pattern like /2025/07/
            r'/\d{4}-\d{2}-\d{2}/',  # Date pattern like /2025-07-15/
            r'/-\d{10,}/',  # Timestamp pattern
            r'/[a-z0-9-]{20,}/$',  # Long slug pattern
            r'/article/', r'/post/', r'/news/',
            r'/p/', r'/story/'
        ]
        
        has_article_pattern = any(re.search(pattern, url) for pattern in article_patterns)
        is_quality_domain = any(domain in url.lower() for domain in quality_domains)
        
        return is_quality_domain and (has_article_pattern or len(url) > 50)
    
    def _get_date_filter(self, days_back: int) -> str:
        """Generate date filter for Google Search"""
        target_date = datetime.now() - timedelta(days=days_back)
        return target_date.strftime('%Y-%m-%d')
    
    def _parse_search_results(self, data: Dict) -> List[Dict]:
        """Parse Google Search API response"""
        results = []
        
        items = data.get('items', [])
        if not items:
            logging.warning("No search results returned from Google API")
            return results
        
        for item in items:
            # Validate that we have required fields
            if not item.get('title') or not item.get('link'):
                continue
            
            url = item.get('link', '').strip()
            
            # Skip category/landing pages
            if self._is_category_page(url):
                logging.info(f"Skipping category page: {url}")
                continue
                
            result = {
                'title': item.get('title', '').strip(),
                'snippet': item.get('snippet', '').strip(),
                'url': url,
                'source': self._extract_domain(url),
                'date': self._extract_date(item),
                'display_url': item.get('displayLink', '').strip()
            }
            
            # Only include results with valid URLs
            if result['url'].startswith(('http://', 'https://')):
                results.append(result)
        
        return results
    
    def _is_category_page(self, url: str) -> bool:
        """Check if URL is a category or landing page"""
        import re
        
        # Common category page patterns
        category_patterns = [
            r'/technology/artificial-intelligence/?$',  # Reuters AI category
            r'/category/[^/]+/?$',  # Generic category pages  
            r'/categories/[^/]+/?$',
            r'/topics?/[^/]+/?$',  # Topic pages
            r'/tags?/[^/]+/?$',  # Tag pages
            r'/(news|blog|articles?)/?$',  # Section homepages
            r'/(ai|ml|tech)/?$',  # Short section pages
            r'/page/\d+/?$',  # Pagination
            r'\?page=\d+',  # Query pagination
        ]
        
        for pattern in category_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
                
        # Also check if URL is too short (likely a section page)
        path = url.split('/', 3)[-1] if '/' in url else ''
        if len(path) < 20 and not any(indicator in path for indicator in ['.html', '.htm', '/p/', '/article/']):
            return True
            
        return False
    
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
        
        # Fallback to current date
        return datetime.now().isoformat()
    
    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate results based on URL and ensure source diversity"""
        seen_urls = set()
        seen_domains = {}
        deduplicated = []
        
        # Sort by source diversity
        def source_priority(result):
            domain = result.get('source', '').lower()
            if any(news in domain for news in ['techcrunch', 'venturebeat', 'wired']):
                return 0  # Highest priority
            else:
                return 1  # Medium priority
        
        # Sort results by priority
        sorted_results = sorted(results, key=source_priority)
        
        for result in sorted_results:
            url = result.get('url', '')
            domain = result.get('source', '').lower()
            
            # Skip duplicates
            if url in seen_urls:
                continue
            
            # Limit results per domain to ensure diversity
            domain_count = seen_domains.get(domain, 0)
            if domain_count >= 3:  # Max 3 results per domain
                continue
            
            seen_urls.add(url)
            seen_domains[domain] = domain_count + 1
            deduplicated.append(result)
        
        logging.info(f"After deduplication: {len(deduplicated)} diverse results from {len(seen_domains)} different sources")
        return deduplicated[:40]  # Limit total results