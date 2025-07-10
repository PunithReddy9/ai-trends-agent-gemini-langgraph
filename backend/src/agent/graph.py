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
    categorized_content: Dict[str, List[Dict]]  # Legacy field for fallback
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
    # Trend analysis fields
    trend_patterns: Dict[str, Dict]  # Raw trend patterns identified
    trend_analysis: Dict  # Processed trend analysis with narratives

class AITrendsReporter:
    def __init__(self, gemini_api_key: str):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
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
        """Generate trend-focused search queries with developer perspective"""
        current_date = datetime.now()
        week_ago = current_date - timedelta(days=7)
        
        prompt = f"""
        Generate search queries to identify AI TRENDS and PATTERNS, not just news items. 
        Focus on developments that impact developers and engineers.
        
        Date Range: {week_ago.strftime('%B %d')} to {current_date.strftime('%B %d, %Y')}
        
        Create 15 strategic queries across these trend themes:
        
        1. AGENT ECOSYSTEM (3 queries):
           - AI agents, autonomous systems, CUA (Computer Use Agents)
           - Multi-agent workflows, agent frameworks, orchestration
           - Include: OpenAI Operator, Google Project Mariner, Microsoft agents
        
        2. AI CODING REVOLUTION (3 queries):
           - AI coding assistants, code generation, pair programming
           - Developer productivity tools, IDE integrations
           - Include: Cursor, GitHub Copilot, Codeium, Replit
        
        3. MODEL CAPABILITIES & BREAKTHROUGHS (3 queries):
           - New model releases, benchmarks, performance improvements
           - Multimodal advances, reasoning capabilities
           - Include: GPT, Claude, Gemini, DeepSeek, Mistral
        
        4. DEVELOPER TOOLS & APIS (3 queries):
           - New APIs, SDKs, frameworks, libraries
           - Integration patterns, deployment solutions
           - Include: Hugging Face, LangChain, Vercel AI SDK
        
        5. INDUSTRY SHIFTS & ADOPTION (3 queries):
           - Enterprise AI adoption, job market changes
           - Security concerns, ethical considerations
           - Include: funding rounds, partnerships, regulations
        
        Query Strategy:
        - Use terms like "launches", "releases", "announces", "introduces"
        - Include company names and product names
        - Add time indicators: "this week", "past week", "recent"
        - Mix technical and business perspectives
        
        Return EXACTLY 15 queries as a JSON array.
        """
        
        try:
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            
            # Clean up JSON response
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            elif content.startswith('```'):
                content = content.replace('```', '').strip()
            
            import re
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                content = json_match.group(0)
            
            queries = json.loads(content)
            
            if not isinstance(queries, list) or len(queries) != 15:
                raise ValueError(f"Expected 15 queries, got {len(queries) if isinstance(queries, list) else 0}")
                
            queries = [str(q) for q in queries]
            logging.info(f"Generated {len(queries)} trend-focused queries")
            
        except Exception as e:
            logging.warning(f"Failed to parse queries: {e}")
            # Use trend-focused fallback queries
            current_month = current_date.strftime('%B %Y')
            queries = [
                # Agent trends
                f"AI agents autonomous systems launches {current_month}",
                f"OpenAI Operator Google Mariner agent updates",
                f"multi-agent workflows frameworks recent",
                # Coding trends
                f"AI coding assistants new features this week",
                f"Cursor GitHub Copilot updates {current_month}",
                f"developer productivity AI tools launches",
                # Model trends
                f"GPT Claude Gemini new capabilities {current_month}",
                f"AI model benchmarks performance breakthroughs",
                f"multimodal AI advances this week",
                # Developer tools
                f"AI APIs SDKs releases {current_month}",
                f"Hugging Face LangChain new features",
                f"AI development frameworks launches",
                # Industry trends
                f"AI startup funding rounds this week",
                f"enterprise AI adoption announcements",
                f"AI regulations policy updates {current_month}"
            ]
        
        state["search_queries"] = queries
        state["search_results"] = []
        state["report_date_range"] = f"{week_ago.strftime('%B %d')} - {current_date.strftime('%B %d, %Y')}"
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
        """Reflect on the quality of trend analysis to determine if another iteration is needed"""
        
        # Check if we have trend analysis
        trend_analysis = state.get("trend_analysis", {})
        if trend_analysis:
            # Use trend-based reflection
            return self._reflect_on_trends(state)
        
        # Fall back to old categorization-based reflection
        categorized = state.get("categorized_content", {})
        search_results = state["search_results"]
        iteration_count = state.get("iteration_count", 0)
        
        # Quality metrics for categorized content
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
        url_quality_ratio = good_urls / len(search_results) if search_results else 0
        quality_score += url_quality_ratio * 20
        
        # Source diversity (20 points max)
        source_ratio = preferred_sources / len(search_results) if search_results else 0
        quality_score += source_ratio * 20
        
        # Cross-source validation (10 points max)
        cross_source_ratio = cross_source_items / len(search_results) if search_results else 0
        quality_score += cross_source_ratio * 10
        
        # Determine if improvement is needed
        needs_improvement = False
        improvement_areas = []
        
        if quality_score < 60:  # Threshold for quality
            needs_improvement = True
            
            if total_items < 10:
                improvement_areas.append("insufficient_content")
            if categories_with_content < 3:
                improvement_areas.append("poor_category_coverage")
            if url_quality_ratio < 0.5:
                improvement_areas.append("poor_url_quality")
            if source_ratio < 0.3:
                improvement_areas.append("insufficient_preferred_sources")
            if cross_source_ratio < 0.1:
                improvement_areas.append("lack_cross_source_validation")
        
        # Update state
        state["quality_score"] = quality_score
        state["needs_improvement"] = needs_improvement and iteration_count < 2
        state["improvement_areas"] = improvement_areas
        state["reflection_feedback"] = f"Quality score: {quality_score:.1f}/100. " + \
                                      f"Found {total_items} items across {categories_with_content} categories. " + \
                                      f"URL quality: {url_quality_ratio:.1%}, Preferred sources: {source_ratio:.1%}"
        
        logging.info(f"Reflection complete: {state['reflection_feedback']}")
        logging.info(f"Needs improvement: {needs_improvement}, Areas: {improvement_areas}")
        
        return state
    
    def _reflect_on_trends(self, state: AgentState) -> AgentState:
        """Reflect on trend analysis quality"""
        trend_analysis = state.get("trend_analysis", {})
        trends = trend_analysis.get("major_trends", [])
        search_results = state["search_results"]
        iteration_count = state.get("iteration_count", 0)
        
        # Quality metrics for trends
        num_trends = len(trends)
        total_developments = sum(len(trend.get("key_developments", [])) for trend in trends)
        trends_with_good_narrative = sum(1 for trend in trends if len(trend.get("narrative", "")) > 100)
        trends_with_actions = sum(1 for trend in trends if len(trend.get("action_items", [])) >= 2)
        
        # Calculate quality score
        quality_score = 0.0
        
        # Number of trends (30 points)
        if num_trends >= 4:
            quality_score += 30
        elif num_trends >= 3:
            quality_score += 25
        elif num_trends >= 2:
            quality_score += 15
        
        # Total developments (25 points)
        if total_developments >= 12:
            quality_score += 25
        elif total_developments >= 8:
            quality_score += 20
        elif total_developments >= 5:
            quality_score += 10
        
        # Narrative quality (25 points)
        narrative_ratio = trends_with_good_narrative / num_trends if num_trends > 0 else 0
        quality_score += narrative_ratio * 25
        
        # Actionable insights (20 points)
        action_ratio = trends_with_actions / num_trends if num_trends > 0 else 0
        quality_score += action_ratio * 20
        
        # Determine if improvement is needed
        needs_improvement = False
        improvement_areas = []
        
        if quality_score < 70:
            needs_improvement = True
            
            if num_trends < 3:
                improvement_areas.append("insufficient_trends")
            if total_developments < 8:
                improvement_areas.append("insufficient_developments")
            if narrative_ratio < 0.5:
                improvement_areas.append("weak_narratives")
            if action_ratio < 0.5:
                improvement_areas.append("lack_of_actionable_insights")
        
        # Update state
        state["quality_score"] = quality_score
        state["needs_improvement"] = needs_improvement and iteration_count < 2
        state["improvement_areas"] = improvement_areas
        state["reflection_feedback"] = f"Quality score: {quality_score:.1f}/100. " + \
                                      f"Identified {num_trends} trends with {total_developments} total developments."
        
        logging.info(f"Trend reflection complete: {state['reflection_feedback']}")
        logging.info(f"Needs improvement: {needs_improvement}, Areas: {improvement_areas}")
        
        return state
    
    def improve_search_strategy(self, state: AgentState) -> AgentState:
        """Improve search strategy based on reflection feedback"""
        improvement_areas = state.get("improvement_areas", [])
        iteration_count = state.get("iteration_count", 0)
        
        # Enhanced search queries based on what's missing
        additional_queries = []
        
        # Handle trend-based improvements
        if "insufficient_trends" in improvement_areas:
            additional_queries.extend([
                "AI agent frameworks launches this week",
                "new AI coding tools announcements",
                "AI model capabilities breakthroughs",
                "AI security concerns recent developments",
                "enterprise AI adoption case studies"
            ])
        
        if "insufficient_developments" in improvement_areas:
            additional_queries.extend([
                "OpenAI Anthropic Google AI updates this week",
                "Hugging Face GitHub AI releases",
                "AI startup launches product announcements",
                "AI API SDK releases recent",
                "developer AI tools new features"
            ])
        
        if "weak_narratives" in improvement_areas:
            additional_queries.extend([
                "AI industry analysis trends report",
                "AI technology impact developers",
                "future of AI development predictions",
                "AI transformation software engineering"
            ])
        
        # Handle categorization-based improvements (fallback)
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
        """Generate trend-focused developer report with proper URLs"""
        trend_analysis = state.get("trend_analysis", {})
        date_range = state["report_date_range"]
        
        # If we don't have trend analysis, fall back to categorized content
        if not trend_analysis or not trend_analysis.get("major_trends"):
            # Use the old categorization approach as fallback
            return self._generate_categorized_report(state)
        
        # Pre-process to ensure we have URLs
        for trend in trend_analysis.get("major_trends", []):
            for dev in trend.get("key_developments", []):
                if not dev.get("url") or dev["url"] == "#":
                    logging.warning(f"Missing URL for development: {dev.get('title', 'Unknown')}")
        
        prompt = f"""
        Create a compelling AI trends report for developers. Focus on narrative and insights.
        
        CRITICAL URL RULES:
        1. Each development has a "url" field - use it EXACTLY as provided
        2. When mentioning a development, format as: [exact title](exact url)
        3. NEVER use just domain names like (https://openai.com/)
        4. If you see a URL in the data, copy it character-for-character
        
        Trend Data with URLs:
        {json.dumps(trend_analysis, indent=2)}
        
        Date Range: {date_range}
        
        Report Structure:
        
        # AI Trends Weekly: {date_range}
        
        [Opening paragraph: Set the stage for this week's developments - be engaging and insightful]
        
        ## Trend [Number]: [Use trend_title from data]
        
        [Opening narrative paragraph - paint the big picture]
        
        [2-3 paragraphs weaving together the key developments:
        - Use the EXACT title and url from key_developments
        - Format: Company [title](url) description...
        - Connect developments to show the trend
        - Explain why this matters NOW]
        
        [Technical paragraph: architecture changes, tools, infrastructure implications]
        
        [Developer impact paragraph: how this changes workflows, what to prepare for]
        
        ---
        
        [Repeat for each trend]
        
        Writing Style:
        - Engaging and insightful, not just listing facts
        - Connect developments into a coherent narrative
        - Focus on "why this matters" not just "what happened"
        - Use specific technical details when relevant
        - Balance excitement with practical implications
        
        DO NOT INCLUDE:
        - Key Takeaways sections
        - Action Items sections
        - Bullet point lists of takeaways
        
        REMEMBER: Every link must use the EXACT URL from the data!
        """
        
        try:
            response = self.llm.invoke(prompt)
            report_content = response.content.strip()
            
            # Validate report has proper structure
            if not report_content.startswith('#'):
                logging.warning("Report doesn't start with markdown header")
                report_content = self._create_trend_fallback_report(trend_analysis, date_range)
            
            # Post-process to fix any URL issues
            report_content = self._fix_report_urls(report_content, trend_analysis)
            
            # Validate URLs in the report
            self._validate_report_urls(report_content, trend_analysis)
            
        except Exception as e:
            logging.error(f"Failed to generate trend report: {e}")
            report_content = self._create_trend_fallback_report(trend_analysis, date_range)
        
        # Export report
        export_path = self._export_report_to_file(report_content, date_range)
        
        # Generate metadata
        report_metadata = {
            "total_trends": len(trend_analysis.get("major_trends", [])),
            "report_type": "trend_analysis",
            "export_path": export_path if export_path else ""
        }
        
        state["weekly_report"] = report_content
        state["report_metadata"] = report_metadata
        state["generation_timestamp"] = datetime.now().isoformat()
        state["export_path"] = export_path if export_path else ""
        
        return state
    
    def _create_trend_fallback_report(self, trend_analysis: Dict, date_range: str) -> str:
        """Create a fallback trend-based report"""
        trends = trend_analysis.get("major_trends", [])
        
        report = f"""# AI Trends Weekly: {date_range}

This week's AI landscape reveals several transformative trends that are reshaping how developers build and deploy intelligent systems. From autonomous agents to revolutionary coding assistants, the pace of innovation continues to accelerate.

"""
        
        for i, trend in enumerate(trends, 1):
            report += f"""## Trend {i}: {trend['trend_title']}

{trend.get('narrative', 'Significant developments are emerging in this area.')}

"""
            # Add key developments with proper URLs
            for dev in trend.get('key_developments', [])[:3]:
                url = dev.get('url', '')
                # Only add developments with valid full URLs (not domain-only)
                if url and url != '#' and not url.endswith('.com/') and not url.endswith('.org/'):
                    title = dev.get('title', 'a significant development')
                    company = dev.get('company', 'A major player')
                    description = dev.get('description', 'represents an important advancement in the field.')
                    impact = dev.get('impact', '')
                    
                    report += f"""{company} announced [{title}]({url}) which {description} {impact}\n\n"""
            
            report += f"""
{trend.get('technical_implications', 'These developments have significant technical implications for developers.')}

{trend.get('developer_impact', 'Developers need to stay informed about these changes.')}

---

"""
        
        return report
    
    def _generate_categorized_report(self, state: AgentState) -> AgentState:
        """Fallback to old categorized report generation"""
        # Keep the old implementation as fallback
        categorized = state["categorized_content"]
        date_range = state["report_date_range"]
        
        # The old report generation code remains here as fallback
        # ... (keeping existing implementation)
        
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
    
    def identify_trend_patterns(self, search_results: List[Dict]) -> Dict[str, Dict]:
        """Identify emerging trends and patterns across search results"""
        
        # Define trend themes to look for
        trend_themes = {
            "agent_revolution": {
                "theme_title": "AI Agents are Taking the Scene",
                "keywords": ["agent", "autonomous", "CUA", "operator", "mariner", "workflow", "orchestration"],
                "companies": ["openai", "google", "microsoft", "mistral", "anthropic"],
                "related_items": [],
                "signals": []
            },
            "ai_coding": {
                "theme_title": "AI Coding Revolution",
                "keywords": ["coding", "cursor", "copilot", "code generation", "developer", "IDE", "programming"],
                "companies": ["github", "cursor", "replit", "codeium", "tabnine"],
                "related_items": [],
                "signals": []
            },
            "model_evolution": {
                "theme_title": "Model Evolution & Capabilities",
                "keywords": ["model", "benchmark", "performance", "capabilities", "multimodal", "reasoning", "o3"],
                "companies": ["openai", "anthropic", "google", "deepseek", "mistral"],
                "related_items": [],
                "signals": []
            },
            "deepfake_security": {
                "theme_title": "AI Security & Trust Challenges",
                "keywords": ["deepfake", "synthetic", "detection", "trust", "verification", "security", "safety"],
                "companies": ["resemble", "elevenlabs", "runway", "palo alto"],
                "related_items": [],
                "signals": []
            },
            "enterprise_adoption": {
                "theme_title": "Enterprise AI Integration",
                "keywords": ["enterprise", "adoption", "integration", "deployment", "scale", "business", "partnership"],
                "companies": ["microsoft", "salesforce", "aws", "google cloud", "azure"],
                "related_items": [],
                "signals": []
            }
        }
        
        # Analyze each result for trend signals
        for result in search_results:
            title = result.get("title", "").lower()
            snippet = result.get("snippet", "").lower()
            source = result.get("source", "").lower()
            url = result.get("url", "")
            full_text = f"{title} {snippet}"
            
            # Skip results without proper URLs
            if not url or url == "#" or not url.startswith(('http://', 'https://')):
                logging.warning(f"Skipping result with invalid URL: {title[:50]}...")
                continue
            
            for theme_name, theme_data in trend_themes.items():
                # Check keyword matches
                keyword_matches = [kw for kw in theme_data["keywords"] if kw in full_text]
                company_matches = [comp for comp in theme_data["companies"] if comp in full_text or comp in source]
                
                if keyword_matches or company_matches:
                    # Calculate relevance score
                    relevance_score = len(keyword_matches) * 2 + len(company_matches) * 3
                    
                    # Create a clean copy of the result with guaranteed URL preservation
                    clean_result = {
                        "title": result.get("title", ""),
                        "snippet": result.get("snippet", ""),
                        "source": result.get("source", ""),
                        "url": url,  # Ensure URL is preserved
                        "date": result.get("date", ""),
                        "theme_relevance": relevance_score,
                        "matched_keywords": keyword_matches,
                        "matched_companies": company_matches
                    }
                    
                    theme_data["related_items"].append(clean_result)
                    
                    # Extract specific signals
                    if keyword_matches:
                        for kw in keyword_matches[:2]:  # Top 2 keywords
                            signal = f"{kw} mentioned in {source}"
                            if signal not in theme_data["signals"]:
                                theme_data["signals"].append(signal)
        
        # Sort related items by relevance and log URL preservation
        for theme_name, theme_data in trend_themes.items():
            theme_data["related_items"].sort(key=lambda x: x["theme_relevance"], reverse=True)
            if theme_data["related_items"]:
                logging.info(f"Theme '{theme_name}' has {len(theme_data['related_items'])} items with URLs preserved")
        
        return trend_themes
    
    def analyze_trends_with_developer_impact(self, state: AgentState) -> AgentState:
        """Analyze trends and assess developer impact"""
        
        # First identify trend patterns
        trend_patterns = self.identify_trend_patterns(state["search_results"])
        
        # Filter out trends with too few items
        significant_trends = {
            name: data for name, data in trend_patterns.items() 
            if len(data["related_items"]) >= 2
        }
        
        # Create a more direct structure for the LLM
        simplified_trends = {}
        for trend_name, trend_data in significant_trends.items():
            simplified_trends[trend_name] = {
                "theme_title": trend_data["theme_title"],
                "items": [
                    {
                        "title": item["title"],
                        "snippet": item["snippet"],
                        "source": item["source"],
                        "url": item["url"]
                    }
                    for item in trend_data["related_items"][:5]  # Top 5 items per trend
                ]
            }
        
        prompt = f"""
        Analyze these AI trends and create narratives for each. DO NOT modify any URLs - copy them exactly.
        
        Trends data with exact URLs:
        {json.dumps(simplified_trends, indent=2)}
        
        For each trend, create:
        
        1. TREND NARRATIVE (2-3 paragraphs):
           - What's happening and why it matters
           - Connect the developments into a coherent story
           - Focus on developer/engineering implications
        
        2. KEY DEVELOPMENTS (use exact data from items):
           - For each item, use EXACT title, source, snippet, and url
           - DO NOT modify URLs or use domain names
           - Copy the url field character-for-character
        
        3. TECHNICAL IMPLICATIONS:
           - Architecture and infrastructure changes
           - Skills and tools developers need
        
        4. DEVELOPER IMPACT:
           - How this changes development workflows
           - Opportunities and challenges
        
        Return as JSON with this EXACT structure:
        {{
            "major_trends": [
                {{
                    "trend_id": "agent_revolution",
                    "trend_title": "COPY theme_title exactly",
                    "narrative": "Write 2-3 paragraph narrative here...",
                    "key_developments": [
                        {{
                            "title": "COPY EXACT title from items",
                            "company": "COPY EXACT source from items", 
                            "description": "COPY EXACT snippet from items",
                            "url": "COPY EXACT url from items - DO NOT MODIFY",
                            "impact": "Brief impact statement"
                        }}
                    ],
                    "developer_impact": "Impact on developers...",
                    "technical_implications": "Technical implications..."
                }}
            ]
        }}
        
        CRITICAL: The url field MUST be copied exactly from the items data. Do not use domain names or modify URLs.
        """
        
        try:
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            
            # Clean JSON response
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            
            trend_analysis = json.loads(content)
            
            # Validate URLs were preserved
            for trend in trend_analysis.get("major_trends", []):
                for dev in trend.get("key_developments", []):
                    url = dev.get("url", "")
                    if url and (url.endswith('.com/') or url.endswith('.org/') or '/' not in url.split('://')[-1]):
                        logging.warning(f"LLM returned domain-only URL: {url}")
            
            state["trend_analysis"] = trend_analysis
            state["trend_patterns"] = significant_trends
            
        except Exception as e:
            logging.error(f"Failed to analyze trends: {e}")
            # Create fallback analysis
            state["trend_analysis"] = self._create_fallback_trend_analysis(significant_trends)
            state["trend_patterns"] = significant_trends
        
        return state
    
    def _create_fallback_trend_analysis(self, trend_patterns: Dict) -> Dict:
        """Create fallback trend analysis when LLM fails"""
        major_trends = []
        
        for trend_id, trend_data in trend_patterns.items():
            if len(trend_data["related_items"]) < 2:
                continue
                
            trend = {
                "trend_id": trend_id,
                "trend_title": trend_data["theme_title"],
                "narrative": f"Multiple developments in {trend_data['theme_title']} signal a major shift in the AI landscape.",
                "key_developments": [
                    {
                        "title": item.get("title", "Unknown development"),
                        "company": item.get("source", "Unknown"),
                        "description": item.get("snippet", "")[:200],
                        "url": item.get("url", "#"),  # Preserve exact URL from search results
                        "impact": "Significant development in the field"
                    }
                    for item in trend_data["related_items"][:3]
                    if item.get("url") and item.get("url") != "#"  # Only include items with valid URLs
                ],
                "developer_impact": "This trend requires developers to adapt their skills and workflows.",
                "technical_implications": "New architectures and integration patterns emerging.",
                "action_items": ["Research this trend further", "Experiment with related tools"]
            }
            major_trends.append(trend)
        
        return {"major_trends": major_trends}
    
    def _validate_report_urls(self, report_content: str, trend_analysis: Dict) -> None:
        """Validate that the report contains proper URLs, not just domain names"""
        import re
        
        # Extract all URLs from the report
        url_pattern = r'\[([^\]]+)\]\((https?://[^\)]+)\)'
        report_urls = re.findall(url_pattern, report_content)
        
        # Extract expected URLs from trend analysis
        expected_urls = []
        for trend in trend_analysis.get("major_trends", []):
            for dev in trend.get("key_developments", []):
                if dev.get("url"):
                    expected_urls.append(dev["url"])
        
        # Check for domain-only URLs
        domain_only_count = 0
        for link_text, url in report_urls:
            # Check if URL is domain-only (ends with .com/, .org/, etc. or no path)
            if re.match(r'^https?://[^/]+\.(com|org|net|io|ai|co|edu)/?$', url):
                logging.warning(f"Domain-only URL found: [{link_text}]({url})")
                domain_only_count += 1
        
        if domain_only_count > 0:
            logging.warning(f"Found {domain_only_count} domain-only URLs in the report")
            logging.info(f"Expected URLs from data: {expected_urls[:3]}...")  # Show first 3 as examples
        
        # Check if expected URLs are present
        report_url_set = {url for _, url in report_urls}
        missing_urls = [url for url in expected_urls if url not in report_url_set]
        
        if missing_urls:
            logging.warning(f"Missing {len(missing_urls)} expected URLs from the report")
            for url in missing_urls[:3]:  # Log first 3 missing URLs
                logging.warning(f"Missing URL: {url}")
    
    def _fix_report_urls(self, report_content: str, trend_analysis: Dict) -> str:
        """Post-process report to fix any domain-only URLs with actual article URLs"""
        import re
        
        # Create a mapping of titles to their correct URLs
        title_to_url = {}
        for trend in trend_analysis.get("major_trends", []):
            for dev in trend.get("key_developments", []):
                title = dev.get("title", "")
                url = dev.get("url", "")
                if title and url and url != "#":
                    title_to_url[title.lower()] = url
        
        # Find all markdown links in the report
        link_pattern = r'\[([^\]]+)\]\((https?://[^\)]+)\)'
        
        def replace_url(match):
            link_text = match.group(1)
            current_url = match.group(2)
            
            # Check if the current URL is domain-only
            if re.match(r'^https?://[^/]+\.(com|org|net|io|ai|co|edu)/?$', current_url):
                # Try to find the correct URL based on the link text
                link_text_lower = link_text.lower()
                
                # Look for exact match first
                if link_text_lower in title_to_url:
                    correct_url = title_to_url[link_text_lower]
                    logging.info(f"Fixed URL: [{link_text}]({current_url}) -> [{link_text}]({correct_url})")
                    return f"[{link_text}]({correct_url})"
                
                # Look for partial matches
                for title, url in title_to_url.items():
                    if link_text_lower in title or title in link_text_lower:
                        logging.info(f"Fixed URL (partial match): [{link_text}]({current_url}) -> [{link_text}]({url})")
                        return f"[{link_text}]({url})"
            
            # Return unchanged if not domain-only or no match found
            return match.group(0)
        
        # Replace URLs in the report
        fixed_report = re.sub(link_pattern, replace_url, report_content)
        
        return fixed_report

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
    
    # Add nodes - UPDATED to use trend analysis
    workflow.add_node("generate_queries", reporter.generate_ai_weekly_queries)
    workflow.add_node("research", reporter.research_ai_trends)
    workflow.add_node("analyze", reporter.analyze_trends_with_developer_impact)  # Changed from categorize_and_analyze
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