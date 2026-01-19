"""
Async non-blocking startup collection
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from app.collectors.twitter_collector import TwitterCollector
from app.persistent_rate_limiter import get_persistent_rate_limiter
from app.config import ACCOUNTS_TO_FOLLOW

logger = logging.getLogger(__name__)

async def async_collect_tweets():
    """
    Completely non-blocking tweet collection
    Returns immediately if rate limited
    """
    
    try:
        logger.info("Starting async tweet collection (non-blocking)")
        
        # Get rate limiter
        rate_limiter = get_persistent_rate_limiter()
        
        # Check if we're rate limited - if so, return immediately
        if not rate_limiter.can_make_request():
            wait_time = rate_limiter.get_wait_time()
            logger.info(f"Rate limited - will retry in {wait_time} seconds (returning immediately)")
            
            # Schedule retry but don't wait
            asyncio.create_task(retry_after_delay(wait_time))
            
            db.close()
            return {"status": "rate_limited", "retry_in": wait_time}
        
        # Get last run time
        last_run = CollectionState.get_last_run(db)
        
        if last_run:
            # Make sure last_run is timezone-aware
            if last_run.tzinfo is None:
                last_run = last_run.replace(tzinfo=timezone.utc)
            
            time_diff = datetime.now(timezone.utc) - last_run
            hours_since = time_diff.total_seconds() / 3600
            
            # Skip if very recent
            if hours_since < 0.25:  # 15 minutes
                logger.info("Recently collected, skipping")
                db.close()
                return {"status": "skipped", "reason": "recent_collection"}
        
        # Create collector
        collector = TwitterCollector(db_session=db)
        
        # Start collection in background task
        asyncio.create_task(collect_in_background(collector, db, last_run))
        
        db.close()
        return {"status": "started", "message": "Collection started in background"}
        
    except Exception as e:
        logger.error(f"Error in async collection: {e}")
        db.close()
        return {"status": "error", "error": str(e)}

async def collect_in_background(collector, db, last_run: Optional[datetime]):
    """
    Run the actual collection in background
    This function runs asynchronously and doesn't block
    """
    try:
        logger.info("Background collection task started")
        new_tweets = 0
        
        # Collect from accounts one by one
        for account in ACCOUNTS_TO_FOLLOW[:3]:  # Limit to 3 for safety
            try:
                # Use async sleep instead of blocking sleep
                await asyncio.sleep(1)
                
                logger.info(f"Collecting from @{account['username']}")
                
                # Get tweets (this is still sync but we could make it async)
                tweets = collector.client.get_users_tweets(
                    id=account['id'],
                    max_results=10,
                    tweet_fields=['created_at', 'public_metrics', 'referenced_tweets', 'entities']
                )
                
                if tweets.data:
                    for tweet in tweets.data:
                        if collector._save_tweet(tweet, account, {}):
                            new_tweets += 1
                    logger.info(f"Got {len(tweets.data)} tweets from @{account['username']}")
                
            except Exception as e:
                if "429" in str(e):
                    logger.warning(f"Rate limited on {account['username']}")
                    # Don't block, just skip
                    break
                else:
                    logger.error(f"Error collecting from {account['username']}: {e}")
        
        # Commit changes
        db.commit()
        
        # Update collection state
        CollectionState.update_last_run(db, tweet_count=new_tweets)
        
        logger.info(f"Background collection completed: {new_tweets} new tweets")
        
    except Exception as e:
        logger.error(f"Error in background collection: {e}")
    finally:
        db.close()

async def retry_after_delay(delay_seconds: int):
    """
    Wait and retry collection after delay
    This runs completely in background
    """
    logger.info(f"Scheduled retry in {delay_seconds} seconds")
    await asyncio.sleep(delay_seconds)
    logger.info("Retrying collection after delay")
    await async_collect_tweets()