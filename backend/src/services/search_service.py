# backend/src/services/search_service.py
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
    
    def search_ai_content(self, query: str, days_back: int = 7) -> List[Dict]:
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
        """Search with focus on diverse, high-quality sources"""
        if exclude_sources is None:
            exclude_sources = []
        
        # Technical AI and research sources with balanced industry coverage
        diverse_sources = [
            # AI Company Technical Blogs (Highest Priority)
            "ai.googleblog.com",
            "openai.com/blog",
            "blog.anthropic.com", 
            "research.microsoft.com",
            "ai.meta.com",
            "deepmind.google",
            # Development & Open Source
            "huggingface.co",
            "github.com",
            # Research Sources
            "arxiv.org",
            "papers.nips.cc",
            # Technical Journalism
            "technologyreview.mit.edu",
            "spectrum.ieee.org",
            # Industry News (Secondary)
            "techcrunch.com",
            "venturebeat.com", 
            "theinformation.com"
        ]
        
        # Filter out excluded sources
        sources_to_use = [s for s in diverse_sources if s not in exclude_sources]
        
        all_results = []
        
        # Search diverse sources first (limit to avoid rate limits)
        for source in sources_to_use[:5]:  # Top 5 diverse sources
            try:
                site_query = f"{query} site:{source}"
                results = self.search_ai_content(site_query)
                all_results.extend(results)
                
                # Small delay to respect rate limits
                time.sleep(0.3)
                
            except Exception as e:
                logging.warning(f"Failed to search {source}: {e}")
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
                
            result = {
                'title': item.get('title', '').strip(),
                'snippet': item.get('snippet', '').strip(),
                'url': item.get('link', '').strip(),
                'source': self._extract_domain(item.get('link', '')),
                'date': self._extract_date(item),
                'display_url': item.get('displayLink', '').strip()
            }
            
            # Only include results with valid URLs
            if result['url'].startswith(('http://', 'https://')):
                results.append(result)
        
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
        
        # Fallback to current date
        return datetime.now().isoformat()
    
    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate results based on URL and ensure source diversity"""
        seen_urls = set()
        seen_domains = {}
        deduplicated = []
        
        # Sort by source diversity (prefer non-arxiv sources first)
        def source_priority(result):
            domain = result.get('source', '').lower()
            if 'arxiv' in domain:
                return 2  # Lower priority
            elif any(news in domain for news in ['techcrunch', 'venturebeat', 'wired']):
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