#!/usr/bin/env python3
"""
MongoDB-based Tweet Collector Service
- Uses MongoDB instead of SQLite for all data storage
- Collects tweets on a fixed cadence with proper rate limiting
- Robust error handling, pagination, and graceful shutdown
- Log rotation and configurable timings via environment variables
"""

import os
import sys
import time
import signal
import logging
import random
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

# Ensure relative imports work when invoked as a script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(usecwd=True))

from pymongo import MongoClient, ASCENDING, DESCENDING
from app.collectors.twitter_collector import TwitterCollector
from app.persistent_rate_limiter import get_persistent_rate_limiter
from app.config import ACCOUNTS_TO_FOLLOW
from logging.handlers import TimedRotatingFileHandler

# =========================
# MongoDB Connection
# =========================
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
mongo_client = MongoClient(MONGODB_URL)
db = mongo_client.smarttrendtracer

# =========================
# Configuration via ENV
# =========================
# Main collection interval (default 15 min)
COLLECTION_INTERVAL_SECONDS = int(os.getenv("COLLECTION_INTERVAL_SECONDS", "900"))
# Minimum minutes between runs (for multi-instance safety)
MIN_SKIP_MINUTES = float(os.getenv("MIN_SKIP_MINUTES", "5"))
# Delay between accounts to be nice to API
INTER_ACCOUNT_DELAY_SECONDS = float(os.getenv("INTER_ACCOUNT_DELAY_SECONDS", "2"))
# Add +/- jitter (fraction) to main sleep to avoid synchronized clients
SLEEP_JITTER_PCT = float(os.getenv("SLEEP_JITTER_PCT", "0.1"))
# Max tweets per page (most APIs allow up to 100)
PER_PAGE_MAX_RESULTS = int(os.getenv("PER_PAGE_MAX_RESULTS", "100"))
# Optional per-account hard cap (safety break for runaway pagination), 0 = unlimited
PER_ACCOUNT_MAX_PAGES = int(os.getenv("PER_ACCOUNT_MAX_PAGES", "0"))

# =========================
# Logging
# =========================
log_dir = Path(__file__).resolve().parent
log_dir.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Rotate daily, keep 7 days
file_handler = TimedRotatingFileHandler(
    filename=str(log_dir / "tweet_collector_mongodb.log"),
    when="D",
    interval=1,
    backupCount=7,
    encoding="utf-8",
)
stream_handler = logging.StreamHandler()

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# Avoid duplicate handlers if script reloaded
if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
else:
    logger.handlers.clear()
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

# =========================
# Shutdown handling
# =========================
running = True

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global running
    logger.info("Received shutdown signal (%s), stopping collector...", signum)
    running = False

# =========================
# Helper utilities
# =========================
def jitter_sleep(total_seconds: float):
    """
    Sleep with some randomization to avoid synchronized behavior.
    """
    if SLEEP_JITTER_PCT > 0:
        jitter = random.uniform(1 - SLEEP_JITTER_PCT, 1 + SLEEP_JITTER_PCT)
        sleep_time = total_seconds * jitter
    else:
        sleep_time = total_seconds
    
    logger.info(f"Sleeping for {sleep_time:.1f} seconds...")
    time.sleep(sleep_time)

def get_collection_state(key: str) -> Optional[Dict]:
    """Get collection state from MongoDB"""
    return db.collection_state.find_one({"key": key})

def update_collection_state(key: str, last_run: datetime, last_tweet_id: Optional[str] = None, 
                          tweets_collected: int = 0):
    """Update collection state in MongoDB"""
    db.collection_state.update_one(
        {"key": key},
        {
            "$set": {
                "last_run": last_run,
                "last_tweet_id": last_tweet_id,
                "tweets_collected": tweets_collected,
                "updated_at": datetime.now(timezone.utc)
            },
            "$setOnInsert": {
                "key": key,
                "created_at": datetime.now(timezone.utc)
            }
        },
        upsert=True
    )

