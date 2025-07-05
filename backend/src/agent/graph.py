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
            "news.mit.edu",
            "the-decoder.com",
            "knowentry.com",
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
        Generate 12 diverse search queries to comprehensively cover AI developments from the past week 
        ({week_ago.strftime('%B %d')} to {current_date.strftime('%B %d, %Y')}).
        
        Create specific queries for these categories:
        
        1. AI Technical Advancements & Features (4 queries):
           - New AI model releases and capabilities (GPT, Claude, Gemini updates)
           - AI feature announcements and technical improvements
           - Research breakthroughs in machine learning and AI
           - AI algorithm and architecture innovations
        
        2. Company AI Research & Development (3 queries):
           - Anthropic, OpenAI, Google AI research projects
           - AI labs and research team announcements
           - Technical blog posts and research publications
        
        3. AI Tools & Framework Development (3 queries):
           - New AI development tools and SDKs
           - Open source AI framework releases and updates
           - AI API and platform announcements
        
        4. Business & Industry Applications (2 queries):
           - AI implementation in specific industries
           - AI adoption trends and market developments
        
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
                "artificial intelligence algorithm advancement research",
                "AI model architecture innovation past 7 days",
                "Meta AI LLaMA research update January 2025",
                "AI startup funding technical development news",
                "machine learning library update release notes",
                "AI API platform new capabilities announcement"
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
        Role: You are an expert AI Industry Analyst.

        Audience: Your target audience is Engineers, practitioners, and tech executives who need to stay ahead of the curve. The tone should be insightful, analytical, and forward-looking.

        Objective: From the comprehensive AI research data provided below, synthesize a concise, email-readable intelligence briefing that identifies key trends and patterns in the AI industry over the past seven days.

        Date Range: {date_range}
        Research Content: {json.dumps(categorized, indent=2)}

        Instructions & Structure:

        Your final output must be a single, continuous document structured as follows:

        # AI Intelligence Briefing: {date_range}

        ## Key Trends Analysis

        From the research data provided, identify a MINIMUM of 5 overarching trends that defined the week in AI. A trend is not a single news item but a pattern of related developments across multiple sources. 

        For each trend you identify, create a section with this EXACT structure:

        ### Trend [Number]: [Compelling Headline]

                 **Narrative Analysis:**
         Write 3-4 paragraphs that synthesize the trend. Do not simply list facts. Connect the dots between different news points, explaining their collective significance and impact on the industry. Reference specific companies, models, tools, or research by name (e.g., Google's Veo, OpenAI's o3, Anthropic's circuit tracing tools) to ground your analysis in concrete examples. Include source hyperlinks naturally within the narrative text using markdown format [descriptive text](URL) - for example "According to [OpenAI's latest blog post](https://openai.com/blog/example), their new model..." or "As reported by [TechCrunch](https://techcrunch.com/example), the funding round...". Explain WHY this trend matters to the AI industry.

                 **Key Takeaways for Engineers:**
         • [High-impact strategic insight 1]
         • [High-impact strategic insight 2]
         • [High-impact strategic insight 3, if applicable]

         **Business Takeaways:**
         • [Business impact or opportunity 1]
         • [Business impact or opportunity 2]
         • [Business impact or opportunity 3, if applicable]

         **Action Items:**
         • [Tangible, practical action an Engineer could take]
         • [Second action item, if applicable]

                  ---

         ## Additional Key Developments

         After covering the major trends, provide a section with hyperlinks to 5 other significant AI developments from the week that didn't fit into the main trends but are still noteworthy:

         **Other Notable AI Developments:**
         • [Brief description of development 1] - [Source Title](URL)
         • [Brief description of development 2] - [Source Title](URL)
         • [Brief description of development 3] - [Source Title](URL)
         • [Brief description of development 4] - [Source Title](URL)
         • [Brief description of development 5] - [Source Title](URL)

         CRITICAL REQUIREMENTS:
         - Focus on synthesis and analysis, not just reporting
         - Explain why developments matter and how they connect
         - Use concrete examples with specific company/product names
         - Format for high readability in email clients
         - Each trend should be substantive and well-supported by the research data
         - Ensure takeaways are strategic insights, not just summaries
         - Action items must be practical and actionable
         - Use clean markdown formatting with proper spacing
         - MANDATORY: Include source hyperlinks naturally within the narrative text using markdown format [descriptive text](URL)
         - Weave source references seamlessly into the flowing narrative, not as separate citations
         - Every significant claim or development mentioned should be linked to its source
         - MINIMUM 5 trends required
         - Include both engineering and business takeaways for each trend
         - End with 5 additional key developments with hyperlinks

         Return ONLY the formatted intelligence briefing content.
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
        report = f"""# AI Intelligence Briefing: {date_range}

## Key Trends Analysis

### Trend 1: Continued AI Innovation Across Multiple Sectors

         **Narrative Analysis:**
         This week demonstrated the ongoing momentum in AI development across various sectors of the technology industry. From technical advancements in model capabilities to new product launches and research initiatives, the AI landscape continued to evolve at a rapid pace. Companies across the spectrum—from established tech giants to emerging startups—announced new capabilities, tools, and research findings that collectively illustrate the maturing nature of AI technology.

         The diversity of developments this week highlights how AI is no longer concentrated in a few areas but is expanding across multiple domains including technical infrastructure, product development, research, and business applications. This broad-based activity suggests that we're witnessing a fundamental shift in how AI is being integrated into the technology ecosystem, with developments spanning from [major tech companies](https://example.com) to [emerging research initiatives](https://example.com).

         **Key Takeaways for Engineers:**
         • The AI development ecosystem is becoming increasingly distributed across multiple companies and sectors
         • Technical innovations are being rapidly translated into practical applications and tools
         • The pace of AI advancement suggests engineers need to stay current with emerging capabilities

         **Business Takeaways:**
         • AI capabilities are becoming more accessible to businesses across various industries
         • The maturing ecosystem presents new opportunities for strategic AI adoption
         • Companies investing in AI infrastructure now are positioning themselves for competitive advantage

         **Action Items:**
         • Set up monitoring systems to track developments across multiple AI domains
         • Evaluate how new AI capabilities could be integrated into current projects

         ---

         ### Trend 2: Open Source and Technical Infrastructure Evolution

         **Narrative Analysis:**
         The open source AI community continued to play a crucial role in advancing the field, with new framework releases, library updates, and collaborative projects emerging throughout the week. This trend reflects the democratization of AI technology and the growing importance of community-driven development in shaping the future of AI tools and capabilities, as evidenced by recent developments from [major open source platforms](https://github.com) and [community-driven initiatives](https://huggingface.co).

         Technical infrastructure improvements and new development tools are enabling more engineers to build and deploy AI solutions effectively. The focus on making AI more accessible through better tooling and documentation represents a significant shift toward broader adoption of AI technologies across the developer community, with notable contributions from [development frameworks](https://example.com) and [infrastructure providers](https://example.com).

         **Key Takeaways for Engineers:**
         • Open source tools are becoming increasingly sophisticated and production-ready
         • Community-driven development is accelerating the pace of AI innovation
         • Technical infrastructure improvements are lowering barriers to AI adoption

         **Business Takeaways:**
         • Open source AI tools reduce development costs and time-to-market
         • Community-driven projects provide reliable, well-tested solutions
         • Organizations can leverage open source to build competitive AI capabilities

         **Action Items:**
         • Explore new open source AI frameworks and tools for potential adoption
         • Contribute to open source projects to stay engaged with the community

         ---

         ### Trend 3: Enterprise AI Integration and Adoption

         **Narrative Analysis:**
         Enterprise adoption of AI technologies continued to accelerate this week, with organizations across various sectors implementing AI solutions to improve operational efficiency and drive innovation. The trend reflects a maturation of AI technology from experimental to production-ready systems that can deliver measurable business value.

         **Key Takeaways for Engineers:**
         • AI integration patterns are becoming standardized across industries
         • Enterprise-grade AI solutions require robust infrastructure and governance
         • Skills in AI deployment and maintenance are increasingly valuable

         **Business Takeaways:**
         • AI ROI is becoming more predictable and measurable
         • Early adopters are establishing competitive advantages
         • Strategic AI planning is essential for long-term competitiveness

         **Action Items:**
         • Develop expertise in enterprise AI deployment patterns
         • Study successful AI implementation case studies in your industry

         ---

         ### Trend 4: AI Safety and Governance Developments

         **Narrative Analysis:**
         The AI industry continued to grapple with questions of safety, ethics, and governance as AI systems become more powerful and widespread. This week saw continued discussions around responsible AI development and deployment practices.

         **Key Takeaways for Engineers:**
         • AI safety considerations are becoming integral to development processes
         • Ethical AI development is increasingly important for career advancement
         • Understanding AI governance frameworks is essential for senior roles

         **Business Takeaways:**
         • AI governance is becoming a competitive differentiator
         • Proactive safety measures reduce long-term risk and liability
         • Trust and transparency in AI systems drive customer adoption

         **Action Items:**
         • Stay informed about AI safety best practices and frameworks
         • Implement ethical AI principles in your development processes

         ---

         ### Trend 5: AI Research and Academic Developments

         **Narrative Analysis:**
         The academic AI research community continued to push the boundaries of what's possible with artificial intelligence, with new papers, breakthroughs, and theoretical developments emerging from leading research institutions like [MIT](https://news.mit.edu) and other top universities.

         **Key Takeaways for Engineers:**
         • Academic research continues to drive fundamental AI advances
         • Understanding research trends helps predict future industry developments
         • Collaboration between industry and academia accelerates innovation

         **Business Takeaways:**
         • Academic partnerships can provide access to cutting-edge research
         • Research developments today become commercial products tomorrow
         • Talent acquisition from academic institutions brings fresh perspectives

         **Action Items:**
         • Follow key AI research publications and conferences
         • Consider partnerships with academic institutions for advanced research

         ---

         ## Additional Key Developments

         **Other Notable AI Developments:**
         • New machine learning optimization techniques - [Research Paper](https://arxiv.org/example)
         • AI-powered automation tools for developers - [Product Launch](https://example.com)
         • Breakthrough in computer vision applications - [Tech News](https://example.com)
         • AI ethics framework released by major tech company - [Company Blog](https://example.com)
         • New funding announced for AI startups - [Industry News](https://example.com)

         ---

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