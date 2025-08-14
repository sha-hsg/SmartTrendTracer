"""
Background task manager for non-blocking operations
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional
import threading
from concurrent.futures import ThreadPoolExecutor

from app.smart_startup_collector import smart_collect_on_startup
from app.persistent_rate_limiter import get_persistent_rate_limiter

logger = logging.getLogger(__name__)

# Global executor for background tasks
executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="tweet-collector")

# Global flag to track if collection is running
collection_in_progress = False
collection_lock = threading.Lock()

def get_collection_status():
    """Get the current collection status"""
    with collection_lock:
        return {
            "in_progress": collection_in_progress,
            "rate_limited": not get_persistent_rate_limiter().can_make_request()
        }

def run_background_collection():
    """Run tweet collection in background thread"""
    global collection_in_progress
    
    try:
        with collection_lock:
            if collection_in_progress:
                logger.info("Collection already in progress, skipping")
                return 0
            collection_in_progress = True
        
        logger.info("Starting background tweet collection...")
        
        # Check rate limit status
        rate_limiter = get_persistent_rate_limiter()
        
        if not rate_limiter.can_make_request():
            wait_time = rate_limiter.get_wait_time()
            
            # Ensure we wait the full 15 minutes (900 seconds)
            if wait_time > 0:
                wait_time = max(wait_time, 900)  # Always wait at least 15 minutes
                
            logger.info(f"Rate limited - scheduling retry in {wait_time} seconds ({wait_time/60:.1f} minutes)")
            
            # Schedule a retry after the wait period
            # This doesn't block - it creates a timer that runs later
            threading.Timer(wait_time, run_background_collection).start()
            
            with collection_lock:
                collection_in_progress = False
            return 0
        
        # Run the actual collection
        new_tweets = smart_collect_on_startup()
        logger.info(f"Background collection completed: {new_tweets} new tweets")
        
        # After successful collection, schedule next one in 15 minutes
        # This ensures we respect the 900 second interval
        logger.info("Scheduling next collection in 15 minutes")
        threading.Timer(900, run_background_collection).start()
        
        return new_tweets
        
    except Exception as e:
        logger.error(f"Error in background collection: {e}")
        
        # On error, retry in 15 minutes
        logger.info("Error occurred, retrying in 15 minutes")
        threading.Timer(900, run_background_collection).start()
        
        return 0
    finally:
        with collection_lock:
            collection_in_progress = False

async def start_background_collection():
    """Async wrapper to start background collection"""
    loop = asyncio.get_event_loop()
    
    # Submit to thread pool executor
    future = executor.submit(run_background_collection)
    
    # Don't wait for completion - let it run in background
    logger.info("Tweet collection started in background")
    
    return {"status": "started", "message": "Collection running in background"}

def shutdown_background_tasks():
    """Shutdown background task executor gracefully"""
    logger.info("Shutting down background task executor...")
    executor.shutdown(wait=False)
    logger.info("Background task executor shutdown complete")