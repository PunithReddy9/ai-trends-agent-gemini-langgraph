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
            model="gemini-2.5-flash",
            api_key=gemini_api_key,
            temperature=0.1
        )
        self.search_service = GoogleSearchService()
        
        # Balanced AI sources - technical advancement and industry
        self.diverse_ai_sources = [
            # Technical/Research Sources (Higher Priority)
            "ai.googleblog.com",
            "openai.com",
            "blog.anthropic.com",
            "research.microsoft.com",
            "ai.meta.com",
            "deepmind.google",
            "huggingface.co",
            "github.com",
            "arxiv.org",
            "papers.nips.cc",
            # Industry News Sources
            "techcrunch.com",
            "venturebeat.com", 
            "theinformation.com",
            "technologyreview.mit.edu",
            "spectrum.ieee.org"
        ]
    
    def generate_ai_weekly_queries(self, state: AgentState) -> AgentState:
        """Generate comprehensive AI search queries"""
        current_date = datetime.now()
        week_ago = current_date - timedelta(days=7)
        
        prompt = f"""
        Generate 8 diverse search queries to comprehensively cover AI developments from the past week 
        ({week_ago.strftime('%B %d')} to {current_date.strftime('%B %d, %Y')}).
        
        Create specific queries for these categories:
        
        1. AI Technical Advancements & Features (3 queries):
           - New AI model releases and capabilities (GPT, Claude, Gemini updates)
           - AI feature announcements and technical improvements
           - Research breakthroughs in machine learning and AI
        
        2. Company AI Research & Development (2 queries):
           - Anthropic, OpenAI, Google AI research projects
           - Technical blog posts and research publications
        
        3. AI Tools & Framework Development (2 queries):
           - New AI development tools and SDKs
           - Open source AI framework releases and updates
        
        4. Business & Industry Applications (1 query):
           - AI implementation in specific industries
        
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
            # Balanced queries focusing on technical advancements AND business
            queries = [
                "OpenAI GPT new features release January 2025",
                "Anthropic Claude AI capabilities update this week",
                "Google Gemini model improvements announcement 2025",
                "new AI research breakthrough machine learning past week",
                "AI framework release open source January 2025",
                "AI tool developer announcement new features 2025",
                "Meta AI LLaMA research update January 2025",
                "AI startup funding technical development news"
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
                # Use diverse source search instead of priority sites
                diverse_results = self.search_service.search_with_diverse_sources(query)
                all_results.extend(diverse_results)
                
                # Add a small delay to respect rate limits
                import time
                time.sleep(1.0)  # Increased delay for API stability
                
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
        1. AI_TECHNICAL_ADVANCES: New AI model features, capabilities, technical improvements
        2. RESEARCH_BREAKTHROUGHS: Scientific discoveries, algorithm innovations, research papers
        3. PRODUCT_LAUNCHES: New AI products, tools, applications, features
        4. COMPANY_RESEARCH: AI labs research projects, technical blog posts, R&D announcements
        5. OPEN_SOURCE: Framework releases, library updates, community projects
        6. INDUSTRY_NEWS: Business developments, partnerships, strategic moves
        7. FUNDING_INVESTMENT: Venture rounds, acquisitions, financial developments
        
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
            
            # Ensure we have proper structure and filter empty categories
            cleaned_content = {}
            for category, items in categorized_content.items():
                if isinstance(items, list) and len(items) > 0:
                    # Ensure each item has required fields
                    valid_items = []
                    for item in items:
                        if isinstance(item, dict) and item.get('title') and item.get('summary'):
                            valid_items.append(item)
                    
                    if valid_items:
                        cleaned_content[category] = valid_items
            
            categorized_content = cleaned_content
            
        except (json.JSONDecodeError, Exception) as e:
            logging.warning(f"Failed to categorize content: {e}")
            # Create better fallback categorization from search results
            categorized_content = self._create_fallback_categorization(results_sample)
        
        state["categorized_content"] = categorized_content
        return state
    
    def _create_fallback_categorization(self, results_sample: List[Dict]) -> Dict:
        """Create fallback categorization when LLM fails"""
        categorized_content = {
            "AI_TECHNICAL_ADVANCES": [],
            "RESEARCH_BREAKTHROUGHS": [],
            "PRODUCT_LAUNCHES": [],
            "COMPANY_RESEARCH": [],
            "OPEN_SOURCE": [],
            "INDUSTRY_NEWS": []
        }
        
        # Simple keyword-based categorization
        for result in results_sample[:15]:
            title = result.get("title", "").lower()
            source = result.get("source", "").lower()
            
            item = {
                "title": result.get("title", ""),
                "summary": result.get("snippet", "")[:200] + "..." if result.get("snippet") else "",
                "source": result.get("source", ""),
                "url": result.get("url", ""),
                "date": result.get("date", ""),
                "impact_score": 5,
                "relevance_tags": ["AI"],
                "business_impact": "Potential impact on AI industry"
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
            else:
                categorized_content["INDUSTRY_NEWS"].append(item)
        
        # Remove empty categories
        return {k: v for k, v in categorized_content.items() if v}
        
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
        
        Generate a professional report with this EXACT structure, but ONLY INCLUDE SECTIONS THAT HAVE CONTENT:
        
        # 🤖 AI Trends Weekly Report
        ## {date_range}
        
        ### 📊 Executive Summary
        
        [Write 3-4 bullet points highlighting the most significant AI developments of the week - ALWAYS INCLUDE THIS SECTION]
        
        ### 🚀 AI Technical Advances & New Features
        
        [Cover latest AI model updates, feature releases, technical improvements - ONLY INCLUDE IF AI_TECHNICAL_ADVANCES has content]
        
        ### 🔬 Research Breakthroughs & Innovations
        
        [Cover scientific discoveries, algorithm innovations, research papers - ONLY INCLUDE IF RESEARCH_BREAKTHROUGHS has content]
        
        ### 🛠️ New AI Tools & Products
        
        [Cover product launches, tool releases, platform updates - ONLY INCLUDE IF PRODUCT_LAUNCHES has content]
        
        ### 🏭 Company Research & Development
        
        [Cover AI labs projects, technical blog posts, R&D announcements - ONLY INCLUDE IF COMPANY_RESEARCH has content]
        
        ### 🔓 Open Source Highlights
        
        [Cover framework releases, library updates, community projects - ONLY INCLUDE IF OPEN_SOURCE has content]
        
        ### 🏢 Industry Developments
        
        [Cover business news, partnerships, strategic moves - ONLY INCLUDE IF INDUSTRY_NEWS has content]
        
        ### 💰 Funding & Investment Activity
        
        [Cover venture rounds, acquisitions, financial developments - ONLY INCLUDE IF FUNDING_INVESTMENT has content]
        
        ### 🔮 Looking Ahead
        
        [Brief section on implications and what to watch next week - ALWAYS INCLUDE THIS SECTION]
        
        CRITICAL FORMATTING REQUIREMENTS:
        - Use proper markdown headers (### for sections)
        - Use bullet points (- or *) for lists within sections
        - Include source links in format [Source Name](URL) 
        - Each section should have 2-4 substantial bullet points
        - DO NOT include section headers for empty categories
        - If a category has no content, completely skip that section
        - Keep content concise but informative
        - Focus on technical details and business implications
        - Ensure proper spacing between sections
        - Use clean, readable markdown formatting
        
        Return ONLY the markdown report content with proper formatting.
        """
        
        try:
            response = self.llm.invoke(prompt)
            report_content = response.content
            
            # Validate that we have proper markdown structure
            if not report_content.strip().startswith('#'):
                logging.warning("Generated report doesn't start with proper markdown header")
                report_content = self._create_fallback_report(categorized, date_range)
                
        except Exception as e:
            logging.error(f"Failed to generate report: {e}")
            report_content = self._create_fallback_report(categorized, date_range)
        
        # Generate additional metadata
        report_metadata = self._generate_report_metadata(categorized)
        
        state["weekly_report"] = report_content
        state["report_metadata"] = report_metadata
        state["generation_timestamp"] = datetime.now().isoformat()
        
        return state
    
    def _create_fallback_report(self, categorized: Dict, date_range: str) -> str:
        """Create a fallback report when LLM generation fails"""
        report = f"""# 🤖 AI Trends Weekly Report
## {date_range}

### 📊 Executive Summary

* This week saw continued activity in AI development across multiple sectors
* Several companies announced new AI capabilities and research initiatives  
* Open source AI tools and frameworks continued to evolve
* The AI landscape remains dynamic with both technical and business developments

"""
        
        # Add sections based on available content
        section_map = {
            "AI_TECHNICAL_ADVANCES": "### 🚀 AI Technical Advances & New Features\n\n",
            "RESEARCH_BREAKTHROUGHS": "### 🔬 Research Breakthroughs & Innovations\n\n", 
            "PRODUCT_LAUNCHES": "### 🛠️ New AI Tools & Products\n\n",
            "COMPANY_RESEARCH": "### 🏭 Company Research & Development\n\n",
            "OPEN_SOURCE": "### 🔓 Open Source Highlights\n\n",
            "INDUSTRY_NEWS": "### 🏢 Industry Developments\n\n"
        }
        
        for category, items in categorized.items():
            if category in section_map and items:
                report += section_map[category]
                for item in items[:3]:  # Limit to 3 items per section
                    title = item.get('title', 'AI Development')
                    summary = item.get('summary', 'New development in AI sector')
                    source = item.get('source', 'Unknown')
                    url = item.get('url', '#')
                    
                    report += f"* **{title[:100]}**: {summary[:200]}... [Source: {source}]({url})\n\n"
        
        report += """### 🔮 Looking Ahead

* Expect continued developments in AI model capabilities and applications
* Watch for new research publications and technical breakthroughs  
* Monitor industry partnerships and strategic AI initiatives
* Keep an eye on regulatory discussions and AI governance developments
"""
        
        return report
    
    def _filter_and_rank_results(self, results: List[Dict]) -> List[Dict]:
        """Filter and rank results by relevance and quality"""
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
        
        # Exclude domains we want to avoid
        excluded_domains = ['reddit.com', 'quora.com', 'stackoverflow.com']
        
        filtered = []
        for result in results:
            text_content = f"{result.get('title', '')} {result.get('snippet', '')}".lower()
            source = result.get('source', '').lower()
            
            # Skip excluded domains
            if any(excluded in source for excluded in excluded_domains):
                continue
            
            # Check if content contains AI-related keywords
            if any(keyword in text_content for keyword in ai_keywords):
                # Add relevance score
                score = self._calculate_relevance_score(result, ai_keywords)
                result['relevance_score'] = score
                filtered.append(result)
        
        # Sort by relevance score and take top 30 results for better diversity
        filtered.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        return filtered[:30]
    
    def _calculate_relevance_score(self, result: Dict, ai_keywords: List[str]) -> float:
        """Calculate relevance score for ranking"""
        score = 0.0
        text = f"{result.get('title', '')} {result.get('snippet', '')}".lower()
        
        # Keyword matching
        for keyword in ai_keywords:
            if keyword in text:
                score += 1.0
        
        # Source credibility boost - prioritize technical sources
        source = result.get('source', '').lower()
        if any(tech_source in source for tech_source in ['googleblog', 'openai', 'anthropic', 'microsoft', 'meta']):
            score += 5.0  # Highest boost for AI company technical blogs
        elif any(research in source for research in ['arxiv', 'papers.nips', 'deepmind']):
            score += 4.0  # High boost for research sources
        elif any(dev in source for dev in ['huggingface', 'github']):
            score += 3.5  # High boost for development platforms
        elif any(news in source for news in ['techcrunch', 'venturebeat', 'theinformation']):
            score += 2.0  # Lower boost for business news
        elif 'technologyreview.mit.edu' in source or 'spectrum.ieee.org' in source:
            score += 3.0  # Technical journalism
        
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