def save_tweets_to_mongodb(tweets_data: List[Dict]) -> int:
    """
    Save tweets to MongoDB.
    Returns the number of new tweets saved.
    """
    if not tweets_data:
        return 0
    
    saved_count = 0
    
    for tweet_data in tweets_data:
        try:
            # Check if tweet already exists
            existing = db.tweets.find_one({"_id": tweet_data["id"]})
            
            if not existing:
                # Prepare tweet document
                tweet_doc = {
                    "_id": tweet_data["id"],  # Use Twitter ID as MongoDB _id
                    "text": tweet_data.get("text", ""),
                    "author_id": tweet_data.get("author_id"),
                    "author_username": tweet_data.get("author", {}).get("username"),
                    "author_name": tweet_data.get("author", {}).get("name"),
                    "created_at": datetime.fromisoformat(tweet_data["created_at"].replace("Z", "+00:00")),
                    "collected_at": datetime.now(timezone.utc),
                    "processed": False,
                    "metrics": {
                        "retweet_count": tweet_data.get("public_metrics", {}).get("retweet_count", 0),
                        "like_count": tweet_data.get("public_metrics", {}).get("like_count", 0),
                        "reply_count": tweet_data.get("public_metrics", {}).get("reply_count", 0),
                        "quote_count": tweet_data.get("public_metrics", {}).get("quote_count", 0)
                    },
                    "hashtags": tweet_data.get("entities", {}).get("hashtags", []),
                    "mentions": tweet_data.get("entities", {}).get("mentions", []),
                    "urls": tweet_data.get("entities", {}).get("urls", []),
                    "referenced_tweets": tweet_data.get("referenced_tweets", []),
                    "media": [],  # Will be added if media exists
                    "concept_ids": []  # Empty initially, will be populated by tagging service
                }
                
                # Add media if present
                if "media" in tweet_data:
                    for media in tweet_data["media"]:
                        tweet_doc["media"].append({
                            "media_key": media.get("media_key"),
                            "type": media.get("type"),
                            "url": media.get("url"),
                            "preview_image_url": media.get("preview_image_url"),
                            "alt_text": media.get("alt_text"),
                            "width": media.get("width"),
                            "height": media.get("height"),
                            "duration_ms": media.get("duration_ms")
                        })
                
                # Insert tweet
                db.tweets.insert_one(tweet_doc)
                saved_count += 1
                
        except Exception as e:
            logger.error(f"Error saving tweet {tweet_data.get('id')}: {e}")
            continue
    
    return saved_count

