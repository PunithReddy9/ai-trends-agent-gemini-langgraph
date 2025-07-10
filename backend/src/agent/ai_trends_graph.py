# backend/src/agent/ai_trends_graph.py
from typing import List, Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from datetime import datetime, timedelta
import json
import re

class AITrendsReporter:
    def __init__(self, gemini_api_key: str):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-002",
            api_key=gemini_api_key,
            temperature=0.1
        )
        
    def generate_ai_weekly_queries(self, state: Dict) -> Dict:
        """Generate AI-focused search queries for the past week"""
        current_date = datetime.now()
        week_ago = current_date - timedelta(days=7)
        
        prompt = f"""
        Generate 12 specific search queries to find AI trends and developments from the past week 
        ({week_ago.strftime('%B %d')} to {current_date.strftime('%B %d, %Y')}).
        
        Create queries covering these categories:
        1. AI Research Papers & Breakthroughs (2 queries)
        2. New AI Model Releases (LLMs, Vision, Audio) (2 queries)
        3. AI Company News & Announcements (2 queries)
        4. AI Tool & Framework Launches (2 queries)
        5. AI Funding & Investment News (2 queries)
        6. AI Policy & Regulatory Updates (2 queries)
        
        Requirements:
        - Include time constraints ("past week", "this week", "January 2025")
        - Be specific about AI domains
        - Focus on significant developments only
        - Use varied search terms
        
        Return as JSON array of strings.
        
        Example format:
        ["AI research papers arxiv past week January 2025", "new language model releases this week 2025"]
        """
        
        response = self.llm.invoke(prompt)
        try:
            queries = json.loads(response.content)
        except json.JSONDecodeError:
            # Fallback queries if JSON parsing fails
            queries = [
                "AI research breakthrough past week 2025",
                "new AI model release January 2025",
                "artificial intelligence startup funding this week",
                "OpenAI Google AI announcements past 7 days",
                "machine learning framework release 2025",
                "AI policy regulation news this week",
                "computer vision breakthrough January 2025",
                "large language model update past week",
                "AI tool launch announcement 2025",
                "deep learning research paper arxiv week"
            ]
        
        return {
            "search_queries": queries, 
            "search_results": [],
            "report_date_range": f"{week_ago.strftime('%B %d')} - {current_date.strftime('%B %d, %Y')}"
        }
    
    def research_ai_trends(self, state: Dict) -> Dict:
        """Execute searches focusing on high-quality AI sources"""
        # This would integrate with Google Search API
        # For now, showing the structure and priority sources
        
        priority_domains = [
            "arxiv.org",
            "ai.googleblog.com", 
            "openai.com/blog",
            "blog.anthropic.com",
            "research.microsoft.com",
            "ai.meta.com",
            "deepmind.google",
            "techcrunch.com",
            "venturebeat.com",
            "theinformation.com",
            "github.com",
            "huggingface.co"
        ]
        
        search_results = []
        for query in state["search_queries"]:
            # Placeholder for actual Google Search API implementation
            results = self._execute_search_with_filters(query, priority_domains)
            search_results.extend(results)
        
        # Remove duplicates and filter by date
        filtered_results = self._filter_and_deduplicate(search_results)
        
        return {"search_results": filtered_results}
    
    def categorize_and_analyze(self, state: Dict) -> Dict:
        """Analyze and categorize AI content with impact scoring"""
        prompt = f"""
        Analyze these AI-related articles and categorize them. Extract key information and score their significance.
        
        Content to analyze: {json.dumps(state["search_results"][:20], indent=2)}
        
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
        
        response = self.llm.invoke(prompt)
        try:
            categorized_content = json.loads(response.content)
        except json.JSONDecodeError:
            # Fallback structure if parsing fails
            categorized_content = {
                "BREAKTHROUGH_RESEARCH": [],
                "PRODUCT_LAUNCHES": [],
                "INDUSTRY_NEWS": [],
                "FUNDING_INVESTMENT": [],
                "REGULATORY_POLICY": [],
                "OPEN_SOURCE": [],
                "TRENDING_DISCUSSIONS": []
            }
        
        return {"categorized_content": categorized_content}
    
    def generate_weekly_report(self, state: Dict) -> Dict:
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
        - Include at least 15-20 distinct developments
        
        Return only the markdown report content.
        """
        
        response = self.llm.invoke(prompt)
        report_content = response.content
        
        # Generate additional metadata
        report_metadata = self._generate_report_metadata(categorized)
        
        return {
            "weekly_report": report_content,
            "report_metadata": report_metadata,
            "generation_timestamp": datetime.now().isoformat()
        }
    
    def _execute_search_with_filters(self, query: str, priority_domains: List[str]) -> List[Dict]:
        """Execute search with domain prioritization (placeholder for Google Search API)"""
        # This would implement actual Google Custom Search API calls
        # Return format: [{"title": str, "snippet": str, "url": str, "date": str, "source": str}]
        return []
    
    def _filter_and_deduplicate(self, results: List[Dict]) -> List[Dict]:
        """Filter results by date and remove duplicates"""
        week_ago = datetime.now() - timedelta(days=7)
        
        filtered = []
        seen_urls = set()
        
        for result in results:
            # Skip duplicates
            if result.get("url") in seen_urls:
                continue
                
            # Skip if too old (implement date parsing logic)
            # if self._is_too_old(result.get("date"), week_ago):
            #     continue
                
            seen_urls.add(result.get("url"))
            filtered.append(result)
        
        return filtered[:50]  # Limit to top 50 results
    
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
    
    def build_graph(self) -> StateGraph:
        """Build the AI trends reporting graph"""
        workflow = StateGraph(dict)
        
        # Add nodes
        workflow.add_node("generate_queries", self.generate_ai_weekly_queries)
        workflow.add_node("research", self.research_ai_trends)
        workflow.add_node("analyze", self.categorize_and_analyze)
        workflow.add_node("generate_report", self.generate_weekly_report)
        
        # Add edges
        workflow.set_entry_point("generate_queries")
        workflow.add_edge("generate_queries", "research")
        workflow.add_edge("research", "analyze")
        workflow.add_edge("analyze", "generate_report")
        workflow.add_edge("generate_report", END)
        
        return workflow.compile()

# Example usage function for the modified FastAPI backend
def create_ai_trends_endpoint():
    """
    Add this to your FastAPI backend to create the AI trends endpoint
    """
    from fastapi import APIRouter
    import os
    
    router = APIRouter()
    
    @router.post("/generate-weekly-report")
    async def generate_weekly_ai_report():
        """Generate AI trends report for the past week"""
        try:
            # Initialize the AI trends reporter
            reporter = AITrendsReporter(
                gemini_api_key=os.getenv("GEMINI_API_KEY")
            )
            
            # Build and run the graph
            graph = reporter.build_graph()
            result = graph.invoke({"input": "Generate weekly AI trends report"})
            
            return {
                "success": True,
                "report": result["weekly_report"],
                "metadata": result["report_metadata"],
                "generated_at": result["generation_timestamp"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    return router