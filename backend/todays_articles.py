#!/usr/bin/env python3
"""
Simple script to collect today's Substack articles
Usage: python todays_articles.py [--forwarded-only]
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.collectors.gmail_substack_collector import GmailSubstackCollector


def main():
    """Collect today's articles with a simple Gmail query"""
    
    # Check command line arguments
    forwarded_only = '--forwarded-only' in sys.argv or '--forwarded' in sys.argv
    
    # Build today's date filter
    today = datetime.now(timezone.utc)
    today_str = today.strftime('%Y/%m/%d')
    tomorrow_str = today.strftime('%Y/%m/%d')  # Will be adjusted by adding 1
    
    # Gmail date format: after:2025/1/11
    date_query = f"after:{today_str}"
    
    if forwarded_only:
        print("\n📧 Collecting ONLY forwarded articles from today...")
        # Query for forwarded emails only
        query = f"(from:siegfried.handschuh@unisg.ch OR (from:me to:me)) AND substack AND {date_query}"
    else:
        print("\n📧 Collecting ALL articles from today (forwarded + direct)...")
        # Query for all Substack emails
        query = f"(from:substack.com OR from:siegfried.handschuh@unisg.ch OR (from:me to:me AND substack)) AND {date_query}"
    
    print(f"📅 Date: {today.strftime('%Y-%m-%d')}")
    print(f"🔍 Query: {query}\n")
    
    # Initialize collector and run
    collector = GmailSubstackCollector()
    
    try:
        articles_count = collector.collect_newsletters(
            query=query,
            max_results=50  # Should be enough for one day
        )
        
        print(f"\n✅ Collection complete!")
        print(f"📊 Articles processed: {articles_count}")
        
        if articles_count == 0:
            print("\n💡 Tip: No new articles found. They may already be in the database.")
            print("   Check the Substack dashboard to see existing articles.")
        
    except Exception as e:
        print(f"\n❌ Error during collection: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("=" * 60)
    print("  SmartTrendTracer - Today's Article Collector")
    print("=" * 60)
    
    main()
    
    print("\n" + "=" * 60)
    print("  Done! Check http://localhost:3000/substack")
    print("=" * 60)