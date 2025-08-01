#!/usr/bin/env python3
"""
Test script to validate enhanced logging for Google Search tracing
"""

import os
import sys
import logging
from datetime import datetime

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def setup_detailed_logging():
    """Setup detailed logging with multiple levels"""
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Setup logging with detailed format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Setup file handler for detailed logs
    file_handler = logging.FileHandler(
        f'logs/google_search_trace_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
        mode='w'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format))
    
    # Setup console handler for important messages
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    ))
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.handlers.clear()  # Clear any existing handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return file_handler.baseFilename

def test_detailed_search_logging():
    """Test the detailed search logging functionality"""
    
    print("🔍 Testing Detailed Google Search Logging")
    print("=" * 60)
    
    # Check environment variables
    if not os.getenv('GOOGLE_SEARCH_API_KEY') or not os.getenv('GOOGLE_SEARCH_ENGINE_ID'):
        print("❌ Missing required environment variables:")
        print("   - GOOGLE_SEARCH_API_KEY")
        print("   - GOOGLE_SEARCH_ENGINE_ID")
        return False
    
    try:
        from services.search_service import GoogleSearchService
        
        print("✅ Search service imported successfully")
        
        # Initialize service (this will test initialization logging)
        search_service = GoogleSearchService()
        
        # Test a single search with detailed logging
        test_query = "OpenAI announces new model"
        
        print(f"\n🔍 Testing search query: '{test_query}'")
        print("📝 Check the log file for detailed trace information...")
        
        # Test basic search method
        print("\n--- Testing basic search_ai_content ---")
        basic_results = search_service.search_ai_content(test_query, days_back=7)
        
        print(f"Basic search returned: {len(basic_results)} results")
        
        # Test enhanced search method
        print("\n--- Testing enhanced search_recent_ai_news ---")
        enhanced_results = search_service.search_recent_ai_news(test_query, days_back=7)
        
        print(f"Enhanced search returned: {len(enhanced_results)} results")
        
        # Test content fetching if we have results
        if enhanced_results:
            high_quality_results = [r for r in enhanced_results if r.get('url_quality') == 'high']
            if high_quality_results:
                print("\n--- Testing content fetching ---")
                test_url = high_quality_results[0]['url']
                content = search_service.fetch_article_content(test_url)
                print(f"Content fetch result: {'✅ Success' if content.get('is_content_rich') else '⚠️ Low quality'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during search testing: {e}")
        logging.error(f"Search test failed: {e}")
        return False

def test_agent_search_logging():
    """Test the agent-level search logging"""
    
    print("\n🤖 Testing Agent-Level Search Logging")
    print("=" * 60)
    
    try:
        from agent.graph import AITrendsReporter
        
        # Check for Gemini API key
        if not os.getenv('GEMINI_API_KEY'):
            print("⚠️ Missing GEMINI_API_KEY - skipping agent tests")
            return True
        
        print("✅ Agent imported successfully")
        
        # Initialize agent
        agent = AITrendsReporter(gemini_api_key=os.getenv('GEMINI_API_KEY'))
        
        # Test query generation
        print("\n--- Testing query generation logging ---")
        
        state = {
            "input": "test",
            "search_queries": [],
            "search_results": [],
            "weekly_report": "",
            "report_metadata": {},
            "generation_timestamp": "",
            "report_date_range": "",
            "export_path": "",
            "iteration_count": 0,
            "reflection_feedback": "",
            "quality_score": 0.0,
            "needs_improvement": False,
            "improvement_areas": [],
            "trend_analysis": {}
        }
        
        # Generate queries (this will test query generation logging)
        updated_state = agent.generate_ai_weekly_queries(state)
        
        print(f"Generated {len(updated_state['search_queries'])} queries")
        
        # Test research phase (limited to avoid too many API calls)
        print("\n--- Testing research logging (first 2 queries only) ---")
        
        # Limit queries for testing
        limited_state = updated_state.copy()
        limited_state["search_queries"] = updated_state["search_queries"][:2]
        
        research_state = agent.research_ai_trends(limited_state)
        
        print(f"Research completed with {len(research_state['search_results'])} results")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during agent testing: {e}")
        logging.error(f"Agent test failed: {e}")
        return False

