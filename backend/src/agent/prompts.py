from datetime import datetime, timedelta
from typing import List, Dict
import json


# Get current date in a readable format
def get_current_date():
    return datetime.now().strftime("%B %d, %Y")


query_writer_instructions = """Your goal is to generate strategic and effective web search queries optimized for Google Search API. These queries should maximize the likelihood of finding current, relevant information while avoiding common search failures.

SEARCH STRATEGY GUIDELINES:
- Prioritize broad, general queries over site-specific searches (site: operator often fails)
- Use natural language and common terminology rather than technical jargon
- Include temporal indicators for recent information (2024, 2025, "recent", "latest")
- Avoid overly specific or niche terms that might return zero results
- Focus on mainstream news sources and official announcements rather than specific sites

QUERY OPTIMIZATION RULES:
- Use 3-8 words per query for optimal results
- Include relevant keywords that news outlets commonly use
- Add context words like "news", "update", "announcement", "report" when appropriate
- Avoid special characters, quotes, and complex operators
- Test query variations: broad to specific, different keyword combinations

Instructions:
- Generate 1-3 diverse queries maximum, focusing on different angles of the topic
- Each query should be independent and cover a distinct aspect
- Prioritize queries most likely to return current, credible results
- Current date: {current_date}

Format: 
- Format your response as a JSON object with these exact keys:
   - "rationale": Brief explanation of search strategy and why these queries will be effective
   - "query": A list of 1-3 search queries (ordered by priority)

Example:

Topic: Latest developments in AI regulation in Europe
```json
{{
    "rationale": "Using broad, news-focused queries that avoid site-specific searches. Prioritizing general terms that major news outlets use, with temporal indicators for recent information. Covering regulatory, business, and policy angles to ensure comprehensive coverage.",
    "query": ["AI regulation Europe 2024 news", "European Union artificial intelligence act latest updates", "AI compliance requirements Europe recent developments"]
}}
```

Context: {research_topic}"""


web_searcher_instructions = """Conduct strategic web searches to gather the most current, credible information on "{research_topic}" and synthesize findings into a comprehensive report.

SEARCH EXECUTION STRATEGY:
- Execute queries in priority order (most likely to succeed first)
- If a query returns no results, skip to the next query immediately
- Focus on analyzing results from mainstream news sources, official sites, and credible publications
- Look for publication dates and prioritize sources from the last 6 months
- Cross-reference information across multiple sources for accuracy

RESULT PROCESSING:
- Extract key facts, figures, and developments from search results
- Note contradictions or conflicting information between sources
- Identify the most recent and authoritative information
- Track which specific sources provided each piece of information

SYNTHESIS REQUIREMENTS:
- Create a well-structured summary organized by key themes or chronological order
- Include specific dates, numbers, and factual details when available
- Clearly indicate the recency and reliability of information
- Highlight any significant developments or breaking news
- Current date: {current_date}

OUTPUT FORMAT:
- Begin with a brief executive summary (2-3 sentences)
- Organize main content into clear sections with descriptive headings
- Include source attribution for all major claims
- End with a note about information freshness and any limitations

Research Topic: {research_topic}
"""


reflection_instructions = """You are an expert research analyst evaluating the completeness and quality of research summaries about "{research_topic}".

EVALUATION CRITERIA:
- Completeness: Are all major aspects of the topic covered?
- Recency: Is the information current and up-to-date?
- Depth: Are there areas that need more detailed exploration?
- Accuracy: Are there conflicting claims that need verification?
- Context: Is important background or related information missing?

KNOWLEDGE GAP IDENTIFICATION:
- Look for missing recent developments or breaking news
- Identify areas where more specific data or examples would be helpful
- Note any conflicting information that needs clarification
- Consider related topics or implications that weren't explored

FOLLOW-UP QUERY OPTIMIZATION:
- Design queries that are likely to succeed with Google Search API
- Use broad, natural language rather than site-specific searches
- Include temporal indicators for recent information
- Focus on mainstream terminology and common news angles

Requirements:
- If summaries adequately address the user's question with current information, mark as sufficient
- If knowledge gaps exist, create 1-2 strategic follow-up queries
- Ensure follow-up queries are self-contained and optimized for search success

Output Format:
```json
{{
    "is_sufficient": true, // or false
    "knowledge_gap": "Specific description of missing information or areas needing clarification", // "" if is_sufficient is true
    "follow_up_queries": ["Strategic follow-up query optimized for Google Search API"] // [] if is_sufficient is true
}}
```

Example:
```json
{{
    "is_sufficient": false,
    "knowledge_gap": "The summary lacks specific implementation timelines and regulatory compliance deadlines that businesses need to know about",
    "follow_up_queries": ["AI regulation compliance deadlines Europe 2024 2025"]
}}
```

Summaries:
{summaries}
"""


