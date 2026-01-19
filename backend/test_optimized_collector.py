#!/usr/bin/env python3
"""
Test script to verify the optimized tweet collector functionality.
"""

import os
import sys
from datetime import datetime, timezone
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment
load_dotenv()

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
mongo_client = MongoClient(MONGODB_URL)
db = mongo_client.smarttrendtracer

def check_collection_state():
    """Check the current collection state."""
    print("\n" + "="*60)
    print("📊 COLLECTION STATE CHECK")
    print("="*60)
    
    # Get collection states
    states = list(db.collection_state.find())
    
    if not states:
        print("❌ No collection state found - will collect all tweets on first run")
        return
    
    print(f"✅ Found {len(states)} account states:\n")
    
    for state in states:
        account = state.get('key', state.get('_id', '')).replace('twitter_', '')
        last_tweet_id = state.get('last_tweet_id', 'None')
        last_run = state.get('last_run', 'Never')
        tweets_collected = state.get('tweets_collected', 0)
        
        if isinstance(last_run, datetime):
            # Ensure both datetimes are timezone-aware
            now = datetime.now(timezone.utc)
            if last_run.tzinfo is None:
                last_run = last_run.replace(tzinfo=timezone.utc)
            time_since = now - last_run
            last_run_str = f"{time_since.total_seconds()/3600:.1f} hours ago"
        else:
            last_run_str = "Never"
        
        print(f"  @{account}:")
        print(f"    • Last tweet ID: {last_tweet_id}")
        print(f"    • Last run: {last_run_str}")
        print(f"    • Last collection: {tweets_collected} tweets")

def check_tweet_stats():
    """Check tweet statistics."""
    print("\n" + "="*60)
    print("📈 TWEET STATISTICS")
    print("="*60)
    
    # Get total tweets
    total_tweets = db.tweets.count_documents({})
    print(f"Total tweets in database: {total_tweets}")
    
    # Get per-author stats
    pipeline = [
        {"$group": {
            "_id": "$author_username",
            "count": {"$sum": 1},
            "latest": {"$max": "$created_at"},
            "oldest": {"$min": "$created_at"}
        }},
        {"$sort": {"count": -1}}
    ]
    
    results = list(db.tweets.aggregate(pipeline))
    
    print(f"\nTweets by author:")
    for author in results:
        username = author['_id']
        count = author['count']
        latest = author['latest']
        oldest = author['oldest']
        
        if latest and oldest:
            date_range = f"{oldest.strftime('%Y-%m-%d')} to {latest.strftime('%Y-%m-%d')}"
        else:
            date_range = "Unknown"
        
        print(f"  @{username}: {count} tweets ({date_range})")

def explain_optimizations():
    """Explain the optimizations made."""
    print("\n" + "="*60)
    print("🚀 OPTIMIZATIONS IMPLEMENTED")
    print("="*60)
    
    print("""
1. ✅ SMART PAGINATION STOP
   - Stops fetching pages when 80%+ tweets are duplicates
   - Prevents wasting API calls on old tweets
   
2. ✅ MAX PAGES LIMIT
   - Maximum 5 pages per account (configurable)
   - Prevents excessive API usage
   - Set MAX_PAGES_PER_ACCOUNT env var to adjust
   
3. ✅ SINCE_ID TRACKING
   - Only fetches tweets newer than last collected
   - Dramatically reduces API calls for frequent collectors
   
4. ✅ EFFICIENT DUPLICATE DETECTION
   - Checks MongoDB before saving each tweet
   - Returns should_continue flag to stop early
   
Expected Behavior:
- First run: May fetch up to 5 pages (500 tweets)
- Subsequent runs: Usually 1-2 pages only (new tweets)
- When caught up: Often just 1 page with few/no new tweets
""")

def main():
    """Run all checks."""
    print("\n" + "="*60)
    print("🔍 TWEET COLLECTOR OPTIMIZATION TEST")
    print("="*60)
    
    check_collection_state()
    check_tweet_stats()
    explain_optimizations()
    
    print("\n" + "="*60)
    print("💡 NEXT STEPS")
    print("="*60)
    print("""
To test the optimized collector:

1. Run the collector:
   ./tweet_collector_service.py

2. Watch the logs for:
   - "📊 Found X/Y existing tweets (Z%), stopping pagination"
   - "📄 Reached max pages limit (5) for @username"
   - "🛑 Stopping pagination for @username - reached existing tweets"

3. The collector should now:
   - Use fewer API calls
   - Stop early when hitting known tweets
   - Never fetch more than 5 pages per account
""")

if __name__ == "__main__":
    main()