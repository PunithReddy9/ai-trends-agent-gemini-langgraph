# AI Trends Weekly Reporter Agent

## Overview
An intelligent AI agent that generates comprehensive weekly reports on the latest AI trends and developments, specifically tailored for developers and engineers.

## Data Storage and URL Management

### JSON Data Structure
The system now generates comprehensive JSON files alongside each report to provide complete visibility into data fetching and URL handling:

#### Article Data JSON (`*_article_data.json`)
Contains complete metadata for every article fetched:
```json
{
  "metadata": {
    "timestamp": "2025-07-16T00:32:23.043090",
    "total_articles": 45,
    "data_structure_version": "1.0"
  },
  "articles": [
    {
      "id": "openai.com_1234",
      "title": "OpenAI Releases New API Features",
      "url": "https://openai.com/blog/new-api-features",
      "source": "openai.com",
      "snippet": "Brief description from search results...",
      "date_published": "2025-07-15",
      "date_fetched": "2025-07-16T00:32:23.043090",
      "search_metadata": {
        "from_preferred_source": true,
        "source_category": "openai.com",
        "url_quality": "good",
        "relevance_score": 8.5,
        "cross_source_frequency": 2
      },
      "content": {
        "has_full_content": true,
        "content_length": 2500,
        "fetch_status": "success",
        "raw_html_preview": "First 500 chars of HTML content...",
        "fetch_timestamp": "2025-07-16T00:32:23.043090"
      }
    }
  ]
}
```

#### URL Mapping JSON (`*_url_mapping.json`)
Provides debugging information for URL quality issues:
```json
{
  "metadata": {
    "created_at": "2025-07-16T00:32:23.043090",
    "purpose": "URL mapping for debugging domain-only URL issues"
  },
  "title_to_url_mapping": {
    "OpenAI Releases New API Features": {
      "url": "https://openai.com/blog/new-api-features",
      "company": "OpenAI",
      "is_domain_only": false,
      "is_valid": true
    }
  },
  "url_quality_report": {
    "total_urls": 25,
    "domain_only_urls": [
      {"title": "Some Article", "url": "https://example.com/"}
    ],
    "high_quality_urls": [
      {"title": "Good Article", "url": "https://openai.com/blog/article"}
    ],
    "missing_urls": ["Article Without URL"]
  }
}
```

### URL Quality Management

#### URL Classification
- **High Quality**: Direct article URLs with specific paths (`/blog/`, `/news/`, `/2025/`)
- **Domain Only**: URLs ending with just domain (`https://openai.com/`)
- **Poor Quality**: Search pages, constructed URLs, generic paths

#### URL Validation Process
1. **Initial Filtering**: Remove search pages and invalid URLs
2. **Quality Assessment**: Mark URLs as 'good' or 'poor' quality
3. **URL Improvement**: Re-search for better URLs when needed
4. **Post-Processing**: Fix domain-only URLs in final report

### Full Content Fetching (NEW)

The system now supports fetching full article content for high-quality URLs:

```python
# Enable full content fetching
enhanced_results = search_service.search_ai_content_with_full_fetch(query)

# Check if content was fetched
for result in enhanced_results:
    if result.get('content_fetched'):
        content = result['full_content']
        print(f"Fetched {content['content_length']} characters from {result['url']}")
```

### Debugging URL Issues

When you see warnings like:
```
WARNING:root:LLM returned domain-only URL: https://www.edweek.org/
WARNING:root:Domain-only URL found: [Education Week](https://www.edweek.org/)
WARNING:root:Missing 3 expected URLs from the report
```

Check the generated JSON files:
1. `*_article_data.json` - Shows all fetched articles with their URLs
2. `*_url_mapping.json` - Shows URL quality analysis and issues

### Common URL Issues and Solutions

1. **Domain-Only URLs**: LLM converts specific URLs to domain names
   - **Solution**: Check `url_quality_report.domain_only_urls` in JSON
   - **Fix**: Implement stricter URL preservation in prompts

2. **Missing URLs**: Articles without proper URLs in search results
   - **Solution**: Check `url_quality_report.missing_urls` in JSON
   - **Fix**: Improve search queries or URL validation

3. **Poor Quality URLs**: Search pages instead of article pages
   - **Solution**: Check `search_metadata.url_quality` in JSON
   - **Fix**: Enhance URL filtering and re-search logic

## Usage

```bash
# Run the agent (now generates additional JSON files)
python run_report.py

# Output files generated:
# - AI-Trends-Report-YYYY-MM-DD-HH-MM-SS.md (main report)
# - AI-Trends-Report-YYYY-MM-DD-HH-MM-SS_article_data.json (complete data)
# - AI-Trends-Report-YYYY-MM-DD-HH-MM-SS_url_mapping.json (URL debugging)
```

## Improvements Made

1. **Complete Data Visibility**: Every article's metadata now stored in JSON
2. **URL Quality Tracking**: Detailed analysis of URL issues
3. **Full Content Fetching**: Optional fetching of complete article content
4. **Debugging Tools**: JSON files to trace URL problems
5. **Enhanced Validation**: Multiple layers of URL quality checks

This ensures you have complete transparency into what data is being fetched, how URLs are being handled, and where any issues might be occurring. 