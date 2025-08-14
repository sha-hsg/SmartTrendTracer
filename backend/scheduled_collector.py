#!/usr/bin/env python3
"""
Scheduled collector that runs every 30 minutes
Automatically manages rate limits and collects tweets
"""
import sys
import os
import time
import schedule
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.collectors.twitter_collector import TwitterCollector
from app.models import get_db, Tweet, CollectionState
from app.rate_limiter import get_rate_limiter
from app.config import ACCOUNTS_TO_FOLLOW
from sqlalchemy import func

def collect_tweets():
    """
    Collect tweets with rate limit management
    """
    print(f"\n🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Starting collection")
    
    db = next(get_db())
    rate_limiter = get_rate_limiter()
    
    try:
        # Check if we can collect
        if not rate_limiter.can_make_request():
            wait_time = rate_limiter.get_wait_time() if hasattr(rate_limiter, 'get_wait_time') else 900
            print(f"   ⚠️  Rate limited. Will retry in {wait_time/60:.1f} minutes")
            db.close()
            return
        
        # Get last collection time
        last_run = CollectionState.get_last_run(db)
        if last_run and last_run.tzinfo is None:
            last_run = last_run.replace(tzinfo=timezone.utc)
        
        since = last_run or datetime.now(timezone.utc) - timedelta(hours=24)
        
        # Create collector
        collector = TwitterCollector(db_session=db)
        
        new_tweets = 0
        accounts_checked = 0
        
        # Collect from accounts
        for account in ACCOUNTS_TO_FOLLOW:
            if not rate_limiter.can_make_request():
                print(f"   ⚠️  Rate limit reached after {accounts_checked} accounts")
                break
            
            try:
                rate_limiter.record_request()
                
                tweets = collector.client.get_users_tweets(
                    id=account['id'],
                    max_results=20,
                    tweet_fields=['created_at', 'public_metrics', 'referenced_tweets', 'entities'],
                    start_time=since.replace(microsecond=0).isoformat().replace('+00:00', 'Z'),
                    end_time=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
                )
                
                if tweets.data:
                    for tweet in tweets.data:
                        if collector._save_tweet(tweet, account, {}):
                            new_tweets += 1
                
                accounts_checked += 1
                
            except Exception as e:
                if "429" in str(e):
                    rate_limiter.handle_429_error()
                    print(f"   ❌ Rate limited")
                    break
        
        collector.db.commit()
        
        # Update collection state
        if new_tweets > 0 or accounts_checked > 0:
            CollectionState.update_last_run(db, tweet_count=new_tweets)
        
        print(f"   ✅ Checked {accounts_checked} accounts, found {new_tweets} new tweets")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    finally:
        db.close()

def run_scheduler():
    """
    Run the scheduled collector
    """
    print("🚀 SCHEDULED TWEET COLLECTOR")
    print("=" * 60)
    print(f"📍 Tracking {len(ACCOUNTS_TO_FOLLOW)} accounts:")
    for account in ACCOUNTS_TO_FOLLOW:
        print(f"   • @{account['username']}")
    print()
    print("⏰ Schedule:")
    print("   • Runs every 30 minutes")
    print("   • Automatically handles rate limits")
    print("   • Collects new tweets only")
    print()
    print("🔄 Press Ctrl+C to stop")
    print("=" * 60)
    
    # Run immediately on start
    collect_tweets()
    
    # Schedule every 30 minutes
    schedule.every(30).minutes.do(collect_tweets)
    
    # Keep running
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\n🚫 Stopping scheduler...")
            break

if __name__ == "__main__":
    run_scheduler()