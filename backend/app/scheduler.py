"""
Background scheduler for automatic tweet collection
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import logging
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.collectors.twitter_collector import TwitterCollector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def scheduled_tweet_collection():
    """Function to be called by scheduler for tweet collection"""
    logger.info("Starting scheduled tweet collection...")
    
    try:
        # Use background task to avoid blocking
        from app.background_tasks import run_background_collection
        from concurrent.futures import ThreadPoolExecutor
        
        # Submit to background thread
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(run_background_collection)
        
        # Don't wait for completion - let it run in background
        logger.info("Tweet collection started in background thread")
        
    except Exception as e:
        logger.error(f"Error in scheduled collection: {e}")

def start_scheduler():
    """Start the background scheduler"""
    scheduler = BackgroundScheduler()
    
    # Schedule tweet collection every 15 minutes (minimum safe interval for Twitter API)
    # This respects the 900 seconds (15 minutes) rate limit window
    scheduler.add_job(
        func=scheduled_tweet_collection,
        trigger=IntervalTrigger(minutes=15),  # Changed to 15 minutes
        id='collect_tweets',
        name='Collect tweets from monitored accounts',
        replace_existing=True
    )
    
    # Don't run immediately on startup since we already have background collection
    # This prevents double collection on startup
    
    scheduler.start()
    logger.info("Scheduler started - will collect tweets every 15 minutes")
    
    return scheduler

def stop_scheduler(scheduler):
    """Stop the scheduler gracefully"""
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")

if __name__ == "__main__":
    # For testing the scheduler standalone
    import time
    from dotenv import load_dotenv
    
    load_dotenv()
    
    print("Starting tweet collection scheduler...")
    print("Will collect tweets every 30 minutes")
    print("Press Ctrl+C to stop")
    
    scheduler = start_scheduler()
    
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nStopping scheduler...")
        stop_scheduler(scheduler)