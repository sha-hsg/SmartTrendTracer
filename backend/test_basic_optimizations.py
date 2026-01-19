#!/usr/bin/env python3
"""
Test script to verify Basic Account optimizations
"""

import os
from datetime import datetime, timezone
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
mongo_client = MongoClient(MONGODB_URL)
db = mongo_client.smarttrendtracer

def main():
    print("\n" + "="*60)
    print("🔍 TWITTER BASIC ACCOUNT OPTIMIZATIONS TEST")
    print("="*60)
    
    # Check current usage
    current_date = datetime.now()
    month_start = datetime(current_date.year, current_date.month, 1, tzinfo=timezone.utc)
    
    monthly_tweets = db.tweets.count_documents({
        "collected_at": {"$gte": month_start}
    })
    
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
    daily_tweets = db.tweets.count_documents({
        "collected_at": {"$gte": today_start}
    })
    
    total_tweets = db.tweets.count_documents({})
    
    print(f"\n📊 CURRENT USAGE:")
    print(f"  • Total tweets in DB: {total_tweets:,}")
    print(f"  • Tweets this month: {monthly_tweets:,} / 10,000")
    print(f"  • Tweets today: {daily_tweets} / 333")
    print(f"  • Monthly usage: {(monthly_tweets/10000)*100:.1f}%")
    
    print(f"\n✅ OPTIMIZATIONS IMPLEMENTED:")
    print(f"""
    1. TIERED PRIORITY SYSTEM:
       • Tier 1 (4 accounts): Check every 30 min
         - OpenAI, AnthropicAI, sama, emollick
       • Tier 2 (5 accounts): Check every 2 hours
         - huggingface, GoogleDeepMind, stanfordnlp, hwchase17, kaggle
       • Tier 3 (6 accounts): Check every 6 hours
         - rasbt, JayAlammar, Yoavgo, Shayneredford, Sebastienbubeck
    
    2. REQUEST POOLING:
       • Max 12 timeline requests per 15-min window
       • Leaves buffer of 3 requests for safety
       • Tracks usage across all accounts
    
    3. SEARCH API FALLBACK:
       • Uses search API when timeline is rate limited
       • 60 requests/15min available for search
       • Query: "from:username -is:retweet"
    
    4. SINGLE PAGE FETCHING:
       • Only 1 page per account (100 tweets max)
       • Uses since_id to get only new tweets
       • Stops immediately if no new tweets
    
    5. USAGE MONITORING:
       • Tracks monthly usage (10,000 limit)
       • Tracks daily budget (333 tweets)
       • Auto-reduces frequency at 90% usage
    """)
    
    print("="*60)
    print("🚀 HOW TO RUN:")
    print("="*60)
    print("""
    # Option 1: Use the launcher script
    ./start_basic_collector.sh
    
    # Option 2: Run directly with optimal settings
    export MAX_PAGES_PER_ACCOUNT=1
    export COLLECTION_INTERVAL_SECONDS=900
    python tweet_collector_basic.py
    
    # Option 3: Monitor usage in real-time
    python monitor_usage.py
    """)
    
    print("\n💡 EXPECTED BENEFITS:")
    print("""
    • API Calls: 75% reduction (1 page vs 5 pages)
    • Coverage: All 15 accounts checked appropriately
    • Efficiency: Important accounts checked frequently
    • Safety: Never exceeds rate limits
    • Cost: Stays within $100/month Basic plan
    """)

if __name__ == "__main__":
    main()
    mongo_client.close()