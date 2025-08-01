# Google Custom Search API Parameters Guide

## 🎯 **Complete Parameter Reference for Fine-Tuning Search Results**

This guide covers all Google Custom Search API parameters you can use to optimize your AI trends search functionality for better quality, relevance, and targeting.

## 📋 **Core Search Parameters**

### **`q` (Query) - The Search Term**
```python
# Basic query
'q': 'OpenAI announces new model'

# Advanced query techniques
'q': '"OpenAI announces" AND (model OR API OR release)'  # Boolean operators
'q': 'OpenAI -reddit -youtube'                           # Exclude terms
'q': 'AI breakthrough OR "artificial intelligence" breakthrough'  # Synonyms
'q': 'site:openai.com ChatGPT'                          # Site-specific
'q': 'filetype:pdf AI research'                         # File type
'q': 'intitle:"AI breakthrough" 2024'                   # Title must contain
```

### **`cx` (Custom Search Engine ID)**
```python
'cx': 'your_search_engine_id'  # Required - your configured search engine
```

### **`key` (API Key)**
```python
'key': 'your_api_key'  # Required - your Google API key
```

## 🎯 **Search Type Parameters**

### **`tbm` (To Be Matched) - Search Type**
```python
'tbm': 'nws'     # News search (best for recent articles)
'tbm': 'isch'    # Image search
'tbm': 'vid'     # Video search
'tbm': 'shop'    # Shopping search
# None/Empty    # Web search (default)
```

**Recommendation for AI News:** Use `'tbm': 'nws'` for recent news articles

### **`searchType` - Structured Search**
```python
'searchType': 'image'  # Alternative to tbm=isch
```

## 📅 **Time-Based Filtering**

### **Date Range Queries**
```python
# In the query string
'q': 'AI breakthrough after:2024-01-01'           # After specific date
'q': 'AI breakthrough before:2024-12-31'          # Before specific date  
'q': 'AI breakthrough after:2024-01-01 before:2024-12-31'  # Date range

# Relative dates
'q': 'AI breakthrough past:week'                  # Past week
'q': 'AI breakthrough past:month'                 # Past month
'q': 'AI breakthrough past:year'                  # Past year
```

### **`dateRestrict` Parameter**
```python
'dateRestrict': 'd1'     # Past day
'dateRestrict': 'd7'     # Past 7 days  
'dateRestrict': 'w1'     # Past week
'dateRestrict': 'm1'     # Past month
'dateRestrict': 'm6'     # Past 6 months
'dateRestrict': 'y1'     # Past year
```

## 🌍 **Geographic and Language Parameters**

### **`gl` (Geolocation)**
```python
'gl': 'us'      # United States
'gl': 'uk'      # United Kingdom  
'gl': 'ca'      # Canada
'gl': 'au'      # Australia
'gl': 'de'      # Germany
'gl': 'fr'      # France
'gl': 'jp'      # Japan
```

### **`hl` (Host Language)**
```python
'hl': 'en'      # English
'hl': 'es'      # Spanish
'hl': 'fr'      # French
'hl': 'de'      # German
'hl': 'ja'      # Japanese
```

### **`lr` (Language Restrict)**
```python
'lr': 'lang_en'    # English language pages
'lr': 'lang_es'    # Spanish language pages  
'lr': 'lang_fr'    # French language pages
'lr': 'lang_de'    # German language pages
```

### **`cr` (Country Restrict)**
```python
'cr': 'countryUS'  # United States
'cr': 'countryUK'  # United Kingdom
'cr': 'countryCA'  # Canada
'cr': 'countryAU'  # Australia
```

## 🔍 **Result Control Parameters**

### **`num` (Number of Results)**
```python
'num': 10       # Default, maximum 10 per request
'num': 5        # Fewer results for faster processing
```

### **`start` (Starting Index)**
```python
'start': 1      # First page (default)
'start': 11     # Second page (for pagination)
'start': 21     # Third page
```

### **`sort` (Sort Order)**
```python
'sort': 'date'           # Sort by date (newest first)
'sort': 'relevance'      # Sort by relevance (default)
# Custom sort expressions available for some search engines
```

## 🛡️ **Content Filtering Parameters**

### **`safe` (Safe Search)**
```python
'safe': 'active'    # Filter explicit content
'safe': 'off'       # No filtering (recommended for news)
```

### **`filter` (Duplicate Filtering)**
```python
'filter': '1'       # Enable duplicate filtering (default)
'filter': '0'       # Disable duplicate filtering
```

## 🎛️ **Advanced Search Parameters**

### **`siteSearch` and `siteSearchFilter`**
```python
'siteSearch': 'openai.com'              # Search only this site
'siteSearchFilter': 'i'                 # Include site ('i' = include, 'e' = exclude)

# Example: Search OpenAI and Anthropic only
'siteSearch': 'openai.com OR anthropic.com'
'siteSearchFilter': 'i'
```

### **`linkSite`**
```python
'linkSite': 'openai.com'  # Find pages linking to this site
```

### **`relatedSite`**
```python
'relatedSite': 'openai.com'  # Find sites related to this site
```

### **`excludeTerms`**
```python
'excludeTerms': 'reddit youtube'  # Exclude these terms from results
```

### **`exactTerms`**
```python
'exactTerms': 'artificial intelligence'  # Results must contain this exact phrase
```

### **`orTerms`**
```python
'orTerms': 'breakthrough announcement release'  # Results should contain at least one
```

## 🏷️ **Metadata and Display Parameters**

### **`fileType`**
```python
'fileType': 'pdf'     # Only PDF files
'fileType': 'doc'     # Only DOC files
'fileType': 'txt'     # Only text files
```

### **`fields` (Response Fields)**
```python
'fields': 'items(title,link,snippet,displayLink,pagemap)'  # Limit response data
```

### **`prettyPrint`**
```python
'prettyPrint': 'false'  # Reduce response size
```

## 🚀 **Optimized Parameter Sets for AI News**

### **Configuration 1: Recent AI News (Primary)**
```python
{
    'key': api_key,
    'cx': search_engine_id,
    'q': 'OpenAI announces new model after:2024-07-14',
    'tbm': 'nws',           # News search
    'num': 10,
    'sort': 'date',         # Recent first
    'gl': 'us',             # US results
    'hl': 'en',             # English
    'lr': 'lang_en',        # English pages
    'cr': 'countryUS',      # US country
    'safe': 'off',          # No content filtering
    'filter': '1'           # Remove duplicates
}
```

### **Configuration 2: Official Company Sources**
```python
{
    'key': api_key,
    'cx': search_engine_id,
    'q': 'announcement OR release OR update',
    'siteSearch': 'openai.com OR anthropic.com OR ai.googleblog.com',
    'siteSearchFilter': 'i',
    'num': 10,
    'sort': 'date',
    'dateRestrict': 'w1',   # Past week
    'gl': 'us',
    'hl': 'en',
    'safe': 'off'
}
```

### **Configuration 3: High-Quality Tech News**
```python
{
    'key': api_key,
    'cx': search_engine_id,
    'q': 'AI artificial intelligence',
    'siteSearch': 'techcrunch.com OR venturebeat.com OR theverge.com OR wired.com',
    'siteSearchFilter': 'i',
    'tbm': 'nws',
    'num': 10,
    'sort': 'date',
    'dateRestrict': 'd7',   # Past 7 days
    'gl': 'us',
    'hl': 'en',
    'safe': 'off'
}
```

### **Configuration 4: Research and Academic Sources**
```python
{
    'key': api_key,
    'cx': search_engine_id,
    'q': 'AI research OR "artificial intelligence" research',
    'siteSearch': 'arxiv.org OR papers.nips.cc OR technologyreview.mit.edu',
    'siteSearchFilter': 'i',
    'num': 10,
    'sort': 'date',
    'dateRestrict': 'm1',   # Past month
    'fileType': 'pdf',      # Research papers
    'gl': 'us',
    'hl': 'en'
}
```

## 🎯 **Parameter Combinations for Better Results**

### **1. Maximize Recency**
```python
# Combine multiple time filters
'q': 'AI breakthrough after:2024-07-14',
'tbm': 'nws',
'sort': 'date',
'dateRestrict': 'w1'
```

### **2. Improve Relevance**
```python
# Use exact terms and OR terms
'q': 'OpenAI',
'exactTerms': 'artificial intelligence',
'orTerms': 'ChatGPT GPT model API announcement release'
```

### **3. Filter Low-Quality Sources**
```python
# Exclude common low-quality sites
'q': 'AI news -site:reddit.com -site:quora.com -site:pinterest.com',
'safe': 'off',
'filter': '1'
```

### **4. Geographic Targeting**
```python
# Focus on specific regions for relevant coverage
'gl': 'us',
'cr': 'countryUS',
'hl': 'en',
'lr': 'lang_en'
```

## 📊 **Performance Optimization Parameters**

### **Reduce API Calls**
```python
'num': 10,              # Maximum results per call
'fields': 'items(title,link,snippet,displayLink)',  # Limit response data
'prettyPrint': 'false'  # Reduce JSON size
```

### **Cache-Friendly Queries**
```python
# Use consistent parameter ordering
# Cache results based on date ranges
'dateRestrict': 'd1'  # More cacheable than absolute dates
```

## 🛠️ **Implementation in Your Code**

### **Enhanced Search Function**
```python
def enhanced_ai_search(query, search_type='news', time_range='week'):
    """Enhanced search with optimized parameters"""
    
    # Base parameters
    params = {
        'key': self.api_key,
        'cx': self.search_engine_id,
        'q': query,
        'num': 10,
        'gl': 'us',
        'hl': 'en',
        'lr': 'lang_en',
        'safe': 'off',
        'filter': '1'
    }
    
    # Search type specific parameters
    if search_type == 'news':
        params.update({
            'tbm': 'nws',
            'sort': 'date',
            'cr': 'countryUS'
        })
    elif search_type == 'official':
        params.update({
            'siteSearch': 'openai.com OR anthropic.com OR ai.googleblog.com',
            'siteSearchFilter': 'i',
            'sort': 'date'
        })
    
    # Time range parameters
    time_ranges = {
        'day': 'd1',
        'week': 'w1', 
        'month': 'm1',
        'year': 'y1'
    }
    
    if time_range in time_ranges:
        params['dateRestrict'] = time_ranges[time_range]
    
    return params
```

## 🎯 **Recommendations for Your Use Case**

### **For AI Trends Analysis:**
1. **Use `tbm=nws`** for recent news articles
2. **Combine `sort=date`** with `dateRestrict=w1` for freshness  
3. **Set `num=10`** for comprehensive coverage
4. **Use geographic filtering** (`gl=us`, `cr=countryUS`) for relevant coverage
5. **Enable duplicate filtering** (`filter=1`) to avoid redundancy
6. **Use site-specific searches** for official announcements

### **Query Optimization Tips:**
1. **Use after:YYYY-MM-DD** in queries for precise date filtering
2. **Combine Boolean operators** (AND, OR, -) for better targeting
3. **Use quotation marks** for exact phrase matching
4. **Exclude low-quality sources** with -site: operators
5. **Include synonyms** with OR operators for broader coverage

This comprehensive parameter set will significantly improve your search result quality and relevance for AI trends analysis. 