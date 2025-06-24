# backend/src/services/search_service.py
import requests
import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
from urllib.parse import urlparse

class GoogleSearchService:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_SEARCH_API_KEY')
        self.search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        
        # For development/testing, we'll create mock data if API keys are missing
        self.use_mock_data = not (self.api_key and self.search_engine_id)
        
        if self.use_mock_data:
            logging.warning("Google Search API credentials not found. Using mock data for testing.")
    
    def search_ai_content(self, query: str, days_back: int = 7) -> List[Dict]:
        """Search for AI content with time filtering"""
        if self.use_mock_data:
            return self._get_mock_search_results(query)
        
        try:
            # Add time constraint to query
            time_query = f"{query} after:{self._get_date_filter(days_back)}"
            
            params = {
                'key': self.api_key,
                'cx': self.search_engine_id,
                'q': time_query,
                'num': 10,
                'sort': 'date',
                'gl': 'us',
                'hl': 'en'
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return self._parse_search_results(data)
            
        except requests.RequestException as e:
            logging.error(f"Search API error for query '{query}': {e}")
            return self._get_mock_search_results(query)  # Fallback to mock data
        except Exception as e:
            logging.error(f"Unexpected error in search: {e}")
            return []
    
    def search_with_site_filters(self, query: str, priority_sites: List[str]) -> List[Dict]:
        """Search with priority given to specific sites"""
        if self.use_mock_data:
            return self._get_mock_search_results(query)
        
        all_results = []
        
        # Search priority sites (limit to avoid rate limits)
        for site in priority_sites[:2]:
            site_query = f"{query} site:{site}"
            results = self.search_ai_content(site_query)
            all_results.extend(results)
        
        # General search
        general_results = self.search_ai_content(query)
        all_results.extend(general_results)
        
        return self._deduplicate_results(all_results)
    
    def _get_mock_search_results(self, query: str) -> List[Dict]:
        """Generate mock search results for testing"""
        mock_results = [
            {
                'title': f'AI Breakthrough: {query.title()} Research Paper',
                'snippet': 'New research published this week shows significant advances in artificial intelligence and machine learning capabilities...',
                'url': 'https://arxiv.org/abs/2501.12345',
                'source': 'arxiv.org',
                'date': datetime.now().isoformat(),
                'display_url': 'arxiv.org'
            },
            {
                'title': f'Industry Update: Major AI Company Announces {query}',
                'snippet': 'Leading technology company unveils new AI initiative focusing on practical applications and enterprise solutions...',
                'url': 'https://techcrunch.com/2025/01/ai-announcement',
                'source': 'techcrunch.com',
                'date': (datetime.now() - timedelta(days=1)).isoformat(),
                'display_url': 'techcrunch.com'
            },
            {
                'title': f'Open Source: New AI Framework Related to {query}',
                'snippet': 'Community-driven project releases powerful new tools for developers working on artificial intelligence applications...',
                'url': 'https://github.com/ai-company/new-framework',
                'source': 'github.com',
                'date': (datetime.now() - timedelta(days=2)).isoformat(),
                'display_url': 'github.com'
            }
        ]
        return mock_results
    
    def _get_date_filter(self, days_back: int) -> str:
        """Generate date filter for Google Search"""
        target_date = datetime.now() - timedelta(days=days_back)
        return target_date.strftime('%Y-%m-%d')
    
    def _parse_search_results(self, data: Dict) -> List[Dict]:
        """Parse Google Search API response"""
        results = []
        
        for item in data.get('items', []):
            result = {
                'title': item.get('title', ''),
                'snippet': item.get('snippet', ''),
                'url': item.get('link', ''),
                'source': self._extract_domain(item.get('link', '')),
                'date': self._extract_date(item),
                'display_url': item.get('displayLink', '')
            }
            results.append(result)
        
        return results
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain name from URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc.replace('www.', '')
        except:
            return 'Unknown'
    
    def _extract_date(self, item: Dict) -> str:
        """Extract publication date from search result"""
        # Try to get date from various fields
        if 'pagemap' in item:
            pagemap = item['pagemap']
            
            if 'metatags' in pagemap:
                for meta in pagemap['metatags']:
                    for date_field in ['article:published_time', 'datePublished', 'publishdate']:
                        if date_field in meta:
                            return meta[date_field]
        
        return datetime.now().isoformat()
    
    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate results based on URL"""
        seen_urls = set()
        deduplicated = []
        
        for result in results:
            url = result.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                deduplicated.append(result)
        
        return deduplicated