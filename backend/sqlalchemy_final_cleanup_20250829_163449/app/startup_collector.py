"""
Startup collection - fills gaps since last run
"""
from datetime import datetime, timedelta, timezone
import logging
import time
from app.models import get_db, CollectionState, Tweet
from app.collectors.twitter_collector import TwitterCollector
from app.rate_limiter import get_rate_limiter
from app.config import ACCOUNTS_TO_FOLLOW
from sqlalchemy import func

logger = logging.getLogger(__name__)

def collect_tweets_since_last_run():
    """
    Collect all tweets since the last program run
    Called automatically when the backend starts
    """
    db = next(get_db())
    
    try:
        print("\n" + "="*60)
        print("🚀 STARTUP TWEET COLLECTION")
        print("="*60)
        
        # Get last run time from database
        last_run = CollectionState.get_last_run(db)
        
        # If never run before, get tweets from last 7 days
        if not last_run:
            print("📌 First run detected - collecting last 7 days of tweets")
            since_time = datetime.now(timezone.utc) - timedelta(days=7)
        else:
            # Calculate time since last run
            time_diff = datetime.now(timezone.utc) - last_run
            hours_since = time_diff.total_seconds() / 3600
            
            print(f"⏰ Last collection: {last_run.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            print(f"   ({hours_since:.1f} hours ago)")
            
            # Use last run time, but cap at 7 days (Twitter API limit)
            max_lookback = datetime.now(timezone.utc) - timedelta(days=7)
            since_time = max(last_run, max_lookback)
            
            if last_run < max_lookback:
                print(f"⚠️  Last run was more than 7 days ago")
                print(f"   Will collect from: {since_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        # Check current database stats before collection
        total_before = db.query(func.count(Tweet.id)).scalar()
        print(f"\n📊 Current database: {total_before} tweets")
        
        # Create collector and collect tweets
        collector = TwitterCollector(db_session=db)
        
        print(f"\n🔄 Collecting tweets since {since_time.strftime('%Y-%m-%d %H:%M:%S UTC')}...")
        new_tweets = collector.collect_since_timestamp(since_time)
        
        # Get the latest tweet ID for tracking
        latest_tweet = db.query(Tweet).order_by(Tweet.created_at.desc()).first()
        latest_tweet_id = latest_tweet.id if latest_tweet else None
        
        # Update collection state
        CollectionState.update_last_run(db, tweet_count=new_tweets, last_tweet_id=latest_tweet_id)
        
        # Show results
        total_after = db.query(func.count(Tweet.id)).scalar()
        print(f"\n✅ Collection Complete!")
        print(f"   • New tweets collected: {new_tweets}")
        print(f"   • Total tweets in database: {total_after}")
        
        if new_tweets > 0:
            # Show breakdown by account
            print(f"\n📈 New tweets by account:")
            recent_stats = db.query(
                Tweet.author_username,
                func.count(Tweet.id).label('count')
            ).filter(
                Tweet.created_at >= since_time
            ).group_by(Tweet.author_username).all()
            
            for stat in recent_stats:
                print(f"   • @{stat.author_username}: {stat.count} tweets")
        
        print("="*60 + "\n")
        
        db.close()
        logger.info(f"Startup collection completed: {new_tweets} new tweets")
        
        return new_tweets
        
    except Exception as e:
        logger.error(f"Error in startup collection: {e}")
        print(f"❌ Error during startup collection: {e}")
        db.close()
        return 0

def get_collection_summary(db):
    """Get a summary of the current collection state"""
    try:
        total_tweets = db.query(func.count(Tweet.id)).scalar()
        
        # Get account statistics
        account_stats = db.query(
            Tweet.author_username,
            func.count(Tweet.id).label('count'),
            func.max(Tweet.created_at).label('latest')
        ).group_by(Tweet.author_username).all()
        
        # Check for stale accounts (no tweets in 24 hours)
        stale_accounts = []
        one_day_ago = datetime.now(timezone.utc) - timedelta(days=1)
        
        for stat in account_stats:
            if stat.latest < one_day_ago:
                hours_stale = (datetime.now(timezone.utc) - stat.latest).total_seconds() / 3600
                stale_accounts.append({
                    'username': stat.author_username,
                    'hours_stale': hours_stale,
                    'last_tweet': stat.latest
                })
        
        return {
            'total_tweets': total_tweets,
            'account_stats': account_stats,
            'stale_accounts': stale_accounts
        }
    except Exception as e:
        logger.error(f"Error getting collection summary: {e}")
        return None