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

class AITrendsReporter:
    def __init__(self, gemini_api_key: str):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            api_key=gemini_api_key,
            temperature=0.1
        )
        self.search_service = GoogleSearchService()
        
        # Priority AI sources for better content quality
        self.priority_ai_sources = [
            "arxiv.org",
            "ai.googleblog.com",
            "openai.com",
            "blog.anthropic.com",
            "research.microsoft.com",
            "ai.meta.com",
            "deepmind.google",
            "techcrunch.com",
            "venturebeat.com",
            "theinformation.com",
            "github.com",
            "huggingface.co",
            "papers.nips.cc",
            "icml.cc",
            "aaai.org"
        ]
    
    def generate_ai_weekly_queries(self, state: AgentState) -> AgentState:
        """Generate comprehensive AI search queries"""
        current_date = datetime.now()
        week_ago = current_date - timedelta(days=7)
        
        prompt = f"""
        Generate 12 diverse search queries to comprehensively cover AI developments from the past week 
        ({week_ago.strftime('%B %d')} to {current_date.strftime('%B %d, %Y')}).
        
        Create specific queries for these categories:
        
        1. Research & Breakthroughs (3 queries):
           - New AI research papers and studies
           - Scientific breakthroughs in machine learning
           - Academic conference announcements
        
        2. Product Launches (3 queries):
           - New AI model releases (LLMs, vision, audio)
           - AI tool and application launches
           - Software framework updates
        
        3. Industry News (3 queries):
           - AI company announcements and partnerships
           - Tech giant AI initiatives
           - Startup news and pivots
        
        4. Business & Investment (3 queries):
           - AI startup funding rounds
           - Acquisitions and mergers
           - Market analysis and valuations
        
        Requirements:
        - Include recent time indicators ("this week", "January 2025", "past 7 days")
        - Use varied terminology (AI, artificial intelligence, machine learning, deep learning)
        - Focus on significant developments, not minor updates
        - Target both technical and business audiences
        
        Return as JSON array of strings only.
        """
        
        try:
            response = self.llm.invoke(prompt)
            queries = json.loads(response.content)
        except (json.JSONDecodeError, Exception) as e:
            logging.warning(f"Failed to parse queries from LLM: {e}")
            # Comprehensive fallback queries
            queries = [
                "artificial intelligence research breakthrough January 2025",
                "new language model release this week 2025",
                "machine learning paper arxiv past week",
                "AI startup funding round announcement 2025",
                "OpenAI Google AI Microsoft announcement past 7 days",
                "deep learning framework update January 2025",
                "computer vision breakthrough research 2025",
                "AI regulation policy news this week",
                "artificial intelligence acquisition merger January",
                "LLM large language model release 2025",
                "AI tool application launch past week",
                "machine learning conference announcement 2025"
            ]
        
        state["search_queries"] = queries
        state["search_results"] = []
        state["report_date_range"] = f"{week_ago.strftime('%B %d')} - {current_date.strftime('%B %d, %Y')}"
        
        return state
    
    def research_ai_trends(self, state: AgentState) -> AgentState:
        """Execute comprehensive AI trends research"""
        all_results = []
        
        for query in state["search_queries"]:
            try:
                # Search with priority sites first
                priority_results = self.search_service.search_with_site_filters(
                    query, self.priority_ai_sources
                )
                all_results.extend(priority_results)
                
                # Add a small delay to respect rate limits
                import time
                time.sleep(0.5)
                
            except Exception as e:
                logging.error(f"Error searching for query '{query}': {e}")
                continue
        
        # Filter and rank results
        filtered_results = self._filter_and_rank_results(all_results)
        state["search_results"] = filtered_results
        
        return state
    
    def categorize_and_analyze(self, state: AgentState) -> AgentState:
        """Analyze and categorize AI content with impact scoring"""
        
        # Limit results for LLM processing
        results_sample = state["search_results"][:25] if len(state["search_results"]) > 25 else state["search_results"]
        
        prompt = f"""
        Analyze these AI-related articles and categorize them. Extract key information and score their significance.
        
        Content to analyze: {json.dumps(results_sample, indent=2)}
        
        Categorize into these sections:
        1. BREAKTHROUGH_RESEARCH: Major research papers, scientific discoveries
        2. PRODUCT_LAUNCHES: New AI models, tools, applications, features
        3. INDUSTRY_NEWS: Company announcements, partnerships, strategic moves
        4. FUNDING_INVESTMENT: Venture rounds, acquisitions, IPOs, valuations
        5. REGULATORY_POLICY: Government policies, AI governance, ethics discussions
        6. OPEN_SOURCE: New repositories, framework updates, community projects
        7. TRENDING_DISCUSSIONS: Viral AI content, popular debates, social trends
        
        For each item, extract:
        - title: Clear, descriptive title
        - summary: 2-3 sentence summary focusing on key points
        - source: Publication/website name
        - url: Original link
        - date: Publication date
        - impact_score: 1-10 (10 = game-changing, 1 = minor update)
        - relevance_tags: [array of relevant AI domains like "LLM", "Computer Vision", etc.]
        - business_impact: Brief note on practical/business implications
        
        Return as JSON with categories as keys and arrays of articles as values.
        Only include articles that are clearly AI-related and significant.
        """
        
        try:
            response = self.llm.invoke(prompt)
            categorized_content = json.loads(response.content)
        except (json.JSONDecodeError, Exception) as e:
            logging.warning(f"Failed to categorize content: {e}")
            # Fallback structure
            categorized_content = {
                "BREAKTHROUGH_RESEARCH": [],
                "PRODUCT_LAUNCHES": [],
                "INDUSTRY_NEWS": [],
                "FUNDING_INVESTMENT": [],
                "REGULATORY_POLICY": [],
                "OPEN_SOURCE": [],
                "TRENDING_DISCUSSIONS": []
            }
            
            # Try to create basic categorization from search results
            for result in results_sample[:10]:
                basic_item = {
                    "title": result.get("title", ""),
                    "summary": result.get("snippet", ""),
                    "source": result.get("source", ""),
                    "url": result.get("url", ""),
                    "date": result.get("date", ""),
                    "impact_score": 5,
                    "relevance_tags": ["AI"],
                    "business_impact": "Potential impact on AI industry"
                }
                categorized_content["INDUSTRY_NEWS"].append(basic_item)
        
        state["categorized_content"] = categorized_content
        return state
    
    def generate_weekly_report(self, state: AgentState) -> AgentState:
        """Generate comprehensive weekly AI trends report"""
        categorized = state["categorized_content"]
        date_range = state["report_date_range"]
        
        prompt = f"""
        Create a comprehensive AI Trends Weekly Report from this categorized content:
        
        Date Range: {date_range}
        Content: {json.dumps(categorized, indent=2)}
        
        Generate a professional report with this structure:
        
        # 🤖 AI Trends Weekly Report
        ## {date_range}
        
        ### 📊 Executive Summary
        [3-4 bullet points highlighting the most significant developments of the week]
        
        ### 🔬 Breakthrough Research
        [Cover 2-3 most impactful research developments with clear explanations]
        
        ### 🚀 Product Launches & Updates
        [New AI products, model releases, feature announcements]
        
        ### 🏢 Industry Developments
        [Company news, partnerships, strategic announcements]
        
        ### 💰 Funding & Investment Activity
        [Venture rounds, acquisitions, financial developments]
        
        ### ⚖️ Policy & Regulatory Updates
        [Government policies, regulatory changes, ethics discussions]
        
        ### 🔓 Open Source Highlights
        [Notable open source releases, community projects]
        
        ### 📈 What's Trending
        [Popular discussions, viral AI content, emerging debates]
        
        ### 🔮 Looking Ahead
        [Brief section on implications and what to watch next week]
        
        Guidelines:
        - Use markdown formatting for web display
        - Include source links in format [Source Name](URL)
        - Keep summaries concise but informative
        - Focus on business and technical implications
        - Highlight actionable insights
        - Use emojis sparingly for section headers only
        - Prioritize content by impact_score
        - Include at least 10-15 distinct developments
        - If a section has no content, mention "No major developments this week"
        
        Return only the markdown report content.
        """
        
        try:
            response = self.llm.invoke(prompt)
            report_content = response.content
        except Exception as e:
            logging.error(f"Failed to generate report: {e}")
            report_content = f"""
# 🤖 AI Trends Weekly Report
## {date_range}

### 📊 Executive Summary
- Report generation encountered technical issues
- Please check logs for more details
- Retry report generation

### Error Details
{str(e)}
"""
        
        # Generate additional metadata
        report_metadata = self._generate_report_metadata(categorized)
        
        state["weekly_report"] = report_content
        state["report_metadata"] = report_metadata
        state["generation_timestamp"] = datetime.now().isoformat()
        
        return state
    
    def _filter_and_rank_results(self, results: List[Dict]) -> List[Dict]:
        """Filter and rank results by relevance and quality"""
        # Remove results that are clearly not AI-related
        ai_keywords = [
            'artificial intelligence', 'machine learning', 'deep learning',
            'neural network', 'AI', 'LLM', 'GPT', 'transformer',
            'computer vision', 'natural language', 'robotics',
            'automation', 'algorithm', 'data science'
        ]
        
        filtered = []
        for result in results:
            text_content = f"{result.get('title', '')} {result.get('snippet', '')}".lower()
            
            # Check if content contains AI-related keywords
            if any(keyword in text_content for keyword in ai_keywords):
                # Add relevance score
                score = self._calculate_relevance_score(result, ai_keywords)
                result['relevance_score'] = score
                filtered.append(result)
        
        # Sort by relevance score and take top 40 results
        filtered.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        return filtered[:40]
    
    def _calculate_relevance_score(self, result: Dict, ai_keywords: List[str]) -> float:
        """Calculate relevance score for ranking"""
        score = 0.0
        text = f"{result.get('title', '')} {result.get('snippet', '')}".lower()
        
        # Keyword matching
        for keyword in ai_keywords:
            if keyword in text:
                score += 1.0
        
        # Source credibility boost
        source = result.get('source', '').lower()
        if any(priority in source for priority in ['arxiv', 'googleblog', 'openai', 'anthropic']):
            score += 3.0
        elif any(news in source for news in ['techcrunch', 'venturebeat', 'theinformation']):
            score += 2.0
        
        return score
    
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

# Main graph construction function (this is what LangGraph will use)
def create_graph():
    """Create and return the AI trends reporting graph"""
    
    # Get API key from environment
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY environment variable is required")
    
    # Initialize the reporter
    reporter = AITrendsReporter(gemini_api_key=gemini_api_key)
    
    # Build the workflow
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("generate_queries", reporter.generate_ai_weekly_queries)
    workflow.add_node("research", reporter.research_ai_trends)
    workflow.add_node("analyze", reporter.categorize_and_analyze)
    workflow.add_node("generate_report", reporter.generate_weekly_report)
    
    # Add edges
    workflow.set_entry_point("generate_queries")
    workflow.add_edge("generate_queries", "research")
    workflow.add_edge("research", "analyze")
    workflow.add_edge("analyze", "generate_report")
    workflow.add_edge("generate_report", END)
    
    return workflow.compile()

# For backward compatibility with the original structure
graph = create_graph()