#!/usr/bin/env python3
"""
Test the startup collection feature that fills gaps since last run
"""
import sys
import os
from datetime import datetime, timedelta, timezone

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db, CollectionState, Tweet
from app.startup_collector import collect_tweets_since_last_run
from sqlalchemy import func

def test_startup_collection():
    print("🧪 Testing Startup Collection Feature")
    print("=" * 60)
    
    # Get database connection
    db = next(get_db())
    
    # 1. Check current collection state
    print("\n1. Checking collection state...")
    last_run = CollectionState.get_last_run(db)
    
    if last_run:
        time_diff = datetime.now(timezone.utc) - last_run
        hours_since = time_diff.total_seconds() / 3600
        print(f"   Last collection: {last_run.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"   Time since: {hours_since:.1f} hours ago")
    else:
        print("   No previous collection recorded (first run)")
    
    # 2. Show current database stats
    print("\n2. Current database statistics:")
    total_tweets = db.query(func.count(Tweet.id)).scalar()
    print(f"   Total tweets: {total_tweets}")
    
    # Get latest tweet per account
    account_stats = db.query(
        Tweet.author_username,
        func.max(Tweet.created_at).label('latest')
    ).group_by(Tweet.author_username).all()
    
    print("   Latest tweet per account:")
    for stat in account_stats:
        hours_ago = (datetime.now(timezone.utc) - stat.latest).total_seconds() / 3600
        status = "✅" if hours_ago < 24 else "⚠️"
        print(f"   {status} @{stat.author_username}: {hours_ago:.1f} hours ago")
    
    # 3. Simulate what would happen on startup
    print("\n3. Simulating startup collection...")
    print("   This is what will happen when the backend starts:")
    
    if last_run:
        since_time = last_run
    else:
        since_time = datetime.now(timezone.utc) - timedelta(days=7)
    
    print(f"   Will collect tweets since: {since_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    # 4. Actually run the startup collection
    user_input = input("\n   Do you want to run the startup collection now? (y/n): ")
    
    if user_input.lower() == 'y':
        print("\n4. Running startup collection...")
        db.close()  # Close our connection, let the function use its own
        
        # Run the actual startup collection
        new_tweets = collect_tweets_since_last_run()
        
        # Re-open connection to check results
        db = next(get_db())
        
        # Show new stats
        new_total = db.query(func.count(Tweet.id)).scalar()
        print(f"\n   Results:")
        print(f"   • New tweets collected: {new_tweets}")
        print(f"   • Total tweets now: {new_total}")
        
        # Check new collection state
        new_last_run = CollectionState.get_last_run(db)
        if new_last_run:
            print(f"   • Collection state updated: {new_last_run.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    else:
        print("\n4. Skipped startup collection")
    
    # 5. Test the gap-filling logic
    print("\n5. Gap-filling information:")
    print("   The system will automatically:")
    print("   • Check for gaps when the backend starts")
    print("   • Collect all tweets since the last shutdown")
    print("   • Maximum lookback: 7 days (Twitter API limit)")
    print("   • Regular collection: Every 30 minutes while running")
    
    db.close()
    
    print("\n" + "=" * 60)
    print("✅ Startup collection test complete!")
    print("\nHow it works:")
    print("1. When you start the backend with 'python run.py'")
    print("2. It automatically checks when it was last run")
    print("3. Collects all tweets since that time")
    print("4. Then continues with regular 30-minute collections")
    print("\nThis ensures you never miss tweets, even after being offline!")

if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv()
    
    if not os.getenv('TWITTER_BEARER_TOKEN'):
        print("❌ Error: TWITTER_BEARER_TOKEN not found in .env file")
        sys.exit(1)
    
    try:
        test_startup_collection()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()