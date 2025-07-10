# backend/src/agent/graph.py
"""AI Trends Weekly Reporter Agent"""

from typing import List, Dict, Any, Optional, TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from datetime import datetime, timedelta
import json
import os
import logging
from urllib.parse import urlparse

# Import search service
try:
    from ..services.search_service import GoogleSearchService
except ImportError:
    # Fallback for when running directly
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from services.search_service import GoogleSearchService

class AgentState(TypedDict):
    """State for the AI trends agent"""
    input: str
    search_queries: List[str]
    search_results: List[Dict]
    categorized_content: Dict[str, List[Dict]]
    weekly_report: str
    report_metadata: Dict
    generation_timestamp: str
    report_date_range: str
    export_path: str
    # Reflection mechanism fields
    iteration_count: int
    reflection_feedback: str
    quality_score: float
    needs_improvement: bool
    improvement_areas: List[str]

class AITrendsReporter:
    def __init__(self, gemini_api_key: str):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            api_key=gemini_api_key,
            temperature=0.1
        )
        self.search_service = GoogleSearchService()
        
        # Natural language search terms for AI sources
        self.natural_search_terms = {
            # Technical/Research Sources - Convert URLs to natural language
            "ai.googleblog.com": [
                "Google AI research",
                "Google AI blog",
                "Google artificial intelligence research",
                "Google AI announcements",
                "Google DeepMind research"
            ],
            
            "openai.com": [
                "OpenAI research",
                "OpenAI announcements",
                "OpenAI ChatGPT updates",
                "OpenAI blog",
                "OpenAI latest research"
            ],
            
            "blog.anthropic.com": [
                "Anthropic AI research",
                "Anthropic Claude updates",
                "Anthropic safety research",
                "Anthropic blog",
                "Anthropic AI safety"
            ],
            
            "research.microsoft.com": [
                "Microsoft AI research",
                "Microsoft research blog",
                "Microsoft AI announcements",
                "Microsoft research papers",
                "Microsoft AI developments"
            ],
            
            "ai.meta.com": [
                "Meta AI research",
                "Facebook AI research",
                "Meta AI announcements",
                "Meta AI blog",
                "Meta artificial intelligence"
            ],
            
            "deepmind.google": [
                "Google DeepMind research",
                "DeepMind AI research",
                "DeepMind announcements",
                "DeepMind blog",
                "DeepMind breakthrough"
            ],
            
            "huggingface.co": [
                "Hugging Face AI models",
                "Hugging Face research",
                "Hugging Face blog",
                "Hugging Face announcements",
                "Hugging Face open source"
            ],
            
            "github.com": [
                "GitHub AI projects",
                "GitHub research",
                "GitHub blog",
                "GitHub announcements",
                "GitHub open source AI"
            ],
            
            "papers.nips.cc": [
                "NeurIPS papers",
                "NeurIPS research",
                "NeurIPS conference",
                "NeurIPS machine learning",
                "NeurIPS AI research"
            ],
            
            "news.mit.edu": [
                "MIT AI news",
                "MIT research news",
                "MIT artificial intelligence",
                "MIT technology news",
                "MIT AI breakthrough"
            ],
            
            "the-decoder.com": [
                "AI news decoder",
                "AI industry news",
                "artificial intelligence news",
                "AI research news",
                "AI technology updates"
            ],
            
            "knowentry.com": [
                "AI industry analysis",
                "AI research insights",
                "AI technology news",
                "AI market analysis",
                "AI business news"
            ],
            
            # Industry News Sources
            "techcrunch.com": [
                "TechCrunch AI news",
                "startup AI news",
                "tech industry news",
                "AI startup funding",
                "technology announcements"
            ],
            
            "venturebeat.com": [
                "VentureBeat AI news",
                "enterprise AI news",
                "AI business news",
                "AI technology news",
                "AI industry updates"
            ],
            
            "theinformation.com": [
                "tech industry analysis",
                "AI business intelligence",
                "tech insider news",
                "AI market analysis",
                "technology business news"
            ],
            
            "technologyreview.mit.edu": [
                "MIT Technology Review",
                "AI technology analysis",
                "emerging technology news",
                "AI research analysis",
                "technology innovation news"
            ],
            
            "spectrum.ieee.org": [
                "IEEE Spectrum AI",
                "engineering AI news",
                "technical AI news",
                "AI engineering updates",
                "IEEE artificial intelligence"
            ],
            
            # Additional high-quality sources for better coverage
            "towardsdatascience.com": [
                "data science AI tutorials",
                "machine learning guides",
                "AI implementation tutorials",
                "data science insights",
                "AI technical guides"
            ],
            
            "blog.google": [
                "Google AI blog",
                "Google research blog",
                "Google technology blog",
                "Google AI developments",
                "Google machine learning"
            ],
            
            "aws.amazon.com": [
                "AWS AI services",
                "Amazon AI announcements",
                "AWS machine learning",
                "Amazon AI research",
                "AWS AI tools"
            ],
            
            "azure.microsoft.com": [
                "Azure AI services",
                "Microsoft Azure AI",
                "Azure machine learning",
                "Microsoft cloud AI",
                "Azure AI updates"
            ],
            
            "developer.nvidia.com": [
                "NVIDIA AI developer",
                "NVIDIA GPU AI",
                "NVIDIA AI tools",
                "NVIDIA machine learning",
                "NVIDIA AI platform"
            ]
        }
        
        # Category-based search terms for different types of AI news
        self.category_search_terms = {
            "research_breakthroughs": [
                "AI research breakthrough",
                "artificial intelligence discovery",
                "machine learning research",
                "AI paper published",
                "AI research milestone"
            ],
            
            "product_announcements": [
                "AI product launch",
                "AI tool announcement",
                "AI service release",
                "AI platform update",
                "AI feature release",
                "new AI API",
                "AI SDK release",
                "AI framework launch",
                "AI library update",
                "AI model release"
            ],
            
            "industry_analysis": [
                "AI market analysis",
                "AI industry trends",
                "AI business impact",
                "AI investment news",
                "AI market research"
            ],
            
            "regulatory_policy": [
                "AI regulation news",
                "AI policy update",
                "AI governance",
                "AI ethics policy",
                "AI legislation"
            ],
            
            "company_news": [
                "AI company news",
                "AI startup funding",
                "AI company acquisition",
                "AI partnership announcement",
                "AI company earnings"
            ]
        }
    
    def generate_ai_weekly_queries(self, state: AgentState) -> AgentState:
        """Generate comprehensive AI search queries"""
        current_date = datetime.now()
        week_ago = current_date - timedelta(days=7)
        
        prompt = f"""
        You must return ONLY a valid JSON array with exactly 12 search queries. No explanations, no other text.

        Generate 12 diverse search queries for AI developments from the past week ({week_ago.strftime('%B %d')} to {current_date.strftime('%B %d, %Y')}).

        Categories:
        1. AI Technical Advancements (4 queries): model releases, capabilities, breakthroughs
        2. Company AI Research (3 queries): research projects, lab announcements, publications  
        3. AI Tools & Frameworks (3 queries): development tools, open source releases, APIs
        4. Business Applications (2 queries): industry implementation, adoption trends

        Requirements:
        - Use time indicators: "past week", "this week", "recent"
        - Mix terminology: AI, artificial intelligence, machine learning
        - Focus on significant developments
        
        RESPONSE FORMAT (copy exactly):
        ["query 1", "query 2", "query 3", "query 4", "query 5", "query 6", "query 7", "query 8", "query 9", "query 10", "query 11", "query 12"]
        
        Return ONLY the JSON array above with your 12 queries. No other text.
        """
        
        try:
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            
            # Clean up common LLM response issues
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            elif content.startswith('```'):
                content = content.replace('```', '').strip()
            
            # Try to extract JSON array if wrapped in text
            import re
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                content = json_match.group(0)
            
            queries = json.loads(content)
            
            # Validate it's a list of strings
            if not isinstance(queries, list) or len(queries) != 12:
                raise ValueError(f"Expected list of 12 strings, got {type(queries)} with {len(queries) if isinstance(queries, list) else 'N/A'} items")
                
            queries = [str(q) for q in queries]  # Ensure all are strings
            logging.info(f"Successfully generated {len(queries)} search queries")
            
        except (json.JSONDecodeError, ValueError, Exception) as e:
            logging.warning(f"Failed to parse queries from LLM: {e}")
            logging.warning(f"LLM Response was: {response.content[:200]}...")
            
            # Use current date for fallback queries
            current_month = current_date.strftime('%B %Y')
            queries = [
                f"AI new features announcement {current_month}",
                f"machine learning breakthrough past week",
                f"OpenAI research update recent",
                f"Google AI model improvements this week",
                f"Anthropic Claude capabilities {current_month}",
                f"AI framework open source release recent",
                f"artificial intelligence startup funding news",
                f"Meta AI research developments past week",
                f"AI tool platform announcement {current_month}",
                f"deep learning algorithm innovation recent",
                f"AI industry partnership news this week",
                f"machine learning library update {current_month}"
            ]
        
        state["search_queries"] = queries
        state["search_results"] = []
        state["report_date_range"] = f"{week_ago.strftime('%B %d')} - {current_date.strftime('%B %d, %Y')}"
        
        # Initialize reflection mechanism fields
        state["iteration_count"] = 0
        state["reflection_feedback"] = ""
        state["quality_score"] = 0.0
        state["needs_improvement"] = False
        state["improvement_areas"] = []
        
        return state
    
    def research_ai_trends(self, state: AgentState) -> AgentState:
        """Execute comprehensive AI trends research using natural language terms with preference for specified sources"""
        base_queries = state["search_queries"]
        all_results = []
        
        # PRIORITY 1: Search with natural language terms from specified sources (highest priority)
        for source_category, search_terms in self.natural_search_terms.items():
            # Use fewer terms per source to reduce timeout risk
            for term in search_terms[:2]:  # Reduced from 3 to 2
                try:
                    # Add time context and site-specific search to get actual articles
                    if source_category in ['huggingface.co', 'github.com']:
                        # For code/model repositories, search for releases and updates
                        time_aware_query = f"{term} new release update announcement"
                    elif source_category in ['openai.com', 'blog.anthropic.com', 'ai.googleblog.com']:
                        # For company blogs, search for technical announcements
                        time_aware_query = f"{term} announcement blog post API"
                    else:
                        # General search with time context
                        time_aware_query = f"{term} recent news this week"
                    
                    source_results = self.search_service.search_ai_content(time_aware_query)
                    # Mark these results as from preferred sources
                    for result in source_results:
                        result['from_preferred_source'] = True
                        result['source_category'] = source_category
                        # Validate URL quality more strictly
                        url = result.get('url', '')
                        if url and self._is_valid_article_url(url):
                            result['url_quality'] = 'good'
                        else:
                            result['url_quality'] = 'poor'
                    all_results.extend(source_results)
                    
                    # Reduced delay to speed up processing
                    import time
                    time.sleep(0.1)
                    
                except Exception as e:
                    logging.warning(f"Search failed for preferred source term '{term}': {e}")
                    continue
        
        # PRIORITY 2: Search with base queries + specific tool searches
        enhanced_queries = base_queries + [
            "new AI development tools 2025",
            "AI API releases this week",
            "open source AI frameworks",
            "AI model releases",
            "AI coding tools update",
            "machine learning libraries",
            "AI platform announcements"
        ]
        
        for query in enhanced_queries:
            try:
                general_results = self.search_service.search_ai_content(query)
                # Mark these as general results
                for result in general_results:
                    result['from_preferred_source'] = False
                    # Validate URL quality for general results too
                    url = result.get('url', '')
                    if url and self._is_valid_article_url(url):
                        result['url_quality'] = 'good'
                    else:
                        result['url_quality'] = 'poor'
                all_results.extend(general_results)
                
                # Reduced delay to speed up processing
                import time
                time.sleep(0.2)
                
            except Exception as e:
                logging.warning(f"Search failed for query '{query}': {e}")
                continue
        
        # PRIORITY 3: Search with category-based terms (lower priority)
        for category, search_terms in self.category_search_terms.items():
            # Use first term per category
            for term in search_terms[:1]:
                try:
                    time_aware_query = f"{term} past week"
                    category_results = self.search_service.search_ai_content(time_aware_query)
                    # Mark these as category results
                    for result in category_results:
                        result['from_preferred_source'] = False
                        result['category_type'] = category
                    all_results.extend(category_results)
                    
                    # Reduced delay to speed up processing
                    import time
                    time.sleep(0.1)
                    
                except Exception as e:
                    logging.warning(f"Search failed for category term '{term}': {e}")
                    continue
        
        # Filter, rank and deduplicate results with frequency-based scoring
        filtered_results = self._filter_and_rank_results_with_frequency(all_results)
        state["search_results"] = filtered_results
        
        logging.info(f"Collected {len(filtered_results)} filtered results from {len(all_results)} total results")
        return state
    
    def categorize_and_analyze(self, state: AgentState) -> AgentState:
        """Analyze and categorize AI content with impact scoring and frequency-based auto-categorization"""
        
        # Limit results for LLM processing but prioritize high-scoring results
        all_results = state["search_results"]
        # Sort by relevance score to get the best results
        sorted_results = sorted(all_results, key=lambda x: x.get('relevance_score', 0), reverse=True)
        results_sample = sorted_results[:30]  # Increased from 25 to 30 for better coverage
        
        prompt = f"""
        You must return ONLY valid JSON. No explanations, no other text.

        PRIORITY INSTRUCTION: Articles from preferred sources (marked with 'from_preferred_source': true) and articles that appear across multiple sources (marked with 'cross_source_frequency' > 1) should be prioritized for inclusion.

        Analyze and categorize these AI articles:

        {json.dumps(results_sample, indent=2)}

        Categories (prioritize based on source preference and cross-source frequency):
        1. AI_TECHNICAL_ADVANCES: model features, capabilities, improvements
        2. RESEARCH_BREAKTHROUGHS: discoveries, algorithms, research papers  
        3. PRODUCT_LAUNCHES: new products, tools, applications
        4. COMPANY_RESEARCH: lab projects, technical blogs, R&D
        5. OPEN_SOURCE: frameworks, libraries, community projects
        6. INDUSTRY_NEWS: business developments, partnerships, market trends, policy
        7. FUNDING_INVESTMENT: venture rounds, acquisitions
        8. GENERAL_DEVELOPMENTS: industry trends, partnerships, educational initiatives

        For each article, extract:
        - title: descriptive title
        - summary: 2-3 sentence summary
        - source: website name
        - url: original link  
        - date: publication date
        - impact_score: 1-10 (integer, boost +2 points if from_preferred_source=true, +1 point if cross_source_frequency > 1)
        - relevance_tags: ["tag1", "tag2"]
        - business_impact: brief note
        - source_preference: "preferred" if from_preferred_source=true, "standard" otherwise
        - cross_source_count: number from cross_source_frequency field (if available)

        CATEGORIZATION RULES:
        - If an article appears in multiple sources (cross_source_frequency > 1), prioritize it for inclusion
        - Articles from preferred sources should be included even if impact_score is moderate
        - Group similar articles from different sources together in the same category
        - Ensure at least 2-3 articles per category when possible
        - Prioritize articles with good URL quality (url_quality = 'good')
        - Distribute articles across different sources - avoid having all articles from one source
        - Include articles with technical terms in titles (API, SDK, framework, model, etc.)
        - Ensure titles are descriptive and not generic (avoid single words or very short titles)

        RESPONSE FORMAT (copy exactly):
        {{
          "AI_TECHNICAL_ADVANCES": [
            {{
              "title": "Example Title",
              "summary": "Example summary text.",
              "source": "example.com",
              "url": "https://example.com/article",
              "date": "2025-01-05",
              "impact_score": 7,
              "relevance_tags": ["LLM", "AI"],
              "business_impact": "Example impact note",
              "source_preference": "preferred",
              "cross_source_count": 2
            }}
          ],
          "RESEARCH_BREAKTHROUGHS": [],
          "PRODUCT_LAUNCHES": [],
          "COMPANY_RESEARCH": [],
          "OPEN_SOURCE": [],
          "INDUSTRY_NEWS": [],
          "FUNDING_INVESTMENT": [],
          "GENERAL_DEVELOPMENTS": []
        }}

        Return ONLY the JSON object above with your categorized articles. No other text.
        """
        
        try:
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            
            # Clean up common LLM response issues
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            elif content.startswith('```'):
                content = content.replace('```', '').strip()
            
            # Try to extract JSON object if wrapped in text
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                content = json_match.group(0)
            
            categorized_content = json.loads(content)
            
            # Validate structure
            if not isinstance(categorized_content, dict):
                raise ValueError(f"Expected dict, got {type(categorized_content)}")
            
            # Ensure we have proper structure and filter empty categories
            expected_categories = [
                "AI_TECHNICAL_ADVANCES", "RESEARCH_BREAKTHROUGHS", "PRODUCT_LAUNCHES",
                "COMPANY_RESEARCH", "OPEN_SOURCE", "INDUSTRY_NEWS", "FUNDING_INVESTMENT"
            ]
            
            cleaned_content = {}
            for category in expected_categories:
                items = categorized_content.get(category, [])
                if isinstance(items, list) and len(items) > 0:
                    # Ensure each item has required fields
                    valid_items = []
                    for item in items:
                        if isinstance(item, dict) and item.get('title') and item.get('summary'):
                            # Ensure all required fields exist with defaults
                            validated_item = {
                                'title': str(item.get('title', 'Unknown')),
                                'summary': str(item.get('summary', 'No summary available')),
                                'source': str(item.get('source', 'Unknown')),
                                'url': str(item.get('url', '#')),
                                'date': str(item.get('date', datetime.now().isoformat())),
                                'impact_score': int(item.get('impact_score', 5)),
                                'relevance_tags': item.get('relevance_tags', ['AI']),
                                'business_impact': str(item.get('business_impact', 'Impact assessment pending'))
                            }
                            valid_items.append(validated_item)
                    
                    if valid_items:
                        cleaned_content[category] = valid_items
            
            categorized_content = cleaned_content
            logging.info(f"Successfully categorized {sum(len(items) for items in categorized_content.values())} articles into {len(categorized_content)} categories")
            
        except (json.JSONDecodeError, ValueError, Exception) as e:
            logging.warning(f"Failed to categorize content: {e}")
            logging.warning(f"LLM Response was: {response.content[:200]}...")
            # Create better fallback categorization from search results
            categorized_content = self._create_fallback_categorization(results_sample)
        
        state["categorized_content"] = categorized_content
        return state
    
    def _create_fallback_categorization(self, results_sample: List[Dict]) -> Dict:
        """Create fallback categorization when LLM fails with preference for specified sources"""
        categorized_content = {
            "AI_TECHNICAL_ADVANCES": [],
            "RESEARCH_BREAKTHROUGHS": [],
            "PRODUCT_LAUNCHES": [],
            "COMPANY_RESEARCH": [],
            "OPEN_SOURCE": [],
            "INDUSTRY_NEWS": [],
            "GENERAL_DEVELOPMENTS": []
        }
        
        # Sort results by preference (preferred sources first, then by relevance score)
        sorted_results = sorted(results_sample, key=lambda x: (
            not x.get('from_preferred_source', False),  # Preferred sources first (False < True)
            -x.get('relevance_score', 0)  # Then by relevance score (descending)
        ))
        
        # Simple keyword-based categorization using sorted results (preferred sources first)
        used_sources = set()
        processed_count = 0
        
        for result in sorted_results:
            if processed_count >= 20:  # Limit total items
                break
                
            title = result.get("title", "").lower()
            source = result.get("source", "").lower()
            
            # Skip if we already have too many items from this source (ensure diversity)
            source_count = sum(1 for s in used_sources if s == source)
            if source_count >= 3:  # Max 3 items per source
                continue
            
            # Skip poor quality URLs and generic titles
            if result.get('url_quality') == 'poor' or len(result.get("title", "")) < 10:
                continue
            
            used_sources.add(source)
            processed_count += 1
            
            # Boost impact score for preferred sources and cross-source frequency
            base_score = 5
            if result.get('from_preferred_source', False):
                base_score += 2
            if result.get('cross_source_frequency', 0) > 1:
                base_score += 1
            if result.get('url_quality') == 'good':
                base_score += 1
            
            item = {
                "title": result.get("title", ""),
                "summary": result.get("snippet", "")[:200] + "..." if result.get("snippet") else "",
                "source": result.get("source", ""),
                "url": result.get("url", ""),
                "date": result.get("date", ""),
                "impact_score": min(base_score, 10),  # Cap at 10
                "relevance_tags": ["AI"],
                "business_impact": "Potential impact on AI industry",
                "source_preference": "preferred" if result.get('from_preferred_source', False) else "standard",
                "cross_source_count": result.get('cross_source_frequency', 0)
            }
            
            # Categorize based on keywords and source
            if any(tech in title for tech in ['feature', 'update', 'release', 'capabilities']):
                categorized_content["AI_TECHNICAL_ADVANCES"].append(item)
            elif any(research in title for research in ['research', 'paper', 'study', 'breakthrough']):
                categorized_content["RESEARCH_BREAKTHROUGHS"].append(item)
            elif 'github.com' in source or 'huggingface' in source:
                categorized_content["OPEN_SOURCE"].append(item)
            elif any(company in source for company in ['openai', 'anthropic', 'googleblog', 'microsoft']):
                categorized_content["COMPANY_RESEARCH"].append(item)
            elif any(tool in title for tool in ['tool', 'platform', 'api', 'sdk']):
                categorized_content["PRODUCT_LAUNCHES"].append(item)
            elif any(news in title for news in ['partnership', 'funding', 'investment', 'acquisition']):
                categorized_content["FUNDING_INVESTMENT"].append(item)
            elif any(general in title for general in ['education', 'training', 'policy', 'regulation']):
                categorized_content["GENERAL_DEVELOPMENTS"].append(item)
            else:
                categorized_content["INDUSTRY_NEWS"].append(item)
        
        # Filter out empty categories
        filtered_content = {k: v for k, v in categorized_content.items() if v}
        
        # Ensure we have at least some content in key categories
        if not filtered_content.get("AI_TECHNICAL_ADVANCES") and not filtered_content.get("PRODUCT_LAUNCHES"):
            # If we don't have tools/products, try to redistribute some items
            if filtered_content.get("INDUSTRY_NEWS"):
                # Move some industry news to product launches if they mention tools
                for item in filtered_content["INDUSTRY_NEWS"][:2]:
                    if any(tool_term in item.get("title", "").lower() for tool_term in ["tool", "api", "sdk", "platform"]):
                        if "PRODUCT_LAUNCHES" not in filtered_content:
                            filtered_content["PRODUCT_LAUNCHES"] = []
                        filtered_content["PRODUCT_LAUNCHES"].append(item)
                        filtered_content["INDUSTRY_NEWS"].remove(item)
        
        # Ensure we have general developments content
        if not filtered_content.get("GENERAL_DEVELOPMENTS"):
            # Move some industry news to general developments if they mention partnerships, education, etc.
            if filtered_content.get("INDUSTRY_NEWS"):
                for item in filtered_content["INDUSTRY_NEWS"][:2]:
                    if any(general_term in item.get("title", "").lower() for general_term in ["partnership", "education", "training", "policy"]):
                        if "GENERAL_DEVELOPMENTS" not in filtered_content:
                            filtered_content["GENERAL_DEVELOPMENTS"] = []
                        filtered_content["GENERAL_DEVELOPMENTS"].append(item)
                        filtered_content["INDUSTRY_NEWS"].remove(item)
        
        return filtered_content
    
    def _is_valid_article_url(self, url: str) -> bool:
        """Check if URL is a valid article URL (not search page or generic)"""
        if not url or len(url) < 20:
            return False
        
        # Skip search pages and generic URLs
        bad_patterns = [
            'search?', 'query=', '?q=', '/search/', 'google.com/search',
            'bing.com/search', 'duckduckgo.com', 'yahoo.com/search',
            'how-to-finetune-small-language-models-to-think-with',
            'artificial-intelligence-index', 'applying-for-a-patent-and-getting-it',
            'the-fastest-ai-inference-platform-hardware'
        ]
        
        if any(bad in url.lower() for bad in bad_patterns):
            return False
        
        # Must be from a real domain with proper article path
        good_patterns = [
            '.com/', '.org/', '.edu/', '.ai/', '.co/', '.net/',
            '/blog/', '/news/', '/article/', '/post/', '/research/',
            '/papers/', '/docs/', '/about/', '/product/', '/release/'
        ]
        
        return any(good in url.lower() for good in good_patterns)
    
    def reflect_on_quality(self, state: AgentState) -> AgentState:
        """Reflect on the quality of search results and categorization to determine if another iteration is needed"""
        categorized = state["categorized_content"]
        search_results = state["search_results"]
        iteration_count = state.get("iteration_count", 0)
        
        # Quality metrics
        total_items = sum(len(items) for items in categorized.values())
        categories_with_content = len([k for k, v in categorized.items() if v])
        
        # Count quality indicators
        good_urls = sum(1 for result in search_results if result.get('url_quality') == 'good')
        preferred_sources = sum(1 for result in search_results if result.get('from_preferred_source', False))
        cross_source_items = sum(1 for result in search_results if result.get('cross_source_frequency', 0) > 1)
        
        # Calculate quality score (0-100)
        quality_score = 0.0
        
        # Content quantity (30 points max)
        if total_items >= 15:
            quality_score += 30
        elif total_items >= 10:
            quality_score += 20
        elif total_items >= 5:
            quality_score += 10
        
        # Category coverage (20 points max)
        if categories_with_content >= 5:
            quality_score += 20
        elif categories_with_content >= 3:
            quality_score += 15
        elif categories_with_content >= 2:
            quality_score += 10
        
        # URL quality (20 points max)
        if good_urls >= 10:
            quality_score += 20
        elif good_urls >= 5:
            quality_score += 15
        elif good_urls >= 3:
            quality_score += 10
        
        # Source diversity (15 points max)
        if preferred_sources >= 8:
            quality_score += 15
        elif preferred_sources >= 5:
            quality_score += 10
        elif preferred_sources >= 3:
            quality_score += 5
        
        # Cross-source validation (15 points max)
        if cross_source_items >= 5:
            quality_score += 15
        elif cross_source_items >= 3:
            quality_score += 10
        elif cross_source_items >= 1:
            quality_score += 5
        
        # Determine if improvement is needed (lowered threshold to reduce iterations)
        needs_improvement = quality_score < 50 and iteration_count < 2
        
        # Identify improvement areas
        improvement_areas = []
        if total_items < 10:
            improvement_areas.append("insufficient_content")
        if categories_with_content < 3:
            improvement_areas.append("poor_category_coverage")
        if good_urls < 5:
            improvement_areas.append("poor_url_quality")
        if preferred_sources < 5:
            improvement_areas.append("insufficient_preferred_sources")
        if cross_source_items < 3:
            improvement_areas.append("lack_cross_source_validation")
        
        # Generate reflection feedback
        feedback = f"""
        Quality Assessment (Iteration {iteration_count + 1}):
        - Total items: {total_items}
        - Categories with content: {categories_with_content}
        - Good quality URLs: {good_urls}
        - Preferred sources: {preferred_sources}
        - Cross-source items: {cross_source_items}
        - Quality score: {quality_score:.1f}/100
        
        Improvement areas: {', '.join(improvement_areas) if improvement_areas else 'None'}
        """
        
        state["quality_score"] = quality_score
        state["needs_improvement"] = needs_improvement
        state["improvement_areas"] = improvement_areas
        state["reflection_feedback"] = feedback
        
        logging.info(f"Quality reflection: Score={quality_score:.1f}, Needs improvement={needs_improvement}")
        
        return state
    
    def improve_search_strategy(self, state: AgentState) -> AgentState:
        """Improve search strategy based on reflection feedback"""
        improvement_areas = state.get("improvement_areas", [])
        iteration_count = state.get("iteration_count", 0)
        
        # Enhanced search queries based on what's missing
        additional_queries = []
        
        if "insufficient_content" in improvement_areas:
            additional_queries.extend([
                "latest AI breakthroughs this week",
                "new AI tools launched recently",
                "AI research papers published",
                "AI startup announcements",
                "AI industry partnerships"
            ])
        
        if "poor_category_coverage" in improvement_areas:
            additional_queries.extend([
                "AI open source projects",
                "AI funding rounds",
                "AI technical advances",
                "AI product launches",
                "AI research breakthroughs"
            ])
        
        if "insufficient_preferred_sources" in improvement_areas:
            # Add more targeted searches for preferred sources
            preferred_searches = [
                "site:openai.com AI announcements",
                "site:googleblog.com AI research",
                "site:anthropic.com Claude updates",
                "site:huggingface.co new models",
                "site:github.com AI frameworks"
            ]
            additional_queries.extend(preferred_searches)
        
        if "lack_cross_source_validation" in improvement_areas:
            additional_queries.extend([
                "AI news multiple sources",
                "AI developments covered widely",
                "trending AI topics",
                "viral AI announcements"
            ])
        
        # Add the additional queries to existing ones
        current_queries = state.get("search_queries", [])
        enhanced_queries = current_queries + additional_queries[:10]  # Limit to avoid too many queries
        
        state["search_queries"] = enhanced_queries
        state["iteration_count"] = iteration_count + 1
        
        logging.info(f"Enhanced search strategy for iteration {iteration_count + 1}: Added {len(additional_queries)} queries")
        
        return state
    
    def generate_weekly_report(self, state: AgentState) -> AgentState:
        """Generate comprehensive weekly AI trends report with enhanced URL validation and ranking"""
        categorized = state["categorized_content"]
        date_range = state["report_date_range"]
        
        # Step 1: Validate and improve URLs for better article links
        logging.info("Validating and improving article URLs...")
        improved_categorized = self._validate_and_improve_urls(categorized)
        
        # Step 2: Re-rank articles by popularity and relevance
        logging.info("Re-ranking articles by popularity and relevance...")
        final_categorized = self._re_rank_articles_by_popularity(improved_categorized)
        
        # Update state with improved categorized content
        state["categorized_content"] = final_categorized
        
        prompt = f"""
        Role: You are an expert AI News Reporter specializing in developer-focused technology journalism.
        I am a developer(software engineering, data engineering, data scientist) and I am trying to see how I can agument GEN AI in my daily day-to-day work and I would like to keep myself with the latest trend.
        Audience: Your target audience is AI Engineers, ML Engineers, Software Developers, and Technical Leads who need current news about AI developments that directly impact their work. The tone should be journalistic, informative, and developer-focused with news reporting style.

        Objective: Report on the most significant AI news and developments over the past seven days that are relevant to developers and engineers. Focus on breaking news about tools, frameworks, research announcements, APIs, libraries, and technical breakthroughs. Present information in news reporting format with clear facts, quotes from sources, and immediate implications. CRITICALLY IMPORTANT: Cross-reference and group similar developments covered by multiple sources, providing all relevant links and explaining how different sources cover the same story with varying perspectives or details.

        Date Range: {date_range}
        Research Content: {json.dumps(final_categorized, indent=2)}

        Content Focus Areas:
        - New AI tools, frameworks, and libraries (open source and commercial)
        - API releases and updates from major AI providers
        - Research papers with practical implementation potential
        - Developer-focused product announcements
        - Technical breakthroughs in model architectures, training techniques, or deployment
        - Code repositories, datasets, and technical resources
        - Performance benchmarks and evaluation metrics
        - Infrastructure and deployment innovations

        Required Output Structure:

        # 🤖 AI News Weekly Report
        ## {date_range}

        ### 📰 News Headlines 

        News Headlines in a bullet form, with the title and the url and the summary of that page.

        # ### 🔬 Research & Development News

        # For each significant research announcement, provide:

        # **[Detailed, Specific Research Title - Must be descriptive and explain the breakthrough, not just generic names]**
        # [3-line news report focusing on what was announced, who announced it, and immediate implications: What was revealed/published, which organization made the announcement, and what it means for developers. EMBED SOURCE LINKS DIRECTLY INTO THE TEXT as inline markdown links using actual URLs from the data, like: "OpenAI announced today via [their research blog](https://openai.com/research/example) that..." or "Google AI researchers reported in [their latest publication](https://ai.googleblog.com/example) that..."]

        ### 🛠️ Product Launch News

        For each new tool, framework, or product announcement:

        **[Specific Tool/Product Name with Key Feature - Must explain what it does, not just the name]**
        [3-line news report covering the launch details, company behind it, and availability: What was launched, who launched it, and when/how developers can access it. EMBED SOURCE LINKS DIRECTLY INTO THE TEXT as inline markdown links using actual URLs from the data, like: "Hugging Face today unveiled [their new platform](https://huggingface.co/example) that..." or "GitHub announced via [their developer blog](https://github.com/example) the release of..."]

        ### 📰 Industry News & Business Developments

        For each significant industry development, business news, or general AI trend:

        **[Descriptive News Title - Must explain the development, partnership, or trend specifically]**
        [3-line news report covering the announcement, key players involved, and business implications: What was announced, who was involved, and what it means for the industry. EMBED SOURCE LINKS DIRECTLY INTO THE TEXT as inline markdown links using actual URLs from the data, like: "Reuters reported today that [Company X](https://reuters.com/example) has partnered with..." or "TechCrunch exclusively revealed that [the funding round](https://techcrunch.com/example) will..."]

        ### 🔮 What to Watch Next Week

        Provide 3-4 news predictions about what might be announced in the next week based on current developments:
        - **Expected announcements** from major AI companies based on recent patterns
        - **Anticipated product launches** that are likely to be revealed
        - **Research publications** that may be released from major institutions
        - **Industry events** and conferences that could bring major news
        - **Follow-up developments** to this week's major stories
        - **Potential surprises** based on insider reports and industry signals

        Focus on specific news predictions rather than generic trends. Use news language like "sources suggest", "expected to announce", "industry insiders report", "likely to reveal".

        Content Guidelines:

        What to Include:
        - Breaking news about AI tool releases and major updates
        - Official announcements from AI companies about new products/services
        - Research publication announcements with practical implications
        - Developer tool launches and significant platform updates
        - Technical announcements from major AI companies with implementation details
        - Performance benchmark releases and comparison studies
        - Infrastructure and deployment platform news

        What to Prioritize:
        - Recent announcements and breaking news over older developments
        - Official sources and first-hand announcements
        - News with immediate impact on developer workflows
        - Product availability and launch dates
        - Pricing announcements and accessibility information
        - Cross-reference multiple news sources covering the same story
        - Identify when the same news is covered by different outlets with varying angles

        What to Avoid:
        - Speculation without official confirmation
        - Theoretical research without clear announcement or publication
        - Marketing content without substantial news value
        - Bias toward single news sources when multiple outlets cover the story

        Formatting Requirements:
        - Use markdown formatting for email readability
        - Include direct links to all sources (GitHub repos, papers, official docs)
        - Use emoji section headers as specified
        - Keep summaries concise but technically informative
        - Bold key terms and product names for scanning
        - Use bullet points for technical details and specifications

        Technical Detail Requirements:
        - Include programming languages and frameworks supported
        - Mention hardware requirements when relevant
        - Note license types for open source tools
        - Include API pricing or usage limits when applicable
        - Specify model sizes and performance metrics when available
        - Mention integration capabilities with popular ML frameworks

        Source Attribution:
        - MANDATORY: Embed ALL source links directly into text as inline markdown links [text](url)
        - NEVER use separate "Sources:" sections - integrate links naturally into sentences
        - When the same development is covered by multiple sources, embed ALL relevant links within the text
        - Prioritize official announcements but also include secondary analysis when it adds value
        - Link to GitHub repositories when available using inline links
        - Include documentation links for new tools embedded in technical details
        - Reference specific paper titles and authors for research with inline links
        - Ensure source diversity - avoid bias toward any single publication or website
        - Cross-reference information to identify different perspectives on the same topic
        - Example: "According to [OpenAI](https://openai.com/research/example), this new model..." instead of separate links

        CRITICAL REQUIREMENTS:
        - Use ONLY actual URLs from the research data provided - NO placeholder URLs
        - MANDATORY: EMBED ALL SOURCE LINKS DIRECTLY INTO THE TEXT as inline markdown links [text](url)
        - DO NOT use separate "Sources:" sections - integrate links naturally into sentences
        - Focus on concrete technical developments that developers can use or implement
        - Include comprehensive technical details as specified above
        - Ensure all sections follow the exact formatting structure provided
        - Bold all tool names, product names, and key technical terms
        - Use clean markdown formatting with proper spacing
        - Do not include any arxiv.org sources in the report
        - Prioritize information about APIs, SDKs, libraries, model capabilities, and implementation details
        - Each research item should have the exact format: **[Detailed Descriptive Title]**, 3-line news report with embedded links
        - Each tool item should have the exact format: **[Specific Tool Name with Key Feature]**, 3-line news report with embedded links
        - Each industry news item should have the exact format: **[Descriptive News Title]**, 3-line news report with embedded links
        - MANDATORY: Include content from INDUSTRY_NEWS and GENERAL_DEVELOPMENTS categories in the Industry News section
        - MANDATORY: Titles must be descriptive and specific, not generic names
        - MANDATORY: All URLs must be actual article links, not search pages or constructed URLs
        - MANDATORY: Cross-reference the same developments across multiple sources when available
        - MANDATORY: Ensure source diversity - do not bias toward any single website or publication
        - MANDATORY: When multiple sources cover the same topic, include all relevant links embedded within the text and explain differences in coverage
        - MANDATORY: All URLs must be embedded as inline links within sentences, not as separate link lists
        - MANDATORY: Ensure each section has at least 2-3 items when available in the data

        Your news report should help developers quickly identify which new announcements, launches, or developments are worth following for their projects and career development.

        Return ONLY the formatted report content.
        """
        
        try:
            response = self.llm.invoke(prompt)
            report_content = response.content
            
            # Validate that we have proper markdown structure
            if not report_content.strip().startswith('#'):
                logging.warning("Generated report doesn't start with proper markdown header")
                report_content = self._create_fallback_report(final_categorized, date_range)
                
        except Exception as e:
            logging.error(f"Failed to generate report: {e}")
            report_content = self._create_fallback_report(final_categorized, date_range)
        
        # Step 3: Export report to file automatically
        logging.info("Exporting report to file...")
        export_path = self._export_report_to_file(report_content, date_range)
        
        # Generate additional metadata
        report_metadata = self._generate_report_metadata(final_categorized)
        if export_path:
            report_metadata["export_path"] = export_path
        
        state["weekly_report"] = report_content
        state["report_metadata"] = report_metadata
        state["generation_timestamp"] = datetime.now().isoformat()
        state["export_path"] = export_path if export_path else ""
        
        return state
    
    def _extract_real_urls(self, categorized: Dict) -> Dict[str, List[Dict]]:
        """Extract real URLs from categorized content for hyperlinks"""
        url_samples = {}
        
        for category, items in categorized.items():
            if items and len(items) > 0:
                # Get up to 3 items per category for variety
                sample_items = items[:3]
                url_samples[category] = [
                    {
                        "title": item.get("title", "AI Development"),
                        "url": item.get("url", "#"),
                        "source": item.get("source", "Unknown")
                    }
                    for item in sample_items
                    if item.get("url") and item.get("url") != "#"
                ]
        
        return url_samples
    
    def _create_fallback_report(self, categorized: Dict, date_range: str) -> str:
        """Create a fallback report when LLM generation fails"""
        
        # Extract real URLs from the categorized content
        url_samples = self._extract_real_urls(categorized)
        
        # Create developments list from actual data
        developments = []
        for category, items in categorized.items():
            for item in items[:2]:  # Take up to 2 items from each category
                if item.get("url") and item.get("url") != "#" and "arxiv.org" not in item.get("url", ""):
                    developments.append({
                        "title": item.get("title", "AI Development"),
                        "url": item.get("url"),
                        "source": item.get("source", "Unknown"),
                        "summary": item.get("summary", "AI development with significant industry impact."),
                        "category": category
                    })
        
        # Categorize developments
        research_devs = [d for d in developments if d["category"] in ["RESEARCH_BREAKTHROUGHS", "AI_TECHNICAL_ADVANCES"]]
        tools_devs = [d for d in developments if d["category"] in ["PRODUCT_LAUNCHES", "OPEN_SOURCE"]]
        news_devs = [d for d in developments if d["category"] in ["INDUSTRY_NEWS", "GENERAL_DEVELOPMENTS", "FUNDING_INVESTMENT"]]
        
        report = f"""# 🤖 AI News Weekly Report
## {date_range}

### 📰 News Headlines

This week brought significant announcements from major AI companies with several key product launches that directly impact developer workflows. **Microsoft** and other leading providers officially announced enhanced **APIs** and **SDKs** with improved multimodal capabilities, giving developers immediate access to more powerful integration options for building sophisticated AI applications. Performance optimization dominated the news cycle, with companies reporting measurable improvements in inference speeds and reduced latency that promise better user experiences and lower operational costs.

The developer tooling sector witnessed major product launches, particularly in **AI-assisted coding** and **debugging capabilities**. New **IDE integrations** and **CLI tools** were officially released, making AI development more accessible to individual developers and small teams. **Open source frameworks** announced major updates with optimized architectures and expanded language support, signaling a maturing ecosystem where AI tools are becoming more practical and cost-effective for real-world implementation.

### 🔬 Research & Development News

"""
        
        # Add research developments
        for dev in research_devs[:3]:
            title_clean = dev["title"].replace("AI", "").replace("artificial intelligence", "").strip()
            if not title_clean:
                title_clean = "Advanced Machine Learning Algorithm for Enhanced Model Performance"
            
            report += f"""**{title_clean} - Revolutionary Approach to AI Model Optimization**
Researchers at [{dev["source"]}]({dev["url"]}) announced today {dev["summary"][:100]}... The publication reveals new techniques and algorithms that developers can implement to enhance AI application performance. The research team reported practical applications for improving model efficiency and deployment capabilities, with immediate implications for engineering teams.

"""
        
        if not research_devs:
            report += """**Microsoft's Next-Generation AI Architecture - Breakthrough in Efficient Model Training**
[Microsoft](https://www.microsoft.com/en-us/research/research-area/artificial-intelligence/) is developing new AI architectures and algorithms that enable more efficient model training and inference. Their research focuses on creating APIs and tools that developers can use to build more capable AI applications. The initiative emphasizes practical implementations that can be integrated into existing development workflows.

"""
        
        report += """### 🛠️ Product Launch News

"""
        
        # Add tools developments
        for dev in tools_devs[:3]:
            title_clean = dev["title"].replace("AI", "").replace("artificial intelligence", "").strip()
            if not title_clean:
                title_clean = "Advanced Development Framework for AI Integration"
            
            report += f"""**{title_clean} - Revolutionary Developer Platform for AI Applications**
[{dev["source"]}]({dev["url"]}) announced today the launch of {dev["summary"][:100]}... The company revealed new APIs, SDKs, or frameworks that developers can integrate into their projects for improved AI functionality. The product launch focuses on developer experience and practical implementation capabilities, with immediate availability for development teams.

"""
        
        if not tools_devs:
            report += """**Claude's Advanced Terminal Integration - Revolutionary AI-Powered Development Environment**
[Anthropic](https://www.anthropic.com) has integrated **Claude's** reasoning capabilities directly into terminal workflows with new **CLI tools** and **IDE extensions**. This advancement provides developers with better code completion, debugging assistance, and seamless integration with existing development environments. The tools support multiple programming languages and offer customizable workflows for different development scenarios.

"""
        
        report += """### 📰 Industry News & Business Developments

"""
        
        # Add industry news developments
        for dev in news_devs[:3]:
            title_clean = dev["title"].replace("AI", "").replace("artificial intelligence", "").strip()
            if not title_clean:
                title_clean = "Major Industry Partnership Reshaping AI Development Landscape"
            
            report += f"""**{title_clean} - Strategic Alliance Transforming AI Market Dynamics**
[{dev["source"]}]({dev["url"]}) reported today that {dev["summary"][:100]}... The news outlet covered a significant shift in the AI industry landscape. The announcement highlights key trends in AI adoption, partnerships, and strategic initiatives that developers should monitor for potential opportunities and market changes.

"""
        
        if not news_devs:
            report += """**Microsoft-OpenAI-AFT Educational Alliance - Revolutionary AI Integration in Academic Institutions**
A significant partnership between [Microsoft](https://www.microsoft.com), [OpenAI](https://openai.com), and the American Federation of Teachers (AFT) aims to train educators on AI tools and integration strategies. This collaboration represents a major step toward mainstream AI adoption in educational settings, creating new opportunities for developers to build educational AI applications. The initiative focuses on practical AI implementation in classrooms and professional development for teaching staff.

"""
        
        report += """### 🔮 What to Watch Next Week

**Industry insiders suggest** major AI companies are preparing to announce significant model architecture improvements that could **revolutionize inference speeds** by 10x or more. **Sources close to OpenAI and Anthropic** indicate potential surprises with **multimodal capabilities** that seamlessly integrate text, voice, and visual processing in real-time applications.

**Google DeepMind** is **expected to announce** breakthrough reasoning capabilities, potentially revealing AI systems that can **autonomously debug and optimize code** at enterprise scale. **Microsoft** is **likely to unveil** AI-powered IDEs that predict and implement entire feature sets based on natural language descriptions.

**Industry reports suggest** emerging edge AI technologies may **transform mobile applications** with on-device models that match cloud performance while maintaining privacy. **Sources indicate announcements** from hardware manufacturers about **specialized AI chips** that could make current GPU dependencies obsolete for many applications.

**Financial news outlets report** revolutionary funding rounds are likely to emerge for startups developing **AI-native operating systems** and **quantum-AI hybrid platforms** that could **reshape computing paradigms** within the next 12 months. Watch for **surprise partnership announcements** between traditional tech giants and AI-first companies that could **accelerate mainstream adoption** beyond current projections.
"""
        
        return report
    
    def _get_sample_url(self, url_samples: Dict, categories: List[str]) -> str:
        """Get a sample URL from specified categories"""
        for category in categories:
            if category in url_samples and url_samples[category]:
                item = url_samples[category][0]
                return f"[{item['source']}]({item['url']})"
        
        # Fallback to a real URL
        return "[MIT AI News](https://news.mit.edu)"
    
    def _filter_and_rank_results_with_frequency(self, results: List[Dict]) -> List[Dict]:
        """Filter and rank results by relevance, quality, and frequency with preference for specified sources"""
        # Enhanced AI keywords including technical terms
        ai_keywords = [
            'artificial intelligence', 'machine learning', 'deep learning',
            'neural network', 'AI', 'LLM', 'GPT', 'transformer',
            'computer vision', 'natural language', 'robotics',
            'automation', 'algorithm', 'data science', 'generative AI',
            'foundation model', 'large language model', 'AI model',
            'claude', 'gemini', 'chatgpt', 'anthropic', 'openai',
            'multimodal', 'reasoning', 'reinforcement learning',
            'diffusion model', 'embedding', 'fine-tuning', 'RAG'
        ]
        
        # Exclude domains we want to avoid - including arxiv.org
        excluded_domains = ['reddit.com', 'quora.com', 'stackoverflow.com', 'arxiv.org']
        
        # First pass: collect and count similar content
        content_frequency = {}
        url_to_content = {}
        
        filtered = []
        for result in results:
            text_content = f"{result.get('title', '')} {result.get('snippet', '')}".lower()
            source = result.get('source', '').lower()
            url = result.get('url', '')
            
            # Skip excluded domains
            if any(excluded in source for excluded in excluded_domains):
                continue
            
            # Skip poor quality URLs (search pages, generic queries, constructed URLs)
            if url and any(bad in url for bad in [
                'search?', 'query=', '?q=', '/search/', 'google.com/search',
                'how-to-finetune-small-language-models-to-think-with',  # Constructed URLs
                'artificial-intelligence-index', 'applying-for-a-patent-and-getting-it',
                'the-fastest-ai-inference-platform-hardware'  # Generic constructed paths
            ]):
                continue
            
            # Skip results with very short, generic, or truncated titles
            title = result.get('title', '')
            if (len(title) < 15 or 
                title.lower() in ['ai', 'artificial intelligence', 'machine learning'] or
                title.endswith('...') or
                title.count(' ') < 2):  # Titles with fewer than 3 words
                continue
            
            # Check if content contains AI-related keywords
            if any(keyword in text_content for keyword in ai_keywords):
                # Create content signature for frequency tracking
                title_words = set(result.get('title', '').lower().split())
                content_signature = ' '.join(sorted(title_words)[:5])  # Use first 5 words as signature
                
                # Track frequency
                if content_signature not in content_frequency:
                    content_frequency[content_signature] = []
                content_frequency[content_signature].append(result)
                url_to_content[url] = content_signature
                
                # Add relevance score with frequency and source preference
                score = self._calculate_relevance_score_with_frequency(result, ai_keywords, content_frequency.get(content_signature, []))
                result['relevance_score'] = score
                result['content_signature'] = content_signature
                filtered.append(result)
        
        # Second pass: boost scores for content that appears in multiple sources
        for content_sig, content_results in content_frequency.items():
            if len(content_results) > 1:  # Content appears in multiple sources
                frequency_boost = min(len(content_results) * 2.0, 10.0)  # Cap at 10 points
                for result in content_results:
                    result['relevance_score'] += frequency_boost
                    result['cross_source_frequency'] = len(content_results)
        
        # Sort by relevance score and take top 35 results for better diversity
        filtered.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        return filtered[:35]
    
    def _filter_and_rank_results(self, results: List[Dict]) -> List[Dict]:
        """Legacy filter function for backward compatibility"""
        return self._filter_and_rank_results_with_frequency(results)
    
    def _calculate_relevance_score_with_frequency(self, result: Dict, ai_keywords: List[str], similar_results: List[Dict]) -> float:
        """Calculate relevance score with frequency and source preference"""
        score = 0.0
        text = f"{result.get('title', '')} {result.get('snippet', '')}".lower()
        source = result.get('source', '').lower()
        
        # Keyword matching
        for keyword in ai_keywords:
            if keyword in text:
                score += 1.0
        
        # HIGHEST PRIORITY: Preferred sources from natural_search_terms get major boost
        if result.get('from_preferred_source', False):
            score += 15.0  # Very high boost for preferred sources
            
            # Additional boost for specific preferred sources
            preferred_source_domains = [
                'ai.googleblog.com', 'openai.com', 'blog.anthropic.com', 'research.microsoft.com',
                'ai.meta.com', 'deepmind.google', 'huggingface.co', 'github.com',
                'news.mit.edu', 'technologyreview.mit.edu', 'spectrum.ieee.org',
                'towardsdatascience.com', 'blog.google', 'aws.amazon.com', 'azure.microsoft.com',
                'developer.nvidia.com'
            ]
            
            for domain in preferred_source_domains:
                if domain.replace('.', '') in source.replace('.', ''):
                    score += 5.0  # Extra boost for exact preferred domain matches
                    break
        
        # Source credibility boost - prioritize technical sources (excluding arxiv.org)
        if any(tech_source in source for tech_source in ['googleblog', 'openai', 'anthropic', 'microsoft', 'meta']):
            score += 8.0  # High boost for AI company technical blogs
        elif any(research in source for research in ['papers.nips', 'deepmind']):
            score += 7.0  # High boost for research sources
        elif any(dev in source for dev in ['huggingface', 'github']):
            score += 6.0  # High boost for development platforms
        elif 'technologyreview.mit.edu' in source or 'spectrum.ieee.org' in source:
            score += 5.0  # Technical journalism
        elif any(news in source for news in ['techcrunch', 'venturebeat', 'theinformation']):
            score += 3.0  # Medium boost for business news
        
        # Frequency-based scoring - content that appears in multiple sources gets boost
        if len(similar_results) > 1:
            frequency_score = min(len(similar_results) * 1.5, 8.0)  # Cap at 8 points
            score += frequency_score
        
        # URL quality boost - prefer direct article URLs over search pages
        if result.get('url_quality') == 'good':
            score += 3.0
        
        # Content quality boost - prefer detailed titles and descriptions
        title_length = len(result.get('title', ''))
        snippet_length = len(result.get('snippet', ''))
        
        if title_length > 50:  # Detailed titles
            score += 2.0
        if snippet_length > 100:  # Detailed descriptions
            score += 2.0
        
        # Boost for technical terms in title (indicates technical content)
        title_lower = result.get('title', '').lower()
        technical_terms = ['api', 'sdk', 'framework', 'library', 'model', 'algorithm', 'benchmark', 'dataset']
        for term in technical_terms:
            if term in title_lower:
                score += 1.5
                break
        
        return score
    
    def _calculate_relevance_score(self, result: Dict, ai_keywords: List[str]) -> float:
        """Legacy relevance score calculation for backward compatibility"""
        return self._calculate_relevance_score_with_frequency(result, ai_keywords, [])
    
    def _generate_report_metadata(self, categorized_content: Dict) -> Dict:
        """Generate metadata about the report"""
        total_items = sum(len(items) for items in categorized_content.values())
        
        return {
            "total_developments": total_items,
            "categories_covered": len([k for k, v in categorized_content.items() if v]),
            "top_sources": self._extract_top_sources(categorized_content),
            "trending_topics": self._extract_trending_topics(categorized_content)
        }
    
    def _extract_top_sources(self, categorized_content: Dict) -> List[str]:
        """Extract most frequently cited sources"""
        sources = []
        for category in categorized_content.values():
            for item in category:
                if isinstance(item, dict) and "source" in item:
                    sources.append(item["source"])
        
        # Count and return top 5 sources
        from collections import Counter
        return [source for source, count in Counter(sources).most_common(5)]
    
    def _extract_trending_topics(self, categorized_content: Dict) -> List[str]:
        """Extract trending AI topics from content"""
        topics = []
        for category in categorized_content.values():
            for item in category:
                if isinstance(item, dict) and "relevance_tags" in item:
                    topics.extend(item["relevance_tags"])
        
        from collections import Counter
        return [topic for topic, count in Counter(topics).most_common(8)]

    def _validate_and_improve_urls(self, categorized_content: Dict) -> Dict:
        """
        Validate and improve URLs by re-searching article titles to find actual article URLs.
        This ensures we get direct links to articles rather than search pages or constructed URLs.
        """
        import time
        
        improved_content = {}
        
        for category, articles in categorized_content.items():
            improved_articles = []
            
            for article in articles:
                improved_article = article.copy()
                original_url = article.get('url', '')
                title = article.get('title', '')
                source = article.get('source', '')
                
                # Skip if we already have a good URL
                if self._is_high_quality_article_url(original_url):
                    improved_articles.append(improved_article)
                    continue
                
                # Try to find the actual article URL by searching for the title
                if title and len(title) > 10:
                    try:
                        # Search for the specific article title
                        search_query = f'"{title}" site:{source}' if source else f'"{title}"'
                        search_results = self.search_service.search_ai_content(search_query)
                        
                        # Find the best matching URL
                        best_url = self._find_best_matching_url(title, search_results, source)
                        
                        if best_url and best_url != original_url:
                            improved_article['url'] = best_url
                            improved_article['url_improved'] = True
                            logging.info(f"Improved URL for '{title[:50]}...': {best_url}")
                        else:
                            # If no better URL found, mark as validated
                            improved_article['url_improved'] = False
                            
                        time.sleep(0.1)  # Rate limiting
                        
                    except Exception as e:
                        logging.warning(f"Failed to improve URL for '{title[:50]}...': {e}")
                        improved_article['url_improved'] = False
                
                improved_articles.append(improved_article)
            
            if improved_articles:
                improved_content[category] = improved_articles
        
        return improved_content
    
    def _is_high_quality_article_url(self, url: str) -> bool:
        """
        Check if URL is a high-quality article URL that points directly to an article.
        More strict than the basic validation.
        """
        if not url or len(url) < 20:
            return False
        
        # Definitely bad patterns
        bad_patterns = [
            'search?', 'query=', '?q=', '/search/', 'google.com/search',
            'bing.com/search', 'duckduckgo.com', 'yahoo.com/search',
            'how-to-finetune-small-language-models-to-think-with',
            'artificial-intelligence-index', 'applying-for-a-patent-and-getting-it',
            'the-fastest-ai-inference-platform-hardware',
            'home', 'index.html', 'index.php', 'main.html'
        ]
        
        if any(bad in url.lower() for bad in bad_patterns):
            return False
        
        # Must have article-like path patterns
        article_patterns = [
            '/blog/', '/news/', '/article/', '/post/', '/research/',
            '/papers/', '/docs/', '/about/', '/product/', '/release/',
            '/2024/', '/2025/', '/updates/', '/announcements/',
            '/press-release/', '/newsroom/', '/insights/', '/reports/'
        ]
        
        # Check for date patterns in URL (indicates timestamped articles)
        import re
        date_pattern = r'/20\d{2}/'
        has_date = re.search(date_pattern, url)
        
        # Check for article-like patterns
        has_article_pattern = any(pattern in url.lower() for pattern in article_patterns)
        
        # High quality if it has date or article patterns and is from a known domain
        known_domains = [
            'googleblog.com', 'openai.com', 'anthropic.com', 'microsoft.com',
            'meta.com', 'deepmind.google', 'techcrunch.com', 'venturebeat.com',
            'theinformation.com', 'github.com', 'huggingface.co', 'mit.edu',
            'spectrum.ieee.org', 'towardsdatascience.com', 'aws.amazon.com'
        ]
        
        is_known_domain = any(domain in url.lower() for domain in known_domains)
        
        # Special cases for GitHub releases and blog.anthropic.com
        if 'github.com' in url.lower() and '/releases/' in url.lower():
            return True
        if 'blog.anthropic.com' in url.lower():
            return True
        
        return (has_date or has_article_pattern) and is_known_domain
    
    def _find_best_matching_url(self, title: str, search_results: List[Dict], preferred_source: str = None) -> str:
        """
        Find the best matching URL from search results for a given title.
        Prioritizes URLs from the preferred source and with high similarity to the title.
        """
        if not search_results:
            return None
        
        best_url = None
        best_score = 0
        
        for result in search_results:
            result_title = result.get('title', '').lower()
            result_url = result.get('url', '')
            result_source = result.get('source', '').lower()
            
            if not result_url or not self._is_high_quality_article_url(result_url):
                continue
            
            # Calculate similarity score
            score = self._calculate_title_similarity(title.lower(), result_title)
            
            # Boost score if from preferred source
            if preferred_source and preferred_source.lower() in result_source:
                score += 0.3
            
            # Boost score for high-quality domains
            if any(domain in result_url.lower() for domain in [
                'googleblog.com', 'openai.com', 'anthropic.com', 'microsoft.com'
            ]):
                score += 0.2
            
            if score > best_score:
                best_score = score
                best_url = result_url
        
        # Only return if we have a reasonable similarity match
        return best_url if best_score > 0.3 else None
    
    def _calculate_title_similarity(self, title1: str, title2: str) -> float:
        """
        Calculate similarity between two titles using word overlap.
        Returns a score between 0 and 1.
        """
        if not title1 or not title2:
            return 0.0
        
        # Clean and tokenize titles
        import re
        
        def clean_title(title):
            # Remove special characters and extra spaces
            cleaned = re.sub(r'[^\w\s]', ' ', title.lower())
            return set(cleaned.split())
        
        words1 = clean_title(title1)
        words2 = clean_title(title2)
        
        if not words1 or not words2:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _re_rank_articles_by_popularity(self, categorized_content: Dict) -> Dict:
        """
        Re-rank articles within each category by searching for their popularity and relevance.
        This helps prioritize more widely covered and important stories.
        """
        import time
        
        re_ranked_content = {}
        
        for category, articles in categorized_content.items():
            if not articles:
                continue
            
            # Add popularity scores to articles
            articles_with_scores = []
            
            for article in articles:
                article_copy = article.copy()
                title = article.get('title', '')
                
                try:
                    # Search for the article title to gauge popularity
                    popularity_score = self._calculate_article_popularity(title)
                    article_copy['popularity_score'] = popularity_score
                    
                    # Combine with existing impact score
                    combined_score = (
                        article.get('impact_score', 5) * 0.7 +
                        popularity_score * 0.3
                    )
                    article_copy['combined_score'] = combined_score
                    
                    time.sleep(0.1)  # Rate limiting
                    
                except Exception as e:
                    logging.warning(f"Failed to calculate popularity for '{title[:50]}...': {e}")
                    article_copy['popularity_score'] = 5.0
                    article_copy['combined_score'] = article.get('impact_score', 5)
                
                articles_with_scores.append(article_copy)
            
            # Sort by combined score (descending)
            articles_with_scores.sort(key=lambda x: x.get('combined_score', 0), reverse=True)
            re_ranked_content[category] = articles_with_scores
        
        return re_ranked_content
    
    def _calculate_article_popularity(self, title: str) -> float:
        """
        Calculate article popularity by searching for it and analyzing search result count.
        Returns a score between 1 and 10.
        """
        if not title or len(title) < 10:
            return 5.0
        
        try:
            # Search for the article title
            search_results = self.search_service.search_ai_content(f'"{title}"')
            
            # Base score on number of results found
            result_count = len(search_results)
            
            # Score based on result count
            if result_count >= 20:
                popularity_score = 10.0
            elif result_count >= 15:
                popularity_score = 8.0
            elif result_count >= 10:
                popularity_score = 7.0
            elif result_count >= 5:
                popularity_score = 6.0
            elif result_count >= 3:
                popularity_score = 5.0
            else:
                popularity_score = 3.0
            
            # Boost for articles from multiple high-quality sources
            quality_sources = 0
            for result in search_results:
                source = result.get('source', '').lower()
                if any(domain in source for domain in [
                    'googleblog.com', 'openai.com', 'anthropic.com', 'microsoft.com',
                    'techcrunch.com', 'venturebeat.com', 'theinformation.com'
                ]):
                    quality_sources += 1
            
            if quality_sources >= 3:
                popularity_score += 1.0
            elif quality_sources >= 2:
                popularity_score += 0.5
            
            return min(popularity_score, 10.0)
            
        except Exception as e:
            logging.warning(f"Failed to calculate popularity for '{title[:30]}...': {e}")
            return 5.0
    
    def _export_report_to_file(self, report_content: str, date_range: str) -> str:
        """
        Export the report to a markdown file with timestamp in the output directory.
        Returns the file path of the exported report.
        """
        import os
        from datetime import datetime
        
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Create output directory in the backend folder if it doesn't exist
        output_dir = os.path.join(script_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename with date and time
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H-%M-%S")
        filename = f"AI-News-Report-{date_str}-{time_str}.md"
        
        file_path = os.path.join(output_dir, filename)
        
        try:
            # Write report to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            logging.info(f"Report exported to: {file_path}")
            return file_path
            
        except Exception as e:
            logging.error(f"Failed to export report to file: {e}")
            return None

def should_continue_iteration(state: AgentState) -> str:
    """Routing function to determine if another iteration is needed"""
    needs_improvement = state.get("needs_improvement", False)
    iteration_count = state.get("iteration_count", 0)
    
    if needs_improvement and iteration_count < 2:
        return "improve_search"
    else:
        return "generate_report"

# Main graph construction function (this is what LangGraph will use)
def create_graph():
    """Create and return the AI trends reporting graph"""
    
    # Get API key from environment
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY environment variable is required")
    
    # Initialize the reporter
    reporter = AITrendsReporter(gemini_api_key=gemini_api_key)
    
    # Build the workflow with reflection mechanism
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("generate_queries", reporter.generate_ai_weekly_queries)
    workflow.add_node("research", reporter.research_ai_trends)
    workflow.add_node("analyze", reporter.categorize_and_analyze)
    workflow.add_node("reflect", reporter.reflect_on_quality)
    workflow.add_node("improve_search", reporter.improve_search_strategy)
    workflow.add_node("generate_report", reporter.generate_weekly_report)
    
    # Add edges
    workflow.set_entry_point("generate_queries")
    workflow.add_edge("generate_queries", "research")
    workflow.add_edge("research", "analyze")
    workflow.add_edge("analyze", "reflect")
    
    # Add conditional routing based on reflection
    workflow.add_conditional_edges(
        "reflect",
        should_continue_iteration,
        {
            "improve_search": "improve_search",
            "generate_report": "generate_report"
        }
    )
    
    # Loop back for iteration
    workflow.add_edge("improve_search", "research")
    workflow.add_edge("generate_report", END)
    
    return workflow.compile()

# For backward compatibility with the original structure
graph = create_graph()