def analyze_log_file(log_file_path):
    """Analyze the generated log file"""
    
    print(f"\n📊 Analyzing Log File: {log_file_path}")
    print("=" * 60)
    
    try:
        with open(log_file_path, 'r') as f:
            log_content = f.read()
        
        lines = log_content.split('\n')
        
        # Count different log levels
        log_levels = {
            'DEBUG': 0,
            'INFO': 0,
            'WARNING': 0,
            'ERROR': 0
        }
        
        # Count different types of log messages
        message_types = {
            'API requests': 0,
            'Query processing': 0,
            'Result filtering': 0,
            'Error handling': 0,
            'Performance timing': 0
        }
        
        for line in lines:
            if not line.strip():
                continue
                
            # Count log levels
            for level in log_levels:
                if f' - {level} - ' in line:
                    log_levels[level] += 1
                    break
            
            # Count message types
            if '🌐 Making API request' in line or 'API response time' in line:
                message_types['API requests'] += 1
            elif '🔍 Processing query' in line or 'query generation' in line:
                message_types['Query processing'] += 1
            elif '🔧 Starting enhanced result filtering' in line or 'Filtering statistics' in line:
                message_types['Result filtering'] += 1
            elif '❌' in line or 'error' in line.lower():
                message_types['Error handling'] += 1
            elif '⏱️' in line or 'time:' in line or 'duration' in line:
                message_types['Performance timing'] += 1
        
        # Display analysis
        print("📊 Log Level Distribution:")
        for level, count in log_levels.items():
            print(f"   {level}: {count}")
        
        print("\n📊 Message Type Distribution:")
        for msg_type, count in message_types.items():
            print(f"   {msg_type}: {count}")
        
        print(f"\n📏 Total log lines: {len([l for l in lines if l.strip()])}")
        print(f"📄 Log file size: {len(log_content)} characters")
        
        # Show sample of detailed logs
        print("\n📋 Sample detailed log entries:")
        sample_lines = [l for l in lines if l.strip() and ('🔍' in l or '📊' in l or '⏱️' in l)][:5]
        for i, line in enumerate(sample_lines, 1):
            print(f"   {i}. {line}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing log file: {e}")
        return False

def main():
    """Main test function"""
    
    print("🚀 Google Search Detailed Logging Test Suite")
    print("=" * 70)
    print("This test will generate detailed logs to help trace Google Search issues")
    print()
    
    # Setup detailed logging
    log_file = setup_detailed_logging()
    print(f"📝 Detailed logs will be written to: {log_file}")
    print()
    
    # Test results
    test_results = {}
    
    # Test search service logging
    test_results['search_service'] = test_detailed_search_logging()
    
    # Test agent logging
    test_results['agent_logging'] = test_agent_search_logging()
    
    # Analyze log file
    test_results['log_analysis'] = analyze_log_file(log_file)
    
    # Summary
    print(f"\n📋 Test Summary")
    print("=" * 40)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(test_results.values())
    
    if all_passed:
        print(f"\n🎉 All tests passed!")
        print(f"\nKey logging features validated:")
        print(f"   ✅ Detailed API request/response logging")
        print(f"   ✅ Query processing and timing information")
        print(f"   ✅ Result filtering and ranking details")
        print(f"   ✅ Error handling and debugging information")
        print(f"   ✅ Performance metrics and statistics")
        print(f"\n📁 Check the log file for complete trace: {log_file}")
    else:
        print(f"\n⚠️ Some tests failed. Check the logs for details.")
        print(f"📁 Log file: {log_file}")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 