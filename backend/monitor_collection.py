#!/usr/bin/env python3
"""
Monitor collection status and statistics
"""
import sys
import os
from datetime import datetime, timezone, timedelta
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db, Tweet, CollectionState
from app.rate_limiter import get_rate_limiter
from app.config import ACCOUNTS_TO_FOLLOW
from sqlalchemy import func

def monitor_collection():
    print("📊 COLLECTION MONITOR")
    print("=" * 60)
    
    db = next(get_db())
    
    try:
        # Get collection state
        last_run = CollectionState.get_last_run(db)
        if last_run:
            if last_run.tzinfo is None:
                last_run = last_run.replace(tzinfo=timezone.utc)
            time_since = datetime.now(timezone.utc) - last_run
            print(f"\n🕒 Last Collection:")
            print(f"   Time: {last_run.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            print(f"   {time_since.total_seconds() / 3600:.1f} hours ago")
        else:
            print("\n🕒 No collection history found")
        
        # Get rate limit status
        rate_limiter = get_rate_limiter()
        print(f"\n🚀 Rate Limit Status:")
        print(f"   Requests used: {len(rate_limiter.requests_made)}/{rate_limiter.max_requests}")
        if rate_limiter.backoff_until and rate_limiter.backoff_until > datetime.now(timezone.utc):
            remaining = (rate_limiter.backoff_until - datetime.now(timezone.utc)).total_seconds()
            print(f"   ⚠️  BACKOFF: {remaining:.0f} seconds remaining")
        elif not rate_limiter.can_make_request():
            print(f"   ⚠️  RATE LIMITED")
        else:
            print(f"   ✅ Ready to collect")
        
        # Get database statistics
        total_tweets = db.query(func.count(Tweet.id)).scalar()
        
        # Most recent tweet
        recent_tweet = db.query(Tweet).order_by(Tweet.created_at.desc()).first()
        if recent_tweet:
            tweet_age = datetime.now(timezone.utc) - recent_tweet.created_at
            print(f"\n📝 Most Recent Tweet:")
            print(f"   From: @{recent_tweet.author_username}")
            print(f"   Time: {recent_tweet.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            print(f"   {tweet_age.total_seconds() / 3600:.1f} hours ago")
        
        # Tweets by time period
        print(f"\n📈 Tweet Distribution:")
        periods = [
            (1, "Last hour"),
            (6, "Last 6 hours"),
            (24, "Last 24 hours"),
            (72, "Last 3 days"),
            (168, "Last week")
        ]
        
        for hours, label in periods:
            since = datetime.now(timezone.utc) - timedelta(hours=hours)
            count = db.query(func.count(Tweet.id)).filter(
                Tweet.created_at >= since
            ).scalar()
            if count > 0:
                print(f"   {label}: {count} tweets")
        
        print(f"   Total: {total_tweets} tweets")
        
        # Tweets by account
        print(f"\n👥 Tweets by Account:")
        account_stats = db.query(
            Tweet.author_username,
            func.count(Tweet.id).label('count'),
            func.max(Tweet.created_at).label('latest')
        ).group_by(Tweet.author_username).all()
        
        # Sort with timezone-aware comparison
        def make_aware(dt):
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt
        
        for username, count, latest in sorted(account_stats, key=lambda x: make_aware(x[2]), reverse=True):
            # Ensure latest is timezone-aware
            latest = make_aware(latest)
            age = datetime.now(timezone.utc) - latest
            age_str = f"{age.total_seconds() / 3600:.1f}h ago"
            print(f"   @{username}: {count} tweets (latest: {age_str})")
        
        # Check for gaps
        print(f"\n🕳️ Gap Analysis:")
        now = datetime.now(timezone.utc)
        
        # Check each account for gaps
        gaps_found = False
        for account in ACCOUNTS_TO_FOLLOW:
            account_tweets = db.query(Tweet).filter(
                Tweet.author_id == account['id']
            ).order_by(Tweet.created_at.desc()).limit(10).all()
            
            if account_tweets:
                latest = account_tweets[0].created_at
                if latest.tzinfo is None:
                    latest = latest.replace(tzinfo=timezone.utc)
                gap = (now - latest).total_seconds() / 3600
                
                if gap > 24:  # More than 24 hours since last tweet
                    print(f"   ⚠️  @{account['username']}: No tweets for {gap:.1f} hours")
                    gaps_found = True
        
        if not gaps_found:
            print("   ✅ No significant gaps detected")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        
        if last_run:
            hours_since = time_since.total_seconds() / 3600
            if hours_since > 6:
                print(f"   • Consider running collection (last run {hours_since:.1f}h ago)")
                print(f"     Run: python wait_and_collect.py")
            elif hours_since > 1:
                print(f"   • Collection is recent but you can run if needed")
            else:
                print(f"   • Collection very recent, no action needed")
        else:
            print(f"   • Run initial collection: python wait_and_collect.py")
        
        if not rate_limiter.can_make_request():
            if rate_limiter.backoff_until:
                wait = (rate_limiter.backoff_until - datetime.now(timezone.utc)).total_seconds()
                print(f"   • Wait {wait/60:.1f} minutes for rate limit to clear")
            else:
                print(f"   • Rate limited - wait for window reset")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    monitor_collection()