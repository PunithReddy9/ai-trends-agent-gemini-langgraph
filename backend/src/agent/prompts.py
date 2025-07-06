from datetime import datetime


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
