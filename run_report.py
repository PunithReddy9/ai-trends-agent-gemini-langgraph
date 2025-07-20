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
    
    # Check for required environment variables
    if not os.getenv("GEMINI_API_KEY"):
        print("Error: GEMINI_API_KEY environment variable not set")
        print("Please set your Gemini API key in the .env file or environment")
        sys.exit(1)
    
    if not os.getenv("GOOGLE_SEARCH_API_KEY") or not os.getenv("GOOGLE_SEARCH_ENGINE_ID"):
        print("Error: Google Search API credentials not set")
        print("Please set GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_ENGINE_ID in the .env file or environment")
        sys.exit(1)
    
    try:
        print("🚀 Starting AI Trends Report Generation...")
        print("=" * 60)
        
        # Create the graph
        graph = create_graph()
        
        # Run the agent
        print("📊 Executing agent workflow...")
        result = graph.invoke({"input": "Generate weekly AI trends report"})
        
        # Extract the report content
        if "weekly_report" not in result:
            print("❌ Error: No report generated")
            sys.exit(1)
        
        report_content = result["weekly_report"]
        metadata = result.get("report_metadata", {})
        generation_timestamp = result.get("generation_timestamp", datetime.now().isoformat())
        
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
        
        print("✅ Report Generation Complete!")
        print("=" * 60)
        print(f"📁 Report saved to: {output_path}")
        print(f"📅 Generated at: {generation_timestamp}")
        
        if metadata:
            print(f"📊 Total developments: {metadata.get('total_developments', 'N/A')}")
            print(f"🏷️  Categories covered: {metadata.get('categories_covered', 'N/A')}")
            if metadata.get('trending_topics'):
                print(f"🔥 Trending topics: {', '.join(metadata['trending_topics'][:5])}")
        
        print("\n🎉 Ready to send as email newsletter!")
        
    except Exception as e:
        print(f"❌ Error generating report: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 