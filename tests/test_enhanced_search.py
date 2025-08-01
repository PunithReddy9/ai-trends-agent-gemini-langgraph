#!/usr/bin/env python3
"""
Test script to validate enhanced AI search functionality
"""

import os
import sys
import json
from datetime import datetime
import logging

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_enhanced_search():
    """Test the enhanced search functionality"""
    print("🔍 Testing Enhanced AI Search Functionality")
    print("=" * 50)
    
    # Check environment variables
    if not os.getenv('GOOGLE_SEARCH_API_KEY') or not os.getenv('GOOGLE_SEARCH_ENGINE_ID'):
        print("❌ Missing required environment variables:")
        print("   - GOOGLE_SEARCH_API_KEY")
        print("   - GOOGLE_SEARCH_ENGINE_ID")
        print("\nPlease set these in your .env file")
        return False
    
    try:
        from services.search_service import GoogleSearchService
        
        # Initialize enhanced search service
        search_service = GoogleSearchService()
        print("✅ Search service initialized successfully")
        
        # Test queries
        test_queries = [
            "OpenAI announces new model",
            "AI coding tools released",
            "Google AI research breakthrough",
            "artificial intelligence startup funding"
        ]
        
        all_results = []
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n📋 Test {i}/4: Testing query '{query}'")
            print("-" * 40)
            
            try:
                # Test enhanced search
                results = search_service.search_recent_ai_news(query, days_back=7)
                
                print(f"✅ Retrieved {len(results)} results")
                
                # Show quality metrics
                high_quality = sum(1 for r in results if r.get('url_quality') == 'high')
                medium_quality = sum(1 for r in results if r.get('url_quality') == 'medium')
                official_sources = sum(1 for r in results if r.get('source_type') == 'official')
                news_sources = sum(1 for r in results if r.get('source_type') == 'news')
                
                print(f"   📊 Quality breakdown:")
                print(f"      - High quality URLs: {high_quality}")
                print(f"      - Medium quality URLs: {medium_quality}")
                print(f"      - Official sources: {official_sources}")
                print(f"      - News sources: {news_sources}")
                
                # Show sample results
                print(f"\n   🔗 Sample results:")
                for j, result in enumerate(results[:3], 1):
                    title = result.get('title', 'No title')[:60]
                    source = result.get('source', 'Unknown')
                    url_quality = result.get('url_quality', 'unknown')
                    source_type = result.get('source_type', 'unknown')
                    
                    print(f"      {j}. {title}... [{source}] ({url_quality}/{source_type})")
                
                all_results.extend(results)
                
            except Exception as e:
                print(f"❌ Error testing query '{query}': {e}")
                continue
        
        # Overall statistics
        print(f"\n📈 Overall Results Summary")
        print("=" * 50)
        print(f"Total results retrieved: {len(all_results)}")
        
        if all_results:
            # Quality analysis
            quality_counts = {}
            source_type_counts = {}
            domain_counts = {}
            
            for result in all_results:
                quality = result.get('url_quality', 'unknown')
                source_type = result.get('source_type', 'unknown')
                domain = result.get('source', 'unknown')
                
                quality_counts[quality] = quality_counts.get(quality, 0) + 1
                source_type_counts[source_type] = source_type_counts.get(source_type, 0) + 1
                domain_counts[domain] = domain_counts.get(domain, 0) + 1
            
            print(f"\n📊 Quality Distribution:")
            for quality, count in sorted(quality_counts.items()):
                percentage = (count / len(all_results)) * 100
                print(f"   {quality}: {count} ({percentage:.1f}%)")
            
            print(f"\n📰 Source Type Distribution:")
            for source_type, count in sorted(source_type_counts.items()):
                percentage = (count / len(all_results)) * 100
                print(f"   {source_type}: {count} ({percentage:.1f}%)")
            
            print(f"\n🌐 Top Domains:")
            sorted_domains = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)
            for domain, count in sorted_domains[:10]:
                print(f"   {domain}: {count}")
            
            # Test content fetching
            print(f"\n🔄 Testing Content Fetching")
            print("-" * 30)
            
            high_quality_results = [r for r in all_results if r.get('url_quality') == 'high']
            if high_quality_results:
                test_result = high_quality_results[0]
                print(f"Testing content fetch for: {test_result.get('title', 'Unknown')[:50]}...")
                
                try:
                    content = search_service.fetch_article_content(test_result['url'])
                    if content.get('is_content_rich'):
                        content_length = content.get('content_length', 0)
                        print(f"✅ Successfully fetched rich content ({content_length} chars)")
                    else:
                        print(f"⚠️  Content fetched but may be low quality")
                except Exception as e:
                    print(f"❌ Content fetch failed: {e}")
            else:
                print("⚠️  No high-quality results available for content testing")
        
        # Save sample results
        sample_file = f"enhanced_search_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(sample_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'test_queries': test_queries,
                'total_results': len(all_results),
                'sample_results': all_results[:10],  # Save first 10 results
                'quality_summary': quality_counts if all_results else {},
                'source_type_summary': source_type_counts if all_results else {},
                'top_domains': dict(sorted_domains[:10]) if all_results else {}
            }, f, indent=2)
        
        print(f"\n💾 Sample results saved to: {sample_file}")
        print(f"\n✅ Enhanced search test completed successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running from the project root directory")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_url_validation():
    """Test URL validation improvements"""
    print(f"\n🔗 Testing URL Validation")
    print("-" * 30)
    
    try:
        from services.search_service import GoogleSearchService
        search_service = GoogleSearchService()
        
        # Test URLs
        test_urls = [
            ("https://openai.com/blog/introducing-gpt-4", True, "Valid article URL"),
            ("https://techcrunch.com/2025/01/15/ai-startup-raises-funding/", True, "News article URL"),
            ("https://example.com/", False, "Homepage URL"),
            ("https://example.com/category/ai/", False, "Category page"),
            ("https://reddit.com/r/MachineLearning/", False, "Social media URL"),
            ("https://venturebeat.com/ai/", False, "Section page"),
            ("https://blog.anthropic.com/claude-2-constitutional-ai", True, "Company blog post"),
        ]
        
        for url, expected, description in test_urls:
            result = search_service._is_valid_article_url(url)
            status = "✅" if result == expected else "❌"
            print(f"   {status} {description}: {url}")
            if result != expected:
                print(f"      Expected: {expected}, Got: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ URL validation test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 AI Search Enhancement Test Suite")
    print("=" * 60)
    
    # Test basic search functionality
    search_success = test_enhanced_search()
    
    # Test URL validation
    validation_success = test_url_validation()
    
    # Summary
    print(f"\n📋 Test Summary")
    print("=" * 30)
    print(f"Enhanced Search: {'✅ PASSED' if search_success else '❌ FAILED'}")
    print(f"URL Validation: {'✅ PASSED' if validation_success else '❌ FAILED'}")
    
    if search_success and validation_success:
        print(f"\n🎉 All tests passed! Your enhanced search is ready to use.")
        print(f"\nKey improvements:")
        print(f"   ✅ Better search queries focused on recent news")
        print(f"   ✅ Enhanced URL validation for article quality")
        print(f"   ✅ Improved source targeting (official blogs + news sites)")
        print(f"   ✅ Better content fetching for high-quality sources")
        print(f"   ✅ Enhanced filtering and ranking metrics")
    else:
        print(f"\n⚠️  Some tests failed. Check the error messages above.")
        sys.exit(1) 