def collect_account_tweets(collector: TwitterCollector, account_id: str, 
                          username: str) -> Tuple[int, Optional[str]]:
    """
    Collect tweets for a single account using MongoDB.
    Returns (total_tweets_saved, newest_tweet_id).
    """
    total_saved = 0
    newest_tweet_id = None
    state_key = f"twitter_{username}"
    
    try:
        # Get last collection state from MongoDB
        state = get_collection_state(state_key)
        
        if state:
            last_run = state.get("last_run")
            if last_run and isinstance(last_run, datetime):
                # Check if we've collected recently
                minutes_since = (datetime.now(timezone.utc) - last_run).total_seconds() / 60
                if minutes_since < MIN_SKIP_MINUTES:
                    logger.info(f"Skipping @{username} - collected {minutes_since:.1f} minutes ago")
                    return 0, None
        
        # Collect tweets with pagination
        logger.info(f"Collecting tweets for @{username} (ID: {account_id})")
        
        # Use Twitter API's pagination
        pagination_token = None
        pages_collected = 0
        
        while running:
            try:
                # Call Twitter API
                tweets_response = collector.get_user_tweets(
                    user_id=account_id,
                    max_results=PER_PAGE_MAX_RESULTS,
                    pagination_token=pagination_token
                )
                
                if not tweets_response or "data" not in tweets_response:
                    break
                
                tweets_data = tweets_response["data"]
                
                # Save to MongoDB
                saved = save_tweets_to_mongodb(tweets_data)
                total_saved += saved
                
                # Track newest tweet ID from first page
                if pages_collected == 0 and tweets_data:
                    newest_tweet_id = tweets_data[0]["id"]
                
                pages_collected += 1
                
                # Check for more pages
                pagination_token = tweets_response.get("meta", {}).get("next_token")
                if not pagination_token:
                    break
                
                # Check page limit if configured
                if PER_ACCOUNT_MAX_PAGES > 0 and pages_collected >= PER_ACCOUNT_MAX_PAGES:
                    logger.info(f"Reached max pages ({PER_ACCOUNT_MAX_PAGES}) for @{username}")
                    break
                
                # Small delay between pages
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error collecting page {pages_collected + 1} for @{username}: {e}")
                break
        
        # Update collection state in MongoDB
        if total_saved > 0 or newest_tweet_id:
            update_collection_state(
                key=state_key,
                last_run=datetime.now(timezone.utc),
                last_tweet_id=newest_tweet_id,
                tweets_collected=total_saved
            )
        
        logger.info(f"Saved {total_saved} tweets for @{username}")
        
    except Exception as e:
        logger.error(f"Error collecting tweets for @{username}: {e}")
    
    return total_saved, newest_tweet_id

def run_collection_cycle():
    """
    Run one complete collection cycle for all accounts using MongoDB.
    """
    logger.info("=" * 60)
    logger.info("Starting collection cycle with MongoDB")
    
    total_tweets = 0
    accounts_processed = 0
    
    # Initialize collector
    rate_limiter = get_persistent_rate_limiter()
    collector = TwitterCollector(rate_limiter=rate_limiter)
    
    # Collect for each account
    for account_id, username in ACCOUNTS_TO_FOLLOW.items():
        if not running:
            logger.info("Stopping collection due to shutdown signal")
            break
        
        try:
            saved, newest_id = collect_account_tweets(collector, account_id, username)
            total_tweets += saved
            accounts_processed += 1
            
            # Delay between accounts
            if accounts_processed < len(ACCOUNTS_TO_FOLLOW):
                time.sleep(INTER_ACCOUNT_DELAY_SECONDS)
                
        except Exception as e:
            logger.error(f"Unexpected error for @{username}: {e}")
            continue
    
    # Summary
    logger.info(f"Collection cycle complete: {total_tweets} tweets from {accounts_processed} accounts")
    
    # Get overall stats from MongoDB
    total_in_db = db.tweets.count_documents({})
    unique_authors = len(db.tweets.distinct("author_username"))
    
    logger.info(f"Database totals: {total_in_db} tweets, {unique_authors} unique authors")
    logger.info("=" * 60)

def main():
    """
    Main service loop using MongoDB.
    """
    logger.info("Starting Tweet Collector Service with MongoDB")
    logger.info(f"MongoDB URL: {MONGODB_URL}")
    logger.info(f"Collection interval: {COLLECTION_INTERVAL_SECONDS} seconds")
    logger.info(f"Accounts to follow: {list(ACCOUNTS_TO_FOLLOW.values())}")
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Ensure MongoDB collections have proper indexes
    db.tweets.create_index([("created_at", DESCENDING)])
    db.tweets.create_index([("author_username", ASCENDING)])
    db.collection_state.create_index([("key", ASCENDING)], unique=True)
    
    # Main loop
    while running:
        try:
            # Run collection
            run_collection_cycle()
            
            if not running:
                break
            
            # Sleep until next cycle
            jitter_sleep(COLLECTION_INTERVAL_SECONDS)
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
            break
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
            # Wait a bit before retrying
            time.sleep(60)
    
    # Cleanup
    mongo_client.close()
    logger.info("Tweet Collector Service stopped")

if __name__ == "__main__":
    main()