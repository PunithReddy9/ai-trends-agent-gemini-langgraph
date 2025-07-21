#!/usr/bin/env python3
"""
Standalone AI Trends Report Generator
Run this script to generate a weekly AI trends report and save it to output/
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, rely on system environment variables
    pass

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from agent.graph import create_graph

def main():
    """Generate AI trends report and save to output folder"""
    
    # Set up logging first so we can see all workflow steps
    import logging
    
    # Clear any existing handlers to avoid conflicts
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',  # Simplified format to show clean workflow messages
        handlers=[
            logging.StreamHandler(sys.stdout)
        ],
        force=True  # Force reconfiguration
    )
    
    print("🚀 Starting AI Trends Report Generation...")
    print("=" * 60)
    
    # Show system information
    print(f"⏰ Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Working Directory: {os.getcwd()}")
    
    # Check for required environment variables
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ Error: GEMINI_API_KEY environment variable not set")
        print("Please set your Gemini API key in the .env file or environment")
        sys.exit(1)
    
    if not os.getenv("GOOGLE_SEARCH_API_KEY") or not os.getenv("GOOGLE_SEARCH_ENGINE_ID"):
        print("❌ Error: Google Search API credentials not set")
        print("Please set GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_ENGINE_ID in the .env file or environment")
        sys.exit(1)
    
    # Show API configuration status
    print("🔑 API Configuration:")
    gemini_key = os.getenv("GEMINI_API_KEY")
    google_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
    
    print(f"   ✅ Gemini API Key: {gemini_key[:8]}...{gemini_key[-4:] if len(gemini_key) > 12 else '***'}")
    print(f"   ✅ Google API Key: {google_key[:8]}...{google_key[-4:] if len(google_key) > 12 else '***'}")
    print(f"   ✅ Search Engine ID: {search_engine_id}")
    
    try:
        print("")
        print("🏗️  INITIALIZING WORKFLOW")
        print("=" * 60)
        print("📋 Workflow Overview:")
        print("   1. Generate Queries - Create optimized search terms")
        print("   2. Research Trends - Search across AI news sources")
        print("   3. Analyze Trends - Process and categorize findings")
        print("   4. Quality Reflection - Evaluate content completeness")
        print("   5. Improve Search (if needed) - Refine strategy")
        print("   6. Generate Report - Create final weekly report")
        print("")
        print("🔧 Building LangGraph workflow...")
        
        # Create the graph
        graph = create_graph()
        
        print("✅ Workflow initialized successfully!")
        print("")
        print("🚀 STARTING EXECUTION")
        print("=" * 60)
        
        # Run the agent
        result = graph.invoke({"input": "Generate weekly AI trends report"})
        
        print("")
        print("🏁 WORKFLOW COMPLETED")
        print("=" * 60)
        
        # Extract the report content
        if "weekly_report" not in result:
            print("❌ Error: No report generated")
            sys.exit(1)
        
        report_content = result["weekly_report"]
        metadata = result.get("report_metadata", {})
        generation_timestamp = result.get("generation_timestamp", datetime.now().isoformat())
        search_results = result.get("search_results", [])
        trend_analysis = result.get("trend_analysis", {})
        
        # Show execution summary
        print("📊 EXECUTION SUMMARY:")
        print(f"   📈 Search Results Found: {len(search_results)}")
        
        # Show source breakdown
        if search_results:
            sources = {}
            for article in search_results:
                domain = article.get('link', '').split('/')[2] if '//' in article.get('link', '') else 'unknown'
                sources[domain] = sources.get(domain, 0) + 1
            
            print(f"   🌐 Unique Sources: {len(sources)}")
            print(f"   📰 Top Sources:")
            for i, (domain, count) in enumerate(sorted(sources.items(), key=lambda x: x[1], reverse=True)[:5], 1):
                print(f"      {i}. {domain}: {count} articles")
        
        # Show trend analysis summary
        if trend_analysis and 'trends' in trend_analysis:
            trends = trend_analysis['trends']
            print(f"   🎯 Trends Identified: {len(trends)}")
            if trends:
                print(f"   📝 Trend Headlines:")
                for i, trend in enumerate(trends[:5], 1):
                    headline = trend.get('headline', 'Unknown Trend')
                    print(f"      {i}. {headline}")
        
        # Report statistics
        report_length = len(report_content)
        word_count = len(report_content.split())
        
        print(f"   📄 Report Length: {report_length:,} characters")
        print(f"   📝 Word Count: {word_count:,} words")
        
        # Create output filename with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        filename = f"AI-Trends-Report-{timestamp}.md"
        
        # Ensure output directory exists
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)
        
        # Save the report
        output_path = output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print("")
        print("✅ Report Generation Complete!")
        print("=" * 60)
        print(f"📁 Report saved to: {output_path}")
        print(f"📅 Generated at: {generation_timestamp}")
        
        print("\n🎉 Ready to send as email newsletter!")
        
    except Exception as e:
        print(f"❌ Error generating report: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 