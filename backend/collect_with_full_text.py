#!/usr/bin/env python3
"""
Collect tweets with full text expansion for retweets
Run this to ensure all new tweets are collected with complete text
"""

import sys
import os
from datetime import datetime, timedelta, timezone

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.collectors.twitter_collector import TwitterCollector
from app.models import get_db, Tweet

def main():
    print("=" * 60)
    print("🐦 Twitter Collection with Full Retweet Text")
    print("=" * 60)
    print("This collector ensures retweets are saved with full text")
    print()
    
    # Get database session
    db = next(get_db())
    
    # Check last collection time
    latest_tweet = db.query(Tweet).order_by(Tweet.created_at.desc()).first()
    
    if latest_tweet:
        time_since = datetime.now(timezone.utc) - latest_tweet.created_at
        print(f"📅 Last tweet collected: {time_since.total_seconds() / 3600:.1f} hours ago")
        print(f"   From: @{latest_tweet.author_username}")
        print(f"   Time: {latest_tweet.created_at}")
        print()
        
        # Collect tweets since the last one
        collector = TwitterCollector(db)
        print("🔄 Collecting new tweets since last run...")
        
        # Add a small buffer to avoid missing tweets
        since_time = latest_tweet.created_at - timedelta(minutes=5)
        new_count = collector.collect_since_timestamp(since_time)
    else:
        print("📊 No tweets in database. Collecting last 7 days...")
        collector = TwitterCollector(db)
        new_count = collector.collect_historical_tweets(days=7)
    
    print()
    print("=" * 60)
    
    if new_count > 0:
        print(f"✅ Successfully collected {new_count} new tweets with full text!")
        
        # Show sample of retweets to verify
        recent_retweets = db.query(Tweet).filter(
            Tweet.text.like('RT @%')
        ).order_by(Tweet.created_at.desc()).limit(3).all()
        
        if recent_retweets:
            print("\n📝 Sample of recent retweets (showing full text):")
            for rt in recent_retweets:
                print(f"\n  @{rt.author_username}:")
                if len(rt.text) > 200:
                    print(f"  {rt.text[:200]}...")
                    print(f"  [Full length: {len(rt.text)} chars]")
                else:
                    print(f"  {rt.text}")
    else:
        print("ℹ️  No new tweets found")
    
    print("=" * 60)
    
    # Close database
    db.close()

if __name__ == "__main__":
    main()