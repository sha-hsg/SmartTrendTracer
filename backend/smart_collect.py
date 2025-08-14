#!/usr/bin/env python3
"""
Smart hybrid collector that uses both API and twscrape
Best of both worlds: reliability + no limits
"""
import sys
import os
import asyncio
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.collectors.twitter_collector import TwitterCollector
from app.collectors.twscrape_collector import TwscrapeCollector
from app.models import get_db, Tweet, CollectionState
from app.rate_limiter import get_rate_limiter
from app.config import ACCOUNTS_TO_FOLLOW
from sqlalchemy import func

async def smart_hybrid_collect():
    print("🤖 SMART HYBRID COLLECTION")
    print("=" * 60)
    print("💡 Strategy: Use API first, fall back to twscrape if needed")
    print()
    
    db = next(get_db())
    rate_limiter = get_rate_limiter()
    
    try:
        # Get last collection time
        last_run = CollectionState.get_last_run(db)
        if last_run and last_run.tzinfo is None:
            last_run = last_run.replace(tzinfo=timezone.utc)
        
        since = last_run or datetime.now(timezone.utc) - timedelta(hours=24)
        
        print(f"📊 Collection period: Since {since.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"📊 Accounts to check: {len(ACCOUNTS_TO_FOLLOW)}")
        print()
        
        # Check rate limit status
        can_use_api = rate_limiter.can_make_request()
        available_requests = rate_limiter.max_requests - len(rate_limiter.requests_made)
        
        print(f"🚀 API Status:")
        print(f"   • Available requests: {available_requests}/10")
        
        total_new = 0
        api_collected = 0
        twscrape_collected = 0
        
        if can_use_api and available_requests >= len(ACCOUNTS_TO_FOLLOW):
            # We have enough API requests for all accounts
            print(f"   • Strategy: ✅ Using Twitter API (enough requests)\n")
            
            collector = TwitterCollector(db_session=db)
            
            for account in ACCOUNTS_TO_FOLLOW:
                try:
                    print(f"📡 [API] Checking @{account['username']}...", end="", flush=True)
                    
                    rate_limiter.wait_if_needed()
                    rate_limiter.record_request()
                    
                    tweets = collector.client.get_users_tweets(
                        id=account['id'],
                        max_results=50,
                        tweet_fields=['created_at', 'public_metrics', 'referenced_tweets', 'entities'],
                        start_time=since.replace(microsecond=0).isoformat().replace('+00:00', 'Z'),
                        end_time=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
                    )
                    
                    new_count = 0
                    if tweets.data:
                        for tweet in tweets.data:
                            if collector._save_tweet(tweet, account, {}):
                                new_count += 1
                    
                    print(f" ✅ {new_count} new tweets")
                    api_collected += new_count
                    total_new += new_count
                    
                except Exception as e:
                    if "429" in str(e):
                        print(f" ❌ Rate limited")
                        rate_limiter.handle_429_error()
                        break
                    else:
                        print(f" ❌ Error: {e}")
            
            collector.db.commit()
            
        elif can_use_api and available_requests > 0:
            # We have some API requests but not enough for all
            print(f"   • Strategy: 🔶 Hybrid mode (use {available_requests} API requests, rest with twscrape)\n")
            
            # Use API for priority accounts
            api_collector = TwitterCollector(db_session=db)
            
            for i, account in enumerate(ACCOUNTS_TO_FOLLOW[:available_requests]):
                try:
                    print(f"📡 [API] Checking @{account['username']}...", end="", flush=True)
                    
                    rate_limiter.record_request()
                    
                    tweets = api_collector.client.get_users_tweets(
                        id=account['id'],
                        max_results=50,
                        tweet_fields=['created_at', 'public_metrics', 'referenced_tweets', 'entities'],
                        start_time=since.replace(microsecond=0).isoformat().replace('+00:00', 'Z')
                    )
                    
                    new_count = 0
                    if tweets.data:
                        for tweet in tweets.data:
                            if api_collector._save_tweet(tweet, account, {}):
                                new_count += 1
                    
                    print(f" ✅ {new_count} new tweets")
                    api_collected += new_count
                    total_new += new_count
                    
                except Exception as e:
                    print(f" ❌ Error: {e}")
                    break
            
            api_collector.db.commit()
            
            # Use twscrape for remaining accounts
            if available_requests < len(ACCOUNTS_TO_FOLLOW):
                print(f"\n🔄 Switching to twscrape for remaining accounts...\n")
                
                twscrape_collector = TwscrapeCollector(db_session=db)
                
                for account in ACCOUNTS_TO_FOLLOW[available_requests:]:
                    print(f"🌐 [Twscrape] Checking @{account['username']}...", end="", flush=True)
                    
                    new_count = await twscrape_collector.collect_user_tweets(
                        username=account['username'],
                        since=since,
                        limit=50
                    )
                    
                    print(f" ✅ {new_count} new tweets")
                    twscrape_collected += new_count
                    total_new += new_count
        
        else:
            # Rate limited, use twscrape for everything
            print(f"   • Strategy: 🔴 Twscrape only (API rate limited)\n")
            
            twscrape_collector = TwscrapeCollector(db_session=db)
            
            for account in ACCOUNTS_TO_FOLLOW:
                print(f"🌐 [Twscrape] Checking @{account['username']}...", end="", flush=True)
                
                new_count = await twscrape_collector.collect_user_tweets(
                    username=account['username'],
                    since=since,
                    limit=50
                )
                
                print(f" ✅ {new_count} new tweets")
                twscrape_collected += new_count
                total_new += new_count
        
        # Update collection state
        CollectionState.update_last_run(db, tweet_count=total_new)
        
        # Get statistics
        total_tweets = db.query(func.count(Tweet.id)).scalar()
        recent_tweets = db.query(func.count(Tweet.id)).filter(
            Tweet.created_at >= datetime.now(timezone.utc) - timedelta(hours=24)
        ).scalar()
        
        print("\n" + "=" * 60)
        print("✅ HYBRID COLLECTION COMPLETE")
        print("=" * 60)
        print(f"📊 Results:")
        print(f"   • Total new tweets: {total_new}")
        print(f"   • Via Twitter API: {api_collected}")
        print(f"   • Via Twscrape: {twscrape_collected}")
        print(f"   • Total in database: {total_tweets}")
        print(f"   • Last 24h tweets: {recent_tweets}")
        
        if twscrape_collected > 0:
            print(f"\n💡 Twscrape saved the day! Collected {twscrape_collected} tweets without rate limits.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("\n🎆 SMART HYBRID COLLECTOR")
    print("Best of both worlds: API reliability + twscrape freedom")
    print("\nThis collector will:")
    print("  1. Try Twitter API first (reliable)")
    print("  2. Fall back to twscrape if rate limited")
    print("  3. Use hybrid mode when partially rate limited")
    print("  4. Always get your data, no matter what!")
    
    asyncio.run(smart_hybrid_collect())