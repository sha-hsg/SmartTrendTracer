#!/usr/bin/env python3
"""
Force collection of tweets (bypasses time checks)
"""
import sys
import os
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.collectors.twitter_collector import TwitterCollector
from app.models import get_db, CollectionState
from app.rate_limiter import get_rate_limiter

def force_collect():
    print("🔄 Force Tweet Collection")
    print("=" * 50)
    
    # Reset rate limiter
    rate_limiter = get_rate_limiter()
    rate_limiter.reset()
    print("✅ Rate limiter reset")
    
    db = next(get_db())
    
    # Get tweets from the last 3 hours
    since_time = datetime.now(timezone.utc) - timedelta(hours=3)
    
    print(f"\n📊 Collecting tweets since: {since_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    collector = TwitterCollector(db_session=db)
    
    print("\n🔄 Starting collection...")
    new_tweets = 0
    
    # Collect with small batches to avoid rate limits
    from app.config import ACCOUNTS_TO_FOLLOW
    
    for i, account in enumerate(ACCOUNTS_TO_FOLLOW):
        if i >= 3:  # Only do 3 accounts to avoid rate limit
            print(f"⏸️  Skipping @{account['username']} (avoiding rate limit)")
            continue
            
        try:
            print(f"Collecting from @{account['username']}...")
            
            # Wait if needed
            rate_limiter.wait_if_needed()
            rate_limiter.record_request()
            
            tweets = collector.client.get_users_tweets(
                id=account['id'],
                max_results=10,
                tweet_fields=['created_at', 'public_metrics', 'referenced_tweets', 'entities'],
                start_time=since_time.replace(microsecond=0).isoformat().replace('+00:00', 'Z')
            )
            
            if tweets.data:
                for tweet in tweets.data:
                    if collector._save_tweet(tweet, account, {}):
                        new_tweets += 1
                print(f"  ✅ Got {len(tweets.data)} tweets")
            else:
                print(f"  No new tweets")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            if "429" in str(e):
                print("  Rate limited, stopping collection")
                break
    
    collector.db.commit()
    
    # Update collection state
    CollectionState.update_last_run(db, tweet_count=new_tweets)
    
    print(f"\n✅ Force collection complete!")
    print(f"   New tweets collected: {new_tweets}")
    
    db.close()

if __name__ == "__main__":
    import time
    
    print("This will force collect tweets from the last 3 hours")
    print("It will only collect from 3 accounts to avoid rate limits")
    
    response = input("\nProceed? (y/n): ")
    
    if response.lower() == 'y':
        force_collect()
    else:
        print("Cancelled")