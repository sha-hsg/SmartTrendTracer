#!/usr/bin/env python3
"""
Wait for rate limit to reset, then collect tweets
"""
import sys
import os
import time
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.collectors.twitter_collector import TwitterCollector
from app.models import get_db, CollectionState, Tweet
from app.rate_limiter import get_rate_limiter
from app.config import ACCOUNTS_TO_FOLLOW
from sqlalchemy import func

def wait_and_collect():
    print("⏳ WAIT AND COLLECT")
    print("=" * 50)
    
    # Get rate limiter
    rate_limiter = get_rate_limiter()
    
    # Check current rate limit status
    if not rate_limiter.can_make_request():
        wait_time = rate_limiter.get_wait_time()
        if wait_time > 0:
            print(f"\n⚠️  Rate limited. Need to wait {wait_time:.0f} seconds")
            print(f"   Will resume at: {(datetime.now() + timedelta(seconds=wait_time)).strftime('%H:%M:%S')}")
            print("\n   Waiting...", end="", flush=True)
            
            # Wait with progress indicator
            for i in range(int(wait_time)):
                time.sleep(1)
                if i % 10 == 0:
                    print(".", end="", flush=True)
            
            print(" Done!\n")
        else:
            print("✅ Not rate limited, can proceed")
    else:
        print("✅ Rate limit OK")
    
    # Now collect tweets
    db = next(get_db())
    
    try:
        # Get last collection time
        last_run = CollectionState.get_last_run(db)
        
        if last_run:
            if last_run.tzinfo is None:
                last_run = last_run.replace(tzinfo=timezone.utc)
            print(f"\n📊 Last collection: {last_run.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            since_time = last_run
        else:
            # Collect from 6 hours ago
            since_time = datetime.now(timezone.utc) - timedelta(hours=6)
            print(f"\n📊 First run, collecting from: {since_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        # Create collector
        collector = TwitterCollector(db_session=db)
        
        print("\n🔄 Starting collection...")
        print(f"   Accounts to check: {len(ACCOUNTS_TO_FOLLOW)}")
        print(f"   Available requests: {rate_limiter.max_requests - len(rate_limiter.requests_made)}")
        print()
        
        new_tweets = 0
        accounts_checked = 0
        
        for account in ACCOUNTS_TO_FOLLOW:
            # Check if we can make a request
            if not rate_limiter.can_make_request():
                print(f"\n⚠️  Rate limit reached after {accounts_checked} accounts")
                print("   Will continue in next run")
                break
            
            try:
                print(f"📡 Checking @{account['username']}...", end="", flush=True)
                
                # Wait if needed (should not be needed if can_make_request is true)
                rate_limiter.wait_if_needed()
                
                # Record the request
                rate_limiter.record_request()
                
                # Make the API call
                tweets = collector.client.get_users_tweets(
                    id=account['id'],
                    max_results=50,  # Get more tweets per request
                    tweet_fields=['created_at', 'public_metrics', 'referenced_tweets', 'entities'],
                    start_time=since_time.replace(microsecond=0).isoformat().replace('+00:00', 'Z'),
                    end_time=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
                )
                
                if tweets.data:
                    tweet_count = 0
                    for tweet in tweets.data:
                        if collector._save_tweet(tweet, account, {}):
                            tweet_count += 1
                            new_tweets += 1
                    print(f" ✅ {tweet_count} new tweets")
                else:
                    print(" No new tweets")
                
                accounts_checked += 1
                
                # Small delay between accounts
                time.sleep(1)
                
            except Exception as e:
                if "429" in str(e):
                    print(f" ❌ Rate limited")
                    rate_limiter.handle_429_error()
                    print(f"\n⚠️  Hit rate limit after {accounts_checked} accounts")
                    break
                else:
                    print(f" ❌ Error: {e}")
        
        # Commit changes
        collector.db.commit()
        
        # Update collection state
        CollectionState.update_last_run(db, tweet_count=new_tweets)
        
        # Get statistics
        total_tweets = db.query(func.count(Tweet.id)).scalar()
        recent_tweets = db.query(func.count(Tweet.id)).filter(
            Tweet.created_at >= datetime.now(timezone.utc) - timedelta(hours=24)
        ).scalar()
        
        print("\n" + "=" * 50)
        print("✅ COLLECTION COMPLETE")
        print("=" * 50)
        print(f"📊 Results:")
        print(f"   • Accounts checked: {accounts_checked}/{len(ACCOUNTS_TO_FOLLOW)}")
        print(f"   • New tweets collected: {new_tweets}")
        print(f"   • Total tweets in database: {total_tweets}")
        print(f"   • Tweets from last 24h: {recent_tweets}")
        print(f"   • Remaining API requests: {rate_limiter.max_requests - len(rate_limiter.requests_made)}/{rate_limiter.max_requests}")
        
        if accounts_checked < len(ACCOUNTS_TO_FOLLOW):
            print("\n📝 Note: Not all accounts were checked due to rate limits")
            print("   Run this script again in 15 minutes to check remaining accounts")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    wait_and_collect()