answer_instructions = """Generate a comprehensive, well-structured answer to the user's question based on the research summaries provided.

CONTENT ORGANIZATION:
- Start with a clear, direct answer to the user's main question
- Organize information logically with clear headings and sections
- Present the most important and recent information first
- Include specific details, dates, and quantitative data when available

CITATION REQUIREMENTS:
- Include ALL citations from the summaries correctly
- Use proper attribution for each claim or piece of information
- Indicate the recency of information (e.g., "as of [date]")
- Note any conflicting information from different sources

QUALITY STANDARDS:
- Write in clear, accessible language appropriate for the audience
- Provide context and background where necessary
- Highlight key trends, developments, or implications
- Include actionable insights or takeaways when relevant

FORMATTING:
- Use markdown formatting for better readability
- Include relevant headings and subheadings
- Use bullet points or lists only when they improve clarity
- Ensure proper paragraph structure and flow

COMPLETENESS CHECK:
- Address all aspects of the user's original question
- Include both current developments and relevant background
- Note any limitations in the available information
- Suggest areas for further research if applicable

Current date: {current_date}

User Question: {research_topic}

Research Summaries:
{summaries}"""


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
       - Focus: What new agent capabilities are emerging?
    
    2. AI CODING REVOLUTION (3 queries):
       - AI coding assistants, code generation, pair programming
       - Developer productivity tools, IDE integrations
       - Focus: How is AI changing software development?
    
    3. MODEL CAPABILITIES & BREAKTHROUGHS (3 queries):
       - New model releases, benchmarks, performance improvements
       - Multimodal advances, reasoning capabilities
       - Focus: What technical boundaries are being pushed?
    
    4. DEVELOPER TOOLS & APIS (3 queries):
       - New APIs, SDKs, frameworks, libraries
       - Integration patterns, deployment solutions
       - Focus: What new tools can developers use TODAY?
    
    5. INDUSTRY SHIFTS & ADOPTION (3 queries):
       - Enterprise AI adoption, job market changes
       - Security concerns, ethical considerations
       - Focus: How is AI reshaping the tech industry?
    
    Query Strategy:
    - Use terms like "breakthrough", "launch", "release", "announces"
    - Include company names: OpenAI, Anthropic, Google, Microsoft, Meta
    - Mix technical and business perspectives
    - Look for patterns across multiple developments
    
    Return EXACTLY 15 queries as a JSON array.
    """


def identify_trend_patterns(self, search_results: List[Dict]) -> Dict[str, List[Dict]]:
    """Identify emerging trends and patterns across search results"""
    
    # Define trend themes to look for
    trend_themes = {
        "agent_revolution": {
            "keywords": ["agent", "autonomous", "CUA", "operator", "mariner", "workflow"],
            "companies": ["openai", "google", "microsoft", "mistral"],
            "related_items": []
        },
        "ai_coding": {
            "keywords": ["coding", "cursor", "copilot", "code generation", "developer", "IDE"],
            "companies": ["github", "cursor", "replit", "codestral"],
            "related_items": []
        },
        "model_evolution": {
            "keywords": ["model", "benchmark", "performance", "capabilities", "multimodal"],
            "companies": ["openai", "anthropic", "google", "deepseek"],
            "related_items": []
        },
        "deepfake_concerns": {
            "keywords": ["deepfake", "synthetic", "detection", "trust", "verification"],
            "companies": ["resemble", "elevenlabs", "runway"],
            "related_items": []
        },
        "enterprise_adoption": {
            "keywords": ["enterprise", "adoption", "integration", "deployment", "scale"],
            "companies": ["microsoft", "salesforce", "aws", "google cloud"],
            "related_items": []
        }
    }
    
    # Analyze each result for trend signals
    for result in search_results:
        title = result.get("title", "").lower()
        snippet = result.get("snippet", "").lower()
        source = result.get("source", "").lower()
        
        for theme_name, theme_data in trend_themes.items():
            # Check if result matches theme
            keyword_match = any(kw in title + snippet for kw in theme_data["keywords"])
            company_match = any(comp in title + snippet + source for comp in theme_data["companies"])
            
            if keyword_match or company_match:
                theme_data["related_items"].append({
                    **result,
                    "theme_relevance": "high" if keyword_match and company_match else "medium"
                })
    
    return trend_themes


def validate_and_enrich_trends(self, identified_trends: Dict) -> Dict:
    """Validate trends by finding corroborating evidence across sources"""
    
    enriched_trends = {}
    
    for trend_name, trend_data in identified_trends.items():
        # Count how many different sources report on this trend
        sources = {}
        for item in trend_data["related_items"]:
            source = item.get("source", "")
            sources[source] = sources.get(source, 0) + 1
        
        # Calculate trend strength based on:
        # 1. Number of different sources
        # 2. Authority of sources
        # 3. Recency of reports
        trend_strength = len(sources)
        if any(auth in sources for auth in ["openai", "google", "microsoft", "anthropic"]):
            trend_strength += 2
        
        enriched_trends[trend_name] = {
            **trend_data,
            "source_diversity": len(sources),
            "trend_strength": trend_strength,
            "corroborating_sources": list(sources.keys())[:5]
        }
    
    return enriched_trends


def analyze_trends_with_developer_impact(self, state: AgentState) -> AgentState:
    """Analyze trends and assess developer impact"""
    
    # First identify trend patterns
    trend_patterns = self.identify_trend_patterns(state["search_results"])
    
    prompt = f"""
    Analyze these AI developments to identify MAJOR TRENDS and their impact on developers.
    
    Search Results: {json.dumps(state["search_results"][:30], indent=2)}
    Identified Patterns: {json.dumps(trend_patterns, indent=2)}
    
    For each major trend you identify:
    
    1. TREND NARRATIVE:
       - What's the overarching story? (e.g., "The Rise of Autonomous AI Agents")
       - How do multiple developments connect to form this trend?
       - What's driving this trend forward?
    
    2. TECHNICAL DETAILS:
       - Specific technologies, APIs, frameworks involved
       - Technical capabilities being introduced
       - Implementation requirements and considerations
    
    3. DEVELOPER IMPACT:
       - How does this change developer workflows?
       - What new skills are needed?
       - What opportunities does this create?
       - What challenges must be addressed?
    
    4. KEY DEVELOPMENTS:
       - List 3-5 specific announcements that exemplify this trend
       - Include company, product name, and key features
       - Prioritize developments with immediate availability
    
    5. ACTIONABLE INSIGHTS:
       - What should developers do TODAY?
       - What should they learn or experiment with?
       - What tools should they evaluate?
    
    Structure your analysis as:
    {{
        "major_trends": [
            {{
                "trend_title": "The Rise of AI Agents",
                "narrative": "We're witnessing...",
                "technical_details": "...",
                "developer_impact": "...",
                "key_developments": [...],
                "action_items": [...],
                "supporting_evidence": [...]
            }}
        ],
        "cross_cutting_themes": [...],
        "emerging_concerns": [...]
    }}
    """


def generate_developer_trend_report(self, state: AgentState) -> AgentState:
    """Generate trend-focused report with developer insights"""
    
    trend_analysis = state["trend_analysis"]
    date_range = state["report_date_range"]
    
    prompt = f"""
    Create a compelling AI trends report for developers using this analysis:
    
    Trend Analysis: {json.dumps(trend_analysis, indent=2)}
    Date Range: {date_range}
    
    CRITICAL: Write in the style of the provided example - narrative-driven, insightful, and developer-focused.
    
    Structure:
    
    # AI Trends Weekly: {date_range}
    
    [For each major trend, create a section like:]
    
    ## Trend 1: [Compelling Title like "Agents are Taking the Scene, Changing Your Job"]
    
    [Opening paragraph: Set the scene with a compelling narrative about what's happening]
    
    [2-3 paragraphs diving deep into specific developments, connecting them to show the bigger picture]
    
    [Technical implications paragraph - what this means for architecture, infrastructure, skills]
    
    [Balanced perspective - include both opportunities and challenges]
    
    ### Key Takeaways for AI Engineers
    [3 bullet points with specific, actionable insights]
    
    ### Action Items:
    [2-3 specific things developers should do this week]
    
    Writing Guidelines:
    - Use vivid, engaging language ("witnessing the emergence", "fundamental shift")
    - Connect multiple developments to show patterns
    - Explain WHY things matter, not just WHAT happened
    - Include specific product names, features, and capabilities
    - Provide technical depth while remaining accessible
    - Balance enthusiasm with pragmatism
    - Use metaphors and analogies to explain complex concepts
    - Embed source links naturally in the text
    
    Tone:
    - Authoritative but approachable
    - Technically informed but not jargon-heavy
    - Forward-looking but grounded in current reality
    - Excited about possibilities but aware of challenges
    
    Remember: This is for developers who need to understand not just what's new, 
    but how it changes their work and what they should do about it.
    """
