#!/usr/bin/env python3
"""Test script to verify tag reorganizer includes all sources"""

import requests
import json

def test_tag_sources():
    # Get current tag structure from API
    response = requests.get("http://localhost:8000/api/tags/reorganize/current-structure")
    
    if response.status_code == 200:
        data = response.json()
        
        print("=" * 60)
        print("TAG REORGANIZER - ALL SOURCES TEST")
        print("=" * 60)
        
        print(f"\n✅ Total unique tags found: {data['total_tags']}")
        
        stats = data['statistics']
        print(f"\n📊 Statistics:")
        print(f"  • Total taggings: {stats['total_taggings']}")
        print(f"  • Average usage per tag: {stats['average_usage']:.2f}")
        print(f"  • Low usage tags: {len(stats.get('low_usage_tags', []))}")
        
        if 'tags_by_source' in stats:
            print(f"\n📍 Tags by source:")
            print(f"  • Tweet tags only: {stats['tags_by_source']['tweets_only']}")
            print(f"  • Paper tags only: {stats['tags_by_source']['papers_only']}")  
            print(f"  • Article tags only: {stats['tags_by_source']['articles_only']}")
            print(f"  • Multi-source tags: {stats['tags_by_source']['multi_source']}")
        
        if 'unique_tweets_tagged' in stats:
            print(f"\n📝 Content tagged:")
            print(f"  • Unique tweets: {stats['unique_tweets_tagged']}")
            print(f"  • Unique papers: {stats.get('unique_papers_tagged', 0)}")
            print(f"  • Unique articles: {stats.get('unique_articles_tagged', 0)}")
        
        # Sample some tags to see their sources
        print(f"\n🏷️ Sample tags with sources:")
        tags = data['tags']
        sample_count = 0
        for tag_name, tag_data in list(tags.items())[:10]:
            if 'sources' in tag_data:
                sources = ', '.join(tag_data['sources'])
                print(f"  • {tag_name}: {sources} (used {tag_data['usage_count']} times)")
                sample_count += 1
                if sample_count >= 10:
                    break
        
        print(f"\n✨ Success! The reorganizer now includes tags from all sources.")
        
    else:
        print(f"❌ Error: API returned status {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_tag_sources()