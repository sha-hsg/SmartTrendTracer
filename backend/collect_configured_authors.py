#!/usr/bin/env python3
"""
Collect Substack emails only from configured authors
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.collectors.selective_gmail_collector import SelectiveGmailCollector

if __name__ == "__main__":
    print("=" * 60)
    print("📧 Collecting Substack from Configured Authors Only")
    print("=" * 60)
    
    collector = SelectiveGmailCollector()
    
    # Show configuration
    print("\n📋 Configured Authors:")
    for author in collector.config.get('forwarded_authors', []):
        print(f"  • {author['name']} ({author['email']})")
    
    print("\n🔍 Starting collection...")
    articles = collector.collect_selective(max_results=150)
    
    print(f"\n✅ Collection complete!")
    print(f"   New articles: {articles}")