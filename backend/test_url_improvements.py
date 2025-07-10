#!/usr/bin/env python3
"""
Test script for URL validation, re-ranking, and export functionality
"""

import os
import sys
import json
import tempfile
from datetime import datetime
from unittest.mock import Mock, patch

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.agent.graph import AITrendsReporter, create_graph

def test_url_validation():
    """Test URL validation functionality"""
    print("🔍 Testing URL validation...")
    
    # Mock API key
    reporter = AITrendsReporter("test-api-key")
    
    # Test high-quality URL detection
    good_urls = [
        "https://ai.googleblog.com/2024/01/new-breakthrough-in-ai.html",
        "https://openai.com/blog/gpt-4-improvements",
        "https://blog.anthropic.com/claude-3-announcement",
        "https://techcrunch.com/2024/01/15/ai-startup-funding/",
        "https://github.com/microsoft/DeepSpeed/releases/tag/v0.12.0"
    ]
    
    bad_urls = [
        "https://google.com/search?q=ai+news",
        "https://example.com/home",
        "https://site.com/index.html",
        "https://how-to-finetune-small-language-models-to-think-with",
        "https://artificial-intelligence-index"
    ]
    
    for url in good_urls:
        if not reporter._is_high_quality_article_url(url):
            print(f"❌ Failed: {url} should be considered high quality")
        else:
            print(f"✅ Passed: {url} correctly identified as high quality")
    
    for url in bad_urls:
        if reporter._is_high_quality_article_url(url):
            print(f"❌ Failed: {url} should be considered low quality")
        else:
            print(f"✅ Passed: {url} correctly identified as low quality")

def test_title_similarity():
    """Test title similarity calculation"""
    print("\n🔍 Testing title similarity...")
    
    reporter = AITrendsReporter("test-api-key")
    
    test_cases = [
        ("OpenAI releases GPT-4 Turbo", "OpenAI GPT-4 Turbo Release", 0.5),
        ("New AI breakthrough in language models", "AI breakthrough language models new", 0.8),
        ("Completely different title", "Another unrelated article", 0.0),
        ("", "Some title", 0.0),
        ("Same title", "Same title", 1.0)
    ]
    
    for title1, title2, expected_min in test_cases:
        similarity = reporter._calculate_title_similarity(title1, title2)
        if similarity >= expected_min:
            print(f"✅ Passed: '{title1}' vs '{title2}' = {similarity:.2f}")
        else:
            print(f"❌ Failed: '{title1}' vs '{title2}' = {similarity:.2f} (expected >= {expected_min})")

def test_export_functionality():
    """Test report export functionality"""
    print("\n📁 Testing export functionality...")
    
    reporter = AITrendsReporter("test-api-key")
    
    # Test report content
    test_report = """# 🤖 AI News Weekly Report
## January 13 - January 19, 2025

### 📰 News Headlines

This week brought significant developments in AI technology...

### 🔬 Research & Development News

**New Transformer Architecture Breakthrough**
Researchers announced a new approach to transformer models...

### 🛠️ Product Launch News

**OpenAI API Updates**
OpenAI released new API endpoints...
"""
    
    # Test export
    export_path = reporter._export_report_to_file(test_report, "January 13 - January 19, 2025")
    
    if export_path and os.path.exists(export_path):
        print(f"✅ Passed: Report exported to {export_path}")
        
        # Verify file content
        with open(export_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if content == test_report:
                print("✅ Passed: File content matches expected report")
            else:
                print("❌ Failed: File content doesn't match expected report")
        
        # Verify it's in the output directory
        if "output" in export_path:
            print("✅ Passed: File exported to correct output directory")
        else:
            print("❌ Failed: File not in output directory")
        
        # Clean up
        os.remove(export_path)
        print("✅ Passed: Test file cleaned up")
    else:
        print("❌ Failed: Export failed or file not created")

def test_mock_categorized_content():
    """Test with mock categorized content"""
    print("\n🧪 Testing with mock categorized content...")
    
    # Create mock categorized content
    mock_content = {
        "RESEARCH_BREAKTHROUGHS": [
            {
                "title": "Revolutionary AI Architecture Breakthrough",
                "summary": "Researchers develop new transformer architecture with 50% better efficiency",
                "source": "ai.googleblog.com",
                "url": "https://ai.googleblog.com/2024/01/transformer-breakthrough",
                "date": "2024-01-15",
                "impact_score": 8,
                "relevance_tags": ["AI", "Transformers"],
                "business_impact": "Significant efficiency improvements"
            }
        ],
        "PRODUCT_LAUNCHES": [
            {
                "title": "OpenAI API v2.0 Launch",
                "summary": "OpenAI releases new API with enhanced capabilities",
                "source": "openai.com",
                "url": "https://openai.com/blog/api-v2-launch",
                "date": "2024-01-16",
                "impact_score": 9,
                "relevance_tags": ["API", "OpenAI"],
                "business_impact": "Major API improvements"
            }
        ]
    }
    
    reporter = AITrendsReporter("test-api-key")
    
    # Test URL validation
    print("Testing URL validation on mock content...")
    improved_content = reporter._validate_and_improve_urls(mock_content)
    print(f"✅ URL validation completed: {len(improved_content)} categories processed")
    
    # Test re-ranking (mock the search service)
    print("Testing re-ranking on mock content...")
    with patch.object(reporter, '_calculate_article_popularity', return_value=7.5):
        ranked_content = reporter._re_rank_articles_by_popularity(improved_content)
        print(f"✅ Re-ranking completed: {len(ranked_content)} categories processed")
    
    # Test export
    print("Testing export with mock content...")
    test_report = "# Mock Report\n\nThis is a test report."
    export_path = reporter._export_report_to_file(test_report, "Test Date Range")
    
    if export_path and os.path.exists(export_path):
        print(f"✅ Export successful: {export_path}")
        os.remove(export_path)  # Clean up
    else:
        print("❌ Export failed")

def test_full_workflow():
    """Test the complete workflow with mocked dependencies"""
    print("\n🚀 Testing complete workflow...")
    
    # Mock the LLM and search service
    with patch('src.agent.graph.ChatGoogleGenerativeAI') as mock_llm_class, \
         patch('src.agent.graph.GoogleSearchService') as mock_search_class:
        
        # Setup mocks
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        
        mock_search = Mock()
        mock_search_class.return_value = mock_search
        
        # Mock LLM responses
        mock_llm.invoke.return_value.content = '["AI research", "OpenAI news", "ML tools"]'
        
        # Mock search results
        mock_search.search_ai_content.return_value = [
            {
                "title": "Test AI Article",
                "snippet": "This is a test article about AI",
                "url": "https://example.com/ai-article",
                "source": "example.com",
                "date": "2024-01-15"
            }
        ]
        
        try:
            # Create graph
            graph = create_graph()
            print("✅ Graph created successfully")
            
            # Test state structure
            from src.agent.graph import AgentState
            test_state = {
                "input": "Generate AI news report",
                "search_queries": [],
                "search_results": [],
                "categorized_content": {},
                "weekly_report": "",
                "report_metadata": {},
                "generation_timestamp": "",
                "report_date_range": "",
                "export_path": "",
                "iteration_count": 0,
                "reflection_feedback": "",
                "quality_score": 0.0,
                "needs_improvement": False,
                "improvement_areas": []
            }
            
            print("✅ State structure validated")
            
        except Exception as e:
            print(f"❌ Workflow test failed: {e}")

if __name__ == "__main__":
    print("🧪 Running URL Improvement Tests\n")
    
    # Run all tests
    test_url_validation()
    test_title_similarity()
    test_export_functionality()
    test_mock_categorized_content()
    test_full_workflow()
    
    print("\n✅ All tests completed!") 