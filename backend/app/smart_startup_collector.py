"""
Smart startup collection that respects Twitter rate limits
"""
from datetime import datetime, timedelta, timezone
import logging
import time
from app.collectors.twitter_collector import TwitterCollector
from app.rate_limiter import get_rate_limiter
from app.config import ACCOUNTS_TO_FOLLOW

logger = logging.getLogger(__name__)

def smart_collect_on_startup():
    """
    Smart collection that respects rate limits
    For Twitter Basic tier: 10 requests per 15 minutes
    With 7 accounts, we need to be careful
    """
    
    try:
        print("\n" + "="*60)
        print("🚀 SMART STARTUP COLLECTION")
        print("="*60)
        
        # Get rate limiter
        rate_limiter = get_rate_limiter()
        
        # Check if we're already rate limited
        if not rate_limiter.can_make_request():
            print("⚠️  Rate limit active from previous session")
            print("   Will wait for rate limit window to reset...")
            rate_limiter.wait_if_needed()
        
        # Get last run time
        last_run = CollectionState.get_last_run(db)
        
        if not last_run:
            print("📌 First run detected")
            # For first run, just collect recent tweets (not 7 days - too many requests)
            print("   Will collect recent tweets only (to avoid rate limits)")
            
            # Create collector
            collector = TwitterCollector(db_session=db)
            
            # Collect from just 3 accounts at a time to stay under rate limit
            print("\n🔄 Collecting recent tweets (limited to avoid rate limits)...")
            new_tweets = 0
            
            for i, account in enumerate(ACCOUNTS_TO_FOLLOW):
                if i >= 3:  # Only do 3 accounts on first run
                    print(f"   ⏸️  Skipping @{account['username']} (will collect on next run)")
                    continue
                
                try:
                    print(f"   Checking @{account['username']}...")
                    
                    # Wait if needed
                    rate_limiter.wait_if_needed()
                    
                    # Make request
                    rate_limiter.record_request()
                    tweets = collector.client.get_users_tweets(
                        id=account['id'],
                        max_results=10,  # Small number to be safe
                        tweet_fields=['created_at', 'public_metrics', 'referenced_tweets', 'entities']
                    )
                    
                    if tweets.data:
                        for tweet in tweets.data:
                            if collector._save_tweet(tweet, account, {}):
                                new_tweets += 1
                        print(f"     ✅ Got {len(tweets.data)} tweets")
                    else:
                        print(f"     No tweets found")
                    
                    # Small delay between accounts
                    time.sleep(2)
                    
                except Exception as e:
                    if "429" in str(e):
                        print(f"     ⚠️ Rate limited - will retry later")
                        rate_limiter.handle_429_error()
                        break
                    else:
                        print(f"     ❌ Error: {e}")
            
            collector.db.commit()
            
        else:
            # Not first run - collect since last run
            # Make sure last_run is timezone-aware
            if last_run.tzinfo is None:
                last_run = last_run.replace(tzinfo=timezone.utc)
            
            time_diff = datetime.now(timezone.utc) - last_run
            hours_since = time_diff.total_seconds() / 3600
            
            print(f"⏰ Last collection: {last_run.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            print(f"   ({hours_since:.1f} hours ago)")
            
            # Only skip if REALLY recent (less than 15 minutes)
            if hours_since < 0.25:  # 15 minutes
                print("✅ Very recently collected (less than 15 minutes ago)")
                print("   Skipping startup collection")
                db.close()
                return 0
            
            # If less than 1 hour, do a minimal collection
            if hours_since < 1:
                print(f"📝 Recent collection ({hours_since:.1f} hours ago)")
                print("   Will do minimal collection (3 accounts only)")
            
            # If it's been more than 24 hours, we need to be careful
            if hours_since > 24:
                print("⚠️  Large gap detected (>24 hours)")
                print("   Will collect conservatively to avoid rate limits")
            
            # Create collector
            collector = TwitterCollector(db_session=db)
            
            # Ensure last_run is properly formatted for API
            if last_run.tzinfo is None:
                last_run = last_run.replace(tzinfo=timezone.utc)
            
            # Collect with rate limiting
            print(f"\n🔄 Collecting tweets since last run...")
            new_tweets = collector.collect_since_timestamp(last_run)
        
        # Update collection state
        CollectionState.update_last_run(db, tweet_count=new_tweets)
        
        # Show results
        total_after = db.query(func.count(Tweet.id)).scalar()
        print(f"\n✅ Smart Collection Complete!")
        print(f"   • New tweets collected: {new_tweets}")
        print(f"   • Total tweets in database: {total_after}")
        
        # If we couldn't collect from all accounts, note it
        if last_run is None and len(ACCOUNTS_TO_FOLLOW) > 3:
            print(f"\n📝 Note: Only collected from 3/{len(ACCOUNTS_TO_FOLLOW)} accounts")
            print("   Remaining accounts will be collected on next scheduled run")
        
        print("="*60 + "\n")
        
        db.close()
        logger.info(f"Smart startup collection completed: {new_tweets} new tweets")
        
        return new_tweets
        
    except Exception as e:
        logger.error(f"Error in smart startup collection: {e}")
        print(f"❌ Error during startup collection: {e}")
        db.close()
        return 0