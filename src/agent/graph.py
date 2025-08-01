# backend/src/agent/graph.py
"""AI Trends Weekly Reporter Agent"""

from typing import List, Dict, Any, Optional, TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from datetime import datetime, timedelta
import json
import os
import logging
import time
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
    trend_analysis: Dict  # Processed trend analysis with narratives

class AITrendsReporter:
    def __init__(self, gemini_api_key: str):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            api_key=gemini_api_key,
            temperature=0.1
        )
        self.search_service = GoogleSearchService()
        
        # Enhanced search service now handles source targeting internally
        # No longer need to maintain natural language search terms mapping
        

    
    def generate_ai_weekly_queries(self, state: AgentState) -> AgentState:
        """Generate enhanced news-focused search queries for recent AI developments"""
        generation_start_time = time.time()
        
        current_date = datetime.now()
        one_week_ago = current_date - timedelta(days=7)
        
        logging.info("🎯 Starting AI weekly query generation")
        logging.info(f"   📅 Date range: {one_week_ago.strftime('%B %d')} to {current_date.strftime('%B %d, %Y')}")
        logging.info(f"   🎯 Target: 12 news-focused queries")
        
        # Enhanced prompt for news-focused AI trend discovery
        prompt = f"""
        Generate strategic Google Search queries optimized for finding RECENT AI NEWS ARTICLES and BLOG POSTS from the past week.
        
        TARGET: Recent articles, blog posts, and announcements from quality sources like:
        - Company blogs: OpenAI, Anthropic, Google AI, Microsoft, Meta AI
        - Tech news: TechCrunch, VentureBeat, The Verge, Ars Technica, Reuters  
        - Research sources: MIT Technology Review, IEEE Spectrum
        
        QUERY OPTIMIZATION FOR NEWS:
        - Focus on actionable keywords: "announces", "releases", "launches", "introduces", "unveils"
        - Include company names for official announcements
        - Target specific AI domains: models, tools, APIs, frameworks, research
        - Use news-friendly terms that journalists use in headlines
        
        Date Context: Past 7 days ({one_week_ago.strftime('%B %d')} to {current_date.strftime('%B %d, %Y')})
        
        Generate 12 high-impact queries covering:
        
        1. COMPANY ANNOUNCEMENTS (4 queries):
           - Official product releases and updates from major AI companies
           - New model launches and API announcements
           
        2. DEVELOPER TOOLS & APIS (4 queries):  
           - New AI development tools and frameworks
           - API releases and developer platform updates
           
        3. RESEARCH & BREAKTHROUGHS (2 queries):
           - Significant research findings and technical advances
           - Academic and industry research publications
           
        4. INDUSTRY NEWS & TRENDS (2 queries):
           - Funding rounds, partnerships, industry movements
           - Market analysis and business developments
        
        CRITICAL REQUIREMENTS:
        - Each query must be 4-8 words for optimal Google News results
        - Include time-sensitive action words (announces, releases, launches)
        - Focus on specific, newsworthy events rather than general topics
        - Target queries that news outlets would write headlines about
        
        Return exactly 12 queries as a JSON array, ordered by priority.
        
        Example format: ["OpenAI announces new model", "AI coding tools released", "Google AI research breakthrough"]
        """
        
        try:
            logging.info("   🤖 Invoking LLM for query generation")
            llm_start_time = time.time()
            
            response = self.llm.invoke(prompt)
            
            llm_duration = time.time() - llm_start_time
            logging.info(f"   ⏱️  LLM response time: {llm_duration:.2f}s")
            
            content = response.content.strip()
            
            logging.info(f"   📏 Raw response length: {len(content)} characters")
            logging.debug(f"   📄 Raw response preview: {content[:200]}...")
            
            # Clean up JSON response
            original_content = content
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
                logging.info("   🧹 Cleaned JSON code block markers")
            elif content.startswith('```'):
                content = content.replace('```', '').strip()
                logging.info("   🧹 Cleaned generic code block markers")
            
            import re
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                content = json_match.group(0)
                logging.info("   🎯 Extracted JSON array from response")
            else:
                logging.warning("   ⚠️  No JSON array pattern found in response")
            
            logging.info(f"   📝 Attempting to parse JSON content")
            queries = json.loads(content)
            
            if not isinstance(queries, list):
                raise ValueError(f"Expected list, got {type(queries).__name__}")
            
            if len(queries) < 10:
                raise ValueError(f"Expected at least 10 queries, got {len(queries)}")
                
            queries = [str(q) for q in queries[:12]]  # Limit to 12 queries
            
            logging.info(f"   ✅ Successfully generated {len(queries)} queries")
            
            # Log generated queries
            logging.info("   📋 Generated queries:")
            for i, query in enumerate(queries, 1):
                logging.info(f"      {i:2d}. {query}")
            
        except json.JSONDecodeError as e:
            logging.error(f"   ❌ JSON parsing failed: {e}")
            logging.error(f"   📄 Content that failed to parse: {content[:500]}")
            logging.warning("   🔄 Falling back to predefined queries")
            
            # Enhanced fallback queries focused on recent news
            queries = [
                # Company announcements
                "OpenAI announces new model API",
                "Google AI releases latest research",  
                "Anthropic Claude model updates",
                "Microsoft AI tools announcement",
                
                # Developer tools  
                "AI coding assistant launched",
                "new AI developer framework",
                "AI API SDK released",
                "machine learning tools update",
                
                # Research breakthroughs
                "AI research breakthrough published",
                "artificial intelligence study results",
                
                # Industry trends
                "AI startup funding announcement", 
                "artificial intelligence partnership news"
            ]
            
        except ValueError as e:
            logging.error(f"   ❌ Query validation failed: {e}")
            logging.warning("   🔄 Falling back to predefined queries")
            
            queries = [
                "OpenAI announces new model API",
                "Google AI releases latest research",  
                "Anthropic Claude model updates",
                "Microsoft AI tools announcement",
                "AI coding assistant launched",
                "new AI developer framework",
                "AI API SDK released",
                "machine learning tools update",
                "AI research breakthrough published",
                "artificial intelligence study results",
                "AI startup funding announcement", 
                "artificial intelligence partnership news"
            ]
            
        except Exception as e:
            logging.error(f"   ❌ Unexpected error in query generation: {e}")
            logging.error(f"   🔍 Error type: {type(e).__name__}")
            import traceback
            logging.error(f"   📚 Full traceback: {traceback.format_exc()}")
            logging.warning("   🔄 Falling back to predefined queries")
            
            queries = [
                "OpenAI announces new model API",
                "Google AI releases latest research",  
                "Anthropic Claude model updates",
                "Microsoft AI tools announcement",
                "AI coding assistant launched",
                "new AI developer framework",
                "AI API SDK released",
                "machine learning tools update",
                "AI research breakthrough published",
                "artificial intelligence study results",
                "AI startup funding announcement", 
                "artificial intelligence partnership news"
            ]
        
        generation_duration = time.time() - generation_start_time
        
        # Update state
        state["search_queries"] = queries
        state["search_results"] = []
        state["report_date_range"] = f"{one_week_ago.strftime('%B %d')} - {current_date.strftime('%B %d, %Y')}"
        state["iteration_count"] = 0
        state["reflection_feedback"] = ""
        state["quality_score"] = 0.0
        state["needs_improvement"] = False
        state["improvement_areas"] = []
        
        logging.info(f"✅ Query generation completed in {generation_duration:.2f}s")
        logging.info(f"   📊 Final query count: {len(queries)}")
        logging.info(f"   📅 Date range set: {state['report_date_range']}")
        
        return state
    
    def research_ai_trends(self, state: AgentState) -> AgentState:
        """Execute enhanced AI trends research using improved search service"""
        research_start_time = time.time()
        
        base_queries = state["search_queries"]
        all_results = []
        
        logging.info("🔍 Starting AI trends research")
        logging.info(f"   📋 Base queries to process: {len(base_queries)}")
        logging.info(f"   🎯 Search method: Enhanced AI news search")
        
        # Track research statistics
        research_stats = {
            'queries_processed': 0,
            'queries_successful': 0,
            'queries_failed': 0,
            'total_results': 0,
            'supplementary_results': 0
        }
        
        # Use the enhanced search service for each query
        for i, query in enumerate(base_queries, 1):
            research_stats['queries_processed'] += 1
            
            logging.info(f"   🔍 Processing query {i}/{len(base_queries)}: '{query}'")
            
            try:
                query_start_time = time.time()
                
                # Use the new enhanced search method
                query_results = self.search_service.search_recent_ai_news(query, days_back=7)
                
                query_duration = time.time() - query_start_time
                
                # Mark results with query metadata
                for result in query_results:
                    result['search_query'] = query
                    result['from_enhanced_search'] = True
                    result['query_index'] = i
                
                all_results.extend(query_results)
                research_stats['queries_successful'] += 1
                research_stats['total_results'] += len(query_results)
                
                logging.info(f"      ✅ Retrieved {len(query_results)} results in {query_duration:.2f}s")
                
                # Rate limiting
                time.sleep(0.3)
                
            except Exception as e:
                research_stats['queries_failed'] += 1
                logging.error(f"      ❌ Enhanced search failed for query '{query}': {e}")
                logging.error(f"         🔍 Error type: {type(e).__name__}")
                continue
        
        logging.info(f"   📊 Base query results: {research_stats['total_results']} from {research_stats['queries_successful']}/{len(base_queries)} successful queries")
        
        # Add some supplementary searches for broader coverage
        supplementary_queries = [
            "AI breakthrough research",
            "machine learning model release",
            "artificial intelligence startup funding",
            "AI developer tools update"
        ]
        
        logging.info(f"   🔄 Running {len(supplementary_queries)} supplementary searches")
        
        for i, supp_query in enumerate(supplementary_queries, 1):
            logging.info(f"      🔍 Supplementary search {i}/{len(supplementary_queries)}: '{supp_query}'")
            
            try:
                supp_start_time = time.time()
                
                supp_results = self.search_service.search_recent_ai_news(supp_query, days_back=7)
                
                supp_duration = time.time() - supp_start_time
                
                for result in supp_results:
                    result['search_query'] = supp_query
                    result['from_enhanced_search'] = True
                    result['supplementary'] = True
                
                all_results.extend(supp_results)
                research_stats['supplementary_results'] += len(supp_results)
                
                logging.info(f"         ✅ Retrieved {len(supp_results)} supplementary results in {supp_duration:.2f}s")
                
                time.sleep(0.3)
                
            except Exception as e:
                logging.warning(f"         ❌ Supplementary search failed for query '{supp_query}': {e}")
                continue
        
        logging.info(f"   📊 Supplementary results: {research_stats['supplementary_results']}")
        logging.info(f"   📊 Total raw results collected: {len(all_results)}")
        
        # Analyze result distribution by source type
        source_type_analysis = {}
        for result in all_results:
            source_type = result.get('source_type', 'unknown')
            source_type_analysis[source_type] = source_type_analysis.get(source_type, 0) + 1
        
        logging.info(f"   📈 Source type distribution:")
        for source_type, count in source_type_analysis.items():
            percentage = (count / len(all_results)) * 100 if all_results else 0
            logging.info(f"      {source_type}: {count} ({percentage:.1f}%)")
        
        # Enhanced filtering and ranking with new metrics
        logging.info(f"   🔧 Starting result filtering and ranking")
        filter_start_time = time.time()
        
        filtered_results = self._filter_and_rank_enhanced_results(all_results)
        
        filter_duration = time.time() - filter_start_time
        research_duration = time.time() - research_start_time
        
        state["search_results"] = filtered_results
        
        # Final statistics
        logging.info(f"✅ AI trends research completed in {research_duration:.2f}s")
        logging.info(f"   📊 Research summary:")
        logging.info(f"      Total queries processed: {research_stats['queries_processed']}")
        logging.info(f"      Successful queries: {research_stats['queries_successful']}")
        logging.info(f"      Failed queries: {research_stats['queries_failed']}")
        logging.info(f"      Raw results collected: {len(all_results)}")
        logging.info(f"      Final filtered results: {len(filtered_results)}")
        logging.info(f"      Filtering efficiency: {(len(filtered_results)/max(len(all_results), 1)*100):.1f}%")
        logging.info(f"      Filter processing time: {filter_duration:.2f}s")
        
        # Quality analysis of final results
        if filtered_results:
            quality_dist = {}
            for result in filtered_results:
                quality = result.get('url_quality', 'unknown')
                quality_dist[quality] = quality_dist.get(quality, 0) + 1
            
            logging.info(f"   🏆 Final result quality distribution:")
            for quality, count in quality_dist.items():
                percentage = (count / len(filtered_results)) * 100
                logging.info(f"      {quality}: {count} ({percentage:.1f}%)")
        
        return state
    

    

    
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
        
        # Skip category/landing pages
        import re
        category_patterns = [
            r'/technology/artificial-intelligence/?$',  # Reuters AI category
            r'/category/[^/]+/?$',  # Generic category pages
            r'/topics/[^/]+/?$',  # Topic pages
            r'/news/?$', r'/blog/?$',  # News/blog homepages
            r'/ai/?$', r'/ml/?$'  # Short AI/ML landing pages
        ]
        
        for pattern in category_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                logging.warning(f"Skipping category/landing page URL: {url}")
                return False
        
        # Must be from a real domain with proper article path
        good_patterns = [
            '.com/', '.org/', '.edu/', '.ai/', '.co/', '.net/',
            '/blog/', '/news/', '/article/', '/post/', '/research/',
            '/papers/', '/docs/', '/about/', '/product/', '/release/'
        ]
        
        # Check for article-specific patterns (dates, IDs, slugs)
        article_indicators = [
            r'/\d{4}/\d{2}/',  # Date like /2025/07/
            r'/\d{4}-\d{2}-\d{2}/',  # Date like /2025-07-15/
            r'/-\d{8,}',  # Article ID
            r'/[a-z0-9-]{20,}',  # Long slug (at least 20 chars)
            r'/p/\d+', r'/article/\d+',  # Article with ID
            r'\.html$', r'\.htm$'  # HTML pages
        ]
        
        has_good_pattern = any(good in url.lower() for good in good_patterns)
        has_article_indicator = any(re.search(pattern, url) for pattern in article_indicators)
        
        # URL should have good pattern AND (article indicator OR be long enough)
        return has_good_pattern and (has_article_indicator or len(url) > 60)
    
    def reflect_on_quality(self, state: AgentState) -> AgentState:
        """Reflect on the quality of trend analysis to determine if another iteration is needed"""
        
        trend_analysis = state.get("trend_analysis", {})
        trends = trend_analysis.get("major_trends", [])
        search_results = state["search_results"]
        iteration_count = state.get("iteration_count", 0)
        
        # Quality metrics for trends
        num_trends = len(trends)
        total_developments = sum(len(trend.get("key_developments", [])) for trend in trends)
        trends_with_good_narrative = sum(1 for trend in trends if len(trend.get("narrative", "")) > 100)
        trends_with_tech_details = sum(1 for trend in trends if len(trend.get("technical_implications", "")) > 50)
        
        # Count quality indicators from search results
        good_urls = sum(1 for result in search_results if result.get('url_quality') == 'good')
        preferred_sources = sum(1 for result in search_results if result.get('from_preferred_source', False))
        cross_source_items = sum(1 for result in search_results if result.get('cross_source_frequency', 0) > 1)
        
        # Calculate quality score (0-100)
        quality_score = 0.0
        
        # Number of trends (25 points)
        if num_trends >= 7:
            quality_score += 25
        elif num_trends >= 6:
            quality_score += 22
        elif num_trends >= 5:
            quality_score += 20
        elif num_trends >= 4:
            quality_score += 15
        elif num_trends >= 3:
            quality_score += 10
        elif num_trends >= 2:
            quality_score += 5
        
        # Total developments (25 points)
        if total_developments >= 15:
            quality_score += 25
        elif total_developments >= 10:
            quality_score += 20
        elif total_developments >= 6:
            quality_score += 15
        elif total_developments >= 3:
            quality_score += 10
        
        # Narrative quality (20 points)
        narrative_ratio = trends_with_good_narrative / num_trends if num_trends > 0 else 0
        quality_score += narrative_ratio * 20
        
        # Technical depth (10 points)
        tech_ratio = trends_with_tech_details / num_trends if num_trends > 0 else 0
        quality_score += tech_ratio * 10
        
        # URL quality (10 points)
        url_quality_ratio = good_urls / len(search_results) if search_results else 0
        quality_score += url_quality_ratio * 10
        
        # Source diversity (10 points)
        source_ratio = preferred_sources / len(search_results) if search_results else 0
        quality_score += source_ratio * 10
        
        # Determine if improvement is needed
        needs_improvement = False
        improvement_areas = []
        
        if quality_score < 65:  # Threshold for quality
            needs_improvement = True
            
            if num_trends < 5:
                improvement_areas.append("insufficient_trends")
            if total_developments < 12:
                improvement_areas.append("insufficient_developments")
            if narrative_ratio < 0.5:
                improvement_areas.append("weak_narratives")
            if url_quality_ratio < 0.5:
                improvement_areas.append("poor_url_quality")
            if source_ratio < 0.3:
                improvement_areas.append("insufficient_preferred_sources")
        
        # Update state
        state["quality_score"] = quality_score
        state["needs_improvement"] = needs_improvement and iteration_count < 2
        state["improvement_areas"] = improvement_areas
        state["reflection_feedback"] = f"Quality score: {quality_score:.1f}/100. " + \
                                      f"Identified {num_trends} trends with {total_developments} total developments."
        
        logging.info(f"Reflection complete: {state['reflection_feedback']}")
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
                "AI agent frameworks launches past 2 weeks",
                "new AI coding tools announcements recent",
                "AI model capabilities breakthroughs past 2 weeks",
                "AI security concerns recent developments",
                "enterprise AI adoption case studies past 2 weeks",
                "AI hardware chips GPU announcements recent",
                "AI regulation policy updates recent",
                "quantum AI computing advances past 2 weeks",
                "AI robotics automation news recent"
            ])
        
        if "insufficient_developments" in improvement_areas:
            additional_queries.extend([
                "OpenAI Anthropic Google AI updates past 2 weeks",
                "Hugging Face GitHub AI releases recent",
                "AI startup launches product announcements past 2 weeks",
                "AI API SDK releases recent",
                "developer AI tools new features past 2 weeks"
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
        
        # If we don't have trend analysis, create a simple one
        if not trend_analysis or not trend_analysis.get("major_trends"):
            logging.warning("No trend analysis found, using simple fallback")
            trend_analysis = self._create_simple_trend_analysis(state.get("search_results", []))
        
        # Pre-process to ensure we have URLs
        for trend in trend_analysis.get("major_trends", []):
            for dev in trend.get("key_developments", []):
                if not dev.get("url") or dev["url"] == "#":
                    logging.warning(f"Missing URL for development: {dev.get('title', 'Unknown')}")
        
        prompt = f"""
        Create a compelling AI trends report for developers. Target length: 1000-1200 words total.
        
        CRITICAL URL RULES:
        1. DO NOT include ANY links in the trend descriptions
        2. Links should ONLY appear in the Sources section at the end of each trend
        3. In the Sources section, use the EXACT URL from the data, not domain-only URLs
        4. Each source should be formatted as: - [Source Name](exact full url)
        5. When mentioning a company or development in the narrative, just use the company/product name without links
        
        Trend Data with URLs:
        {json.dumps(trend_analysis, indent=2)}
        
        Date Range: {date_range}
        
        Report Structure:
        
        # Recent AI Trends and Advancements
        ## {date_range}
        
        
        [For each trend, create a section - aim for 150-200 words per trend:]
        
        ### [Use trend_title from data - make it compelling]
        
        [1-2 paragraphs totaling 150-200 words:
        - Opening: What's happening and why it matters (40-60 words)
        - Details: Key developments and companies involved (60-80 words)
        - Impact: What this means for developers (40-60 words)]
        
        **Sources:**
        - [exact source name from data](exact full url from data - NOT domain only)
        [List 2-3 most relevant sources]
        
        ---
        
        [Include 5-7 trends to reach 1000-1200 words total]
        
        Writing Guidelines:
        - Be concise - readers can visit sources for deep dives
        - Focus on the "what" and "why it matters"
        - Avoid redundancy between sections
        - Each trend should offer unique insights
        - Balance technical accuracy with accessibility
        
        REMEMBER: 
        1. Total report should be 1000-1200 words
        2. NO links in main text - only in Sources sections
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
        
        report = f"""# Recent AI Trends and Advancements
## {date_range}

"""
        
        for i, trend in enumerate(trends, 1):
            report += f"""### {trend['trend_title']}

{trend.get('narrative', 'Significant developments are emerging in this area.')}

"""
            # Add key developments with proper URLs
            developments_added = []
            for dev in trend.get('key_developments', [])[:5]:
                url = dev.get('url', '')
                # Only add developments with valid full URLs (not domain-only)
                if url and url != '#' and not url.endswith('.com/') and not url.endswith('.org/'):
                    title = dev.get('title', 'a significant development')
                    company = dev.get('company', 'A major player')
                    description = dev.get('description', 'represents an important advancement in the field.')
                    impact = dev.get('impact', '')
                    
                    # Write without links in the text
                    report += f"""{company} announced {title} which {description} {impact}\n\n"""
                    developments_added.append({'company': company, 'url': url})
            
            report += f"""
{trend.get('technical_implications', 'These developments have significant technical implications for developers.')}

{trend.get('developer_impact', 'Developers need to stay informed about these changes.')}

**Sources:**
"""
            # Add unique sources
            seen_urls = set()
            for dev in developments_added:
                if dev['url'] not in seen_urls:
                    seen_urls.add(dev['url'])
                    report += f"\n- [{dev['company']}]({dev['url']})"
            
            report += "\n\n---\n\n"""
        
        return report
    

    

    

    

    

    
    def _filter_and_rank_enhanced_results(self, results: List[Dict]) -> List[Dict]:
        """Enhanced filtering and ranking using new search service metrics"""
        filtered_results = []
        seen_urls = set()
        domain_counts = {}
        
        # Sort by relevance score from search service if available, otherwise use manual scoring
        def sort_key(result):
            relevance = result.get('relevance_score', self._calculate_manual_relevance(result))
            url_quality = result.get('url_quality', 'basic')
            source_type = result.get('source_type', 'general')
            
            # Priority scoring
            quality_score = {'high': 3, 'medium': 2, 'basic': 1}.get(url_quality, 1)
            type_score = {'official': 3, 'news': 2, 'general': 1}.get(source_type, 1)
            
            return (type_score, quality_score, relevance)
        
        sorted_results = sorted(results, key=sort_key, reverse=True)
        
        for result in sorted_results:
            url = result.get('url', '')
            domain = result.get('source', '').lower()
            
            # Skip duplicates
            if url in seen_urls:
                continue
            
            # Skip excluded domains
            excluded_domains = ['reddit.com', 'quora.com', 'stackoverflow.com', 'linkedin.com']
            if any(excluded in domain for excluded in excluded_domains):
                continue
            
            # Validate content quality
            if not self._is_quality_ai_content(result):
                continue
            
            # Limit results per domain for diversity
            domain_count = domain_counts.get(domain, 0)
            max_per_domain = 4 if result.get('source_type') == 'official' else 2
            
            if domain_count >= max_per_domain:
                continue
            
            seen_urls.add(url)
            domain_counts[domain] = domain_count + 1
            filtered_results.append(result)
            
            # Limit total results
            if len(filtered_results) >= 40:
                break
        
        logging.info(f"Enhanced filtering: {len(filtered_results)} quality results from {len(domain_counts)} sources")
        return filtered_results
    
    def _calculate_manual_relevance(self, result: Dict) -> float:
        """Calculate relevance score manually if not provided by search service"""
        score = 0.0
        
        # Enhanced AI keywords
        ai_keywords = [
            'ai', 'artificial intelligence', 'machine learning', 'deep learning',
            'neural network', 'llm', 'gpt', 'claude', 'gemini', 'chatgpt', 
            'anthropic', 'openai', 'google ai', 'microsoft ai',
            'transformer', 'generative ai', 'foundation model'
        ]
        
        title = result.get('title', '').lower()
        snippet = result.get('snippet', '').lower()
        
        # Title relevance (higher weight)
        score += sum(8 for keyword in ai_keywords if keyword in title)
        
        # Snippet relevance
        score += sum(3 for keyword in ai_keywords if keyword in snippet)
        
        # Recent news indicators
        news_indicators = ['announces', 'releases', 'launches', 'introduces', 'unveils', 'breakthrough']
        score += sum(5 for indicator in news_indicators if indicator in title.lower())
        
        return score
    
    def _is_quality_ai_content(self, result: Dict) -> bool:
        """Check if result contains quality AI content"""
        title = result.get('title', '').lower()
        snippet = result.get('snippet', '').lower()
        url = result.get('url', '')
        
        # Must contain AI-related terms
        ai_terms = ['ai', 'artificial intelligence', 'machine learning', 'neural', 'llm', 'gpt']
        has_ai_content = any(term in title or term in snippet for term in ai_terms)
        
        if not has_ai_content:
            return False
        
        # Skip generic or low-quality content
        skip_terms = ['tutorial', 'course', 'learning', 'guide', 'how to', 'beginner']
        if any(term in title for term in skip_terms):
            return False
        
        # Must have reasonable URL
        if not url or len(url) < 20:
            return False
        
        return True

    def _filter_and_rank_results_with_frequency(self, results: List[Dict]) -> List[Dict]:
        """Legacy method - redirects to enhanced filtering"""
        return self._filter_and_rank_enhanced_results(results)
        
    def _legacy_filter_and_rank_results_with_frequency(self, results: List[Dict]) -> List[Dict]:
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
        
        # Exclude domains we want to avoid
        excluded_domains = ['reddit.com', 'quora.com', 'stackoverflow.com']
        
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
    

    
    def analyze_trends_with_developer_impact(self, state: AgentState) -> AgentState:
        """Analyze trends and assess developer impact without predefined categories"""
        
        search_results = state["search_results"]
        
        # Create a more flexible prompt that allows organic trend discovery
        prompt = f"""
        Analyze these AI search results to identify ORGANIC TRENDS - not predefined categories.
        Look for patterns, common themes, and connected developments across the results.
        
        CRITICAL RULES:
        1. DO NOT force results into predefined categories
        2. PRESERVE EXACT URLs - copy them character-for-character from the search results
        3. Identify trends based on what's actually happening, not what we expect
        4. Each trend should represent a genuine pattern across multiple sources
        
        Search Results (with exact URLs to preserve):
        {json.dumps(search_results[:40], indent=2)}
        
        Identify 5-7 major trends based on these criteria:
        - Multiple related developments from different sources
        - Clear impact on developers/engineers
        - Recent and timely (within past 2 weeks)
        - Represents a shift or emerging pattern
        
        For each trend you identify:
        
        1. TREND TITLE: A compelling, descriptive title (not generic)
        
        2. NARRATIVE (1-2 paragraphs, 100-150 words):
           - What's the overarching story?
           - Why is this happening now?
           - How do the pieces connect?
        
        3. KEY DEVELOPMENTS:
           - Select 2-4 most important items that exemplify this trend
           - For each, COPY EXACTLY from search results:
             * title (exact)
             * url (exact - character for character)
             * snippet (exact)
             * source (exact)
           - Add your own "impact" analysis (one sentence)
        
        4. TECHNICAL IMPLICATIONS (2-3 sentences):
           - Architecture and infrastructure changes
           - New tools and technologies involved
        
        5. DEVELOPER IMPACT (2-3 sentences):
           - How this changes daily workflows
           - Key opportunities or challenges
        
        Return as JSON:
        {{
            "major_trends": [
                {{
                    "trend_id": "unique_id",
                    "trend_title": "Compelling title describing the trend",
                    "narrative": "2-3 paragraph story...",
                    "key_developments": [
                        {{
                            "title": "EXACT title from search results",
                            "company": "EXACT source from search results",
                            "description": "EXACT snippet from search results",
                            "url": "EXACT url from search results - DO NOT MODIFY",
                            "impact": "Your analysis of why this matters"
                        }}
                    ],
                    "technical_implications": "Technical analysis...",
                    "developer_impact": "Impact on developers...",
                    "evidence_strength": "strong|medium based on number of sources"
                }}
            ],
            "emerging_signals": ["Brief notes on patterns that might become trends"],
            "analysis_timestamp": "{datetime.now().isoformat()}"
        }}
        
        IMPORTANT: 
        - Let the data tell the story - don't force predetermined narratives
        - If you see a clear trend across multiple sources, include it
        - URLs must be copied EXACTLY - do not use domain-only URLs
        - Focus on what's NEW and CHANGING, not general AI topics
        """
        
        try:
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            
            # Clean JSON response
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            elif content.startswith('```'):
                content = content.replace('```', '').strip()
            
            trend_analysis = json.loads(content)
            
            # Validate URLs were preserved correctly
            url_validation_passed = True
            valid_trends = []
            
            for trend in trend_analysis.get("major_trends", []):
                # Validate each development has a proper URL
                valid_developments = []
                for dev in trend.get("key_developments", []):
                    url = dev.get("url", "")
                    
                    # Check if URL is valid (not domain-only)
                    if url and url != "#":
                        # Check for domain-only URLs
                        if url.endswith('.com/') or url.endswith('.org/') or '/' not in url.split('://')[-1]:
                            logging.warning(f"Invalid domain-only URL detected: {url}")
                            # Try to find the correct URL from search results
                            for result in search_results:
                                if result.get("title") == dev.get("title") and result.get("url"):
                                    dev["url"] = result["url"]
                                    logging.info(f"Fixed URL: {url} -> {result['url']}")
                                    break
                        
                        # Verify URL exists in original search results
                        url_found = False
                        for result in search_results:
                            if result.get("url") == dev.get("url"):
                                url_found = True
                                break
                        
                        if url_found or dev.get("url", "").startswith(('http://', 'https://')):
                            valid_developments.append(dev)
                        else:
                            logging.warning(f"URL not found in original results: {dev.get('url')}")
                    
                # Only keep trends with valid developments
                if valid_developments:
                    trend["key_developments"] = valid_developments
                    valid_trends.append(trend)
            
            trend_analysis["major_trends"] = valid_trends
            
            if not url_validation_passed:
                logging.warning("URL validation failed - some URLs may be incorrect")
            
            state["trend_analysis"] = trend_analysis
            
            # Log trend discovery
            trends_found = len(trend_analysis.get("major_trends", []))
            logging.info(f"Discovered {trends_found} organic trends from {len(search_results)} search results")
            
        except Exception as e:
            logging.error(f"Failed to analyze trends: {e}")
            # Create simple fallback analysis
            state["trend_analysis"] = self._create_simple_trend_analysis(search_results)
        
        return state
    
    def _create_simple_trend_analysis(self, search_results: List[Dict]) -> Dict:
        """Create a simple trend analysis when LLM fails"""
        trends = []
        
        for result in search_results[:6]:  # Limit to 6 results for simplicity
            trend = {
                "trend_id": f"trend_{len(trends) + 1}",
                "trend_title": result.get("title", "Untitled Trend"),
                "narrative": result.get("snippet", "No summary available"),
                "key_developments": [
                    {
                        "title": result.get("title", "Untitled"),
                        "company": result.get("source", "Unknown"),
                        "description": result.get("snippet", "No summary available"),
                        "url": result.get("url", "#"),
                        "impact": "Brief impact statement"
                    }
                ],
                "technical_implications": "Technical implications...",
                "developer_impact": "Impact on developers...",
                "evidence_strength": "weak based on limited data"
            }
            trends.append(trend)
        
        return {"major_trends": trends}
    
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
        
        # Create a mapping of all available URLs from trend analysis
        url_mapping = {}
        company_to_urls = {}
        
        for trend in trend_analysis.get("major_trends", []):
            for dev in trend.get("key_developments", []):
                url = dev.get("url", "")
                company = dev.get("company", "")
                title = dev.get("title", "")
                
                if url and url != "#" and not url.endswith(('.com/', '.org/')):
                    # Map company name to URL
                    if company:
                        if company not in company_to_urls:
                            company_to_urls[company] = []
                        company_to_urls[company].append(url)
                    
                    # Map title to URL  
                    if title:
                        url_mapping[title.lower()] = url
        
        # Pattern to find URLs in Sources sections
        sources_pattern = r'(\*\*Sources:\*\*)(.*?)(?=\n---|\Z)'
        
        def fix_sources_section(match):
            sources_header = match.group(1)
            sources_content = match.group(2)
            
            # Find all links in the sources section
            link_pattern = r'- \[([^\]]+)\]\((https?://[^\)]+)\)'
            
            def replace_source_url(link_match):
                source_name = link_match.group(1)
                current_url = link_match.group(2)
                
                # Check if URL is domain-only
                if re.match(r'^https?://[^/]+\.(com|org|net|io|ai|co|edu)/?$', current_url):
                    # Try to find the correct URL based on source name
                    if source_name in company_to_urls and company_to_urls[source_name]:
                        # Use the first available URL for this company
                        correct_url = company_to_urls[source_name][0]
                        logging.info(f"Fixed source URL: [{source_name}]({current_url}) -> [{source_name}]({correct_url})")
                        return f"- [{source_name}]({correct_url})"
                
                return link_match.group(0)
            
            # Fix URLs in sources section
            fixed_sources = re.sub(link_pattern, replace_source_url, sources_content)
            return sources_header + fixed_sources
        
        # Apply fixes to all Sources sections
        fixed_report = re.sub(sources_pattern, fix_sources_section, report_content, flags=re.DOTALL)
        
        return fixed_report

def should_continue_iteration(state: AgentState) -> str:
    """Determine whether to continue with another iteration or generate the final report"""
    
    iteration_count = state.get("iteration_count", 0)
    quality_score = state.get("quality_score", 0.0)
    needs_improvement = state.get("needs_improvement", False)
    improvement_areas = state.get("improvement_areas", [])
    
    logging.info("")
    logging.info("🤔 DECISION POINT: Continue Iteration or Generate Report?")
    logging.info("-" * 50)
    logging.info(f"   📊 Current Quality Score: {quality_score:.1f}/10")
    logging.info(f"   🔄 Current Iteration: {iteration_count}")
    logging.info(f"   📈 Needs Improvement: {'YES' if needs_improvement else 'NO'}")
    
    if improvement_areas:
        logging.info(f"   📝 Improvement Areas:")
        for area in improvement_areas[:3]:
            logging.info(f"      • {area}")
    
    if needs_improvement and iteration_count < 2:
        logging.info("")
        logging.info("🔄 DECISION: IMPROVE SEARCH")
        logging.info("   ➡️  Quality below threshold, attempting improvement")
        logging.info("   🎯 Next: Refine search strategy and re-research")
        return "improve_search"
    else:
        if iteration_count >= 2:
            logging.info("")
            logging.info("✅ DECISION: GENERATE REPORT")
            logging.info("   ➡️  Maximum iterations reached, proceeding with current results")
        else:
            logging.info("")
            logging.info("✅ DECISION: GENERATE REPORT")
            logging.info("   ➡️  Quality acceptable, proceeding to final report")
        
        logging.info("   🎯 Next: Generate weekly report")
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
    
    # Enhanced workflow logging
    def log_workflow_step(step_name: str, description: str, step_num: int, total_steps: int):
        """Log workflow progress with visual indicators"""
        progress = f"[{step_num}/{total_steps}]"
        logging.info(f"")
        logging.info(f"🚀 WORKFLOW STEP {progress}: {step_name.upper()}")
        logging.info(f"📝 {description}")
        logging.info(f"⏰ Started at: {datetime.now().strftime('%H:%M:%S')}")
        logging.info(f"{'='*60}")
    
    # Wrap each node function with enhanced logging
    def wrapped_generate_queries(state: AgentState) -> AgentState:
        log_workflow_step("Generate Queries", "Creating optimized search queries for AI trends", 1, 6)
        start_time = time.time()
        try:
            result = reporter.generate_ai_weekly_queries(state)
            duration = time.time() - start_time
            logging.info(f"✅ STEP 1 COMPLETED in {duration:.2f}s")
            logging.info(f"   📊 Generated {len(result.get('search_queries', []))} search queries")
            logging.info(f"   📅 Date range: {result.get('report_date_range', 'unknown')}")
            return result
        except Exception as e:
            logging.error(f"❌ STEP 1 FAILED after {time.time() - start_time:.2f}s: {e}")
            raise
    
    def wrapped_research(state: AgentState) -> AgentState:
        log_workflow_step("Research Trends", "Searching for AI developments across multiple sources", 2, 6)
        start_time = time.time()
        try:
            result = reporter.research_ai_trends(state)
            duration = time.time() - start_time
            logging.info(f"✅ STEP 2 COMPLETED in {duration:.2f}s")
            logging.info(f"   📊 Found {len(result.get('search_results', []))} total articles")
            
            # Show source breakdown
            sources = {}
            for article in result.get('search_results', []):
                domain = urlparse(article.get('link', '')).netloc
                sources[domain] = sources.get(domain, 0) + 1
            
            if sources:
                logging.info(f"   🌐 Top sources:")
                for i, (domain, count) in enumerate(sorted(sources.items(), key=lambda x: x[1], reverse=True)[:5], 1):
                    logging.info(f"      {i}. {domain}: {count} articles")
            
            return result
        except Exception as e:
            logging.error(f"❌ STEP 2 FAILED after {time.time() - start_time:.2f}s: {e}")
            raise
    
    def wrapped_analyze(state: AgentState) -> AgentState:
        log_workflow_step("Analyze Trends", "Processing articles and identifying key AI trends", 3, 6)
        start_time = time.time()
        try:
            result = reporter.analyze_trends_with_developer_impact(state)
            duration = time.time() - start_time
            logging.info(f"✅ STEP 3 COMPLETED in {duration:.2f}s")
            
            # Show analysis results
            analysis = result.get('trend_analysis', {})
            trends = analysis.get('trends', [])
            logging.info(f"   📈 Identified {len(trends)} major trends")
            
            for i, trend in enumerate(trends[:3], 1):
                title = trend.get('headline', 'Unknown Trend')
                logging.info(f"      {i}. {title}")
            
            return result
        except Exception as e:
            logging.error(f"❌ STEP 3 FAILED after {time.time() - start_time:.2f}s: {e}")
            raise
    
    def wrapped_reflect(state: AgentState) -> AgentState:
        log_workflow_step("Quality Reflection", "Evaluating content quality and completeness", 4, 6)
        start_time = time.time()
        try:
            result = reporter.reflect_on_quality(state)
            duration = time.time() - start_time
            logging.info(f"✅ STEP 4 COMPLETED in {duration:.2f}s")
            
            quality_score = result.get('quality_score', 0)
            needs_improvement = result.get('needs_improvement', False)
            iteration_count = result.get('iteration_count', 0)
            
            logging.info(f"   ⭐ Quality Score: {quality_score:.1f}/10")
            logging.info(f"   🔄 Iteration: {iteration_count + 1}")
            
            if needs_improvement:
                logging.info(f"   🔧 Needs Improvement: YES")
                improvements = result.get('improvement_areas', [])
                if improvements:
                    logging.info(f"   📝 Areas to improve:")
                    for improvement in improvements[:3]:
                        logging.info(f"      • {improvement}")
            else:
                logging.info(f"   ✅ Quality: Acceptable, proceeding to report generation")
            
            return result
        except Exception as e:
            logging.error(f"❌ STEP 4 FAILED after {time.time() - start_time:.2f}s: {e}")
            raise
    
    def wrapped_improve_search(state: AgentState) -> AgentState:
        log_workflow_step("Improve Search", "Refining search strategy based on quality feedback", 5, 6)
        start_time = time.time()
        try:
            result = reporter.improve_search_strategy(state)
            duration = time.time() - start_time
            logging.info(f"✅ STEP 5 COMPLETED in {duration:.2f}s")
            logging.info(f"   🔄 Returning to research with improved strategy")
            return result
        except Exception as e:
            logging.error(f"❌ STEP 5 FAILED after {time.time() - start_time:.2f}s: {e}")
            raise
    
    def wrapped_generate_report(state: AgentState) -> AgentState:
        log_workflow_step("Generate Report", "Creating final AI trends weekly report", 6, 6)
        start_time = time.time()
        try:
            result = reporter.generate_weekly_report(state)
            duration = time.time() - start_time
            logging.info(f"✅ STEP 6 COMPLETED in {duration:.2f}s")
            
            export_path = result.get('export_path', 'unknown')
            report_length = len(result.get('weekly_report', ''))
            
            logging.info(f"   📄 Report generated: {report_length:,} characters")
            logging.info(f"   💾 Saved to: {export_path}")
            logging.info(f"")
            logging.info(f"🎉 WORKFLOW COMPLETED SUCCESSFULLY!")
            logging.info(f"{'='*60}")
            
            return result
        except Exception as e:
            logging.error(f"❌ STEP 6 FAILED after {time.time() - start_time:.2f}s: {e}")
            raise
    
    # Build the workflow with reflection mechanism
    workflow = StateGraph(AgentState)
    
    # Add nodes with wrapped functions
    workflow.add_node("generate_queries", wrapped_generate_queries)
    workflow.add_node("research", wrapped_research)
    workflow.add_node("analyze", wrapped_analyze)
    workflow.add_node("reflect", wrapped_reflect)
    workflow.add_node("improve_search", wrapped_improve_search)
    workflow.add_node("generate_report", wrapped_generate_report)
    
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