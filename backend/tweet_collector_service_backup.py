#!/usr/bin/env python3
"""
MongoDB-based Tweet Collector Service with Intelligent Rate Limit Handling
- Smart rate limit management with exponential backoff
- Batch collection with proper timing between batches
- Tracks rate limit windows and respects reset times
- Adaptive collection based on API response headers
- Robust error handling and graceful degradation
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
from collections import deque
import threading

# Ensure relative imports work when invoked as a script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(usecwd=True))

from pymongo import MongoClient, ASCENDING, DESCENDING
import tweepy
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
# Main collection interval (default 30 min for 15 accounts)
COLLECTION_INTERVAL_SECONDS = int(os.getenv("COLLECTION_INTERVAL_SECONDS", "1800"))
# Batch size - how many accounts to collect before longer pause
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "3"))
# Delay between accounts in same batch
INTRA_BATCH_DELAY_SECONDS = float(os.getenv("INTRA_BATCH_DELAY_SECONDS", "5"))
# Delay between batches (longer pause)
INTER_BATCH_DELAY_SECONDS = float(os.getenv("INTER_BATCH_DELAY_SECONDS", "60"))
# Initial backoff time when rate limited (seconds)
INITIAL_BACKOFF_SECONDS = float(os.getenv("INITIAL_BACKOFF_SECONDS", "60"))
# Maximum backoff time (seconds)
MAX_BACKOFF_SECONDS = float(os.getenv("MAX_BACKOFF_SECONDS", "900"))  # 15 minutes
# Max tweets per page (most APIs allow up to 100)
PER_PAGE_MAX_RESULTS = int(os.getenv("PER_PAGE_MAX_RESULTS", "100"))
# Maximum pages per account to prevent excessive API usage
MAX_PAGES_PER_ACCOUNT = int(os.getenv('MAX_PAGES_PER_ACCOUNT', '5'))
# Maximum retry attempts for rate limited requests
MAX_RETRY_ATTEMPTS = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))

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
# Rate Limit Tracking
# =========================
class RateLimitTracker:
    """Track rate limits and manage backoff strategies"""
    
    def __init__(self):
        self.reset_time = None
        self.remaining_requests = None
        self.limit = None
        self.backoff_seconds = INITIAL_BACKOFF_SECONDS
        self.consecutive_rate_limits = 0
        self.last_rate_limit_time = None
        self.account_backoffs = {}  # Per-account backoff tracking
        
    def update_from_response(self, response):
        """Update rate limit info from API response headers"""
        if hasattr(response, 'headers'):
            headers = response.headers
            if 'x-rate-limit-remaining' in headers:
                self.remaining_requests = int(headers['x-rate-limit-remaining'])
            if 'x-rate-limit-reset' in headers:
                self.reset_time = datetime.fromtimestamp(
                    int(headers['x-rate-limit-reset']), 
                    tz=timezone.utc
                )
            if 'x-rate-limit-limit' in headers:
                self.limit = int(headers['x-rate-limit-limit'])
    
    def hit_rate_limit(self, account_username=None):
        """Called when we hit a rate limit"""
        self.consecutive_rate_limits += 1
        self.last_rate_limit_time = datetime.now(timezone.utc)
        
        # Exponential backoff
        self.backoff_seconds = min(
            self.backoff_seconds * 2,
            MAX_BACKOFF_SECONDS
        )
        
        # Track per-account if provided
        if account_username:
            if account_username not in self.account_backoffs:
                self.account_backoffs[account_username] = INITIAL_BACKOFF_SECONDS
            else:
                self.account_backoffs[account_username] = min(
                    self.account_backoffs[account_username] * 2,
                    MAX_BACKOFF_SECONDS
                )
    
    def reset_backoff(self, account_username=None):
        """Reset backoff when successful"""
        self.consecutive_rate_limits = 0
        self.backoff_seconds = INITIAL_BACKOFF_SECONDS
        
        if account_username and account_username in self.account_backoffs:
            self.account_backoffs[account_username] = INITIAL_BACKOFF_SECONDS
    
    def get_wait_time(self, account_username=None):
        """Get how long to wait before next request"""
        # If we have reset time from headers, use that
        if self.reset_time:
            wait_from_reset = (self.reset_time - datetime.now(timezone.utc)).total_seconds()
            if wait_from_reset > 0:
                return wait_from_reset + 5  # Add 5 second buffer
        
        # Use per-account backoff if available
        if account_username and account_username in self.account_backoffs:
            return self.account_backoffs[account_username]
        
        # Otherwise use global backoff
        return self.backoff_seconds
    
    def should_pause_collection(self):
        """Determine if we should pause all collection"""
        # If we've hit rate limits multiple times recently, take a longer break
        if self.consecutive_rate_limits >= 3:
            return True
        
        # If we have very few requests remaining, pause
        if self.remaining_requests is not None and self.remaining_requests < 5:
            return True
        
        return False

rate_limiter = RateLimitTracker()

# =========================
# Shutdown handling
# =========================
running = True

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global running
    signal_name = "SIGINT (Ctrl+C)" if signum == signal.SIGINT else f"Signal {signum}"
    logger.info("\n" + "=" * 50)
    logger.info(f"🛑 {signal_name} received - Gracefully shutting down...")
    logger.info("=" * 50)
    running = False

# =========================
# Helper utilities
# =========================

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

def process_urls_with_previews(urls: List[Dict]) -> List[Dict]:
    """
    Process URL entities to include preview data from Twitter Cards
    """
    processed_urls = []
    for url in urls:
        processed_url = {
            'url': url.get('url'),
            'expanded_url': url.get('expanded_url'),
            'display_url': url.get('display_url'),
            'title': url.get('title'),  # Twitter Card title
            'description': url.get('description'),  # Twitter Card description
            'unwound_url': url.get('unwound_url'),
        }
        
        # Add image previews if available
        if url.get('images'):
            processed_url['preview_images'] = url.get('images')
            # Use the first image as the main preview
            if len(url['images']) > 0:
                processed_url['preview_image_url'] = url['images'][0].get('url')
        
        processed_urls.append(processed_url)
    
    return processed_urls

def save_tweets_to_mongodb(tweets_data: List[Dict]) -> tuple[int, bool]:
    """
    Save tweets to MongoDB.
    Returns a tuple of (number of new tweets saved, should_continue_pagination).
    
    If we encounter tweets we already have, we return should_continue_pagination=False
    to stop fetching more pages.
    """
    if not tweets_data:
        return 0, False
    
    saved_count = 0
    found_existing_count = 0
    
    for tweet_data in tweets_data:
        try:
            # Check if tweet already exists
            existing = db.tweets.find_one({"_id": tweet_data["id"]})
            
            if existing:
                found_existing_count += 1
            else:
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
                    "urls": process_urls_with_previews(tweet_data.get("entities", {}).get("urls", [])),
                    "referenced_tweets": tweet_data.get("referenced_tweets", []),
                    "media": [],  # Will be added if media exists
                    "media_count": 0,  # Track number of media items
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
                    tweet_doc["media_count"] = len(tweet_doc["media"])
                
                # Insert tweet
                db.tweets.insert_one(tweet_doc)
                saved_count += 1
                
        except Exception as e:
            logger.error(f"Error saving tweet {tweet_data.get('id')}: {e}")
            continue
    
    # Decision logic: Stop pagination if we found mostly existing tweets
    # If more than 80% of tweets on this page were already in DB, stop fetching more pages
    total_tweets = len(tweets_data)
    should_continue = True
    
    if found_existing_count > 0:
        existing_ratio = found_existing_count / total_tweets
        if existing_ratio > 0.8:  # More than 80% were duplicates
            should_continue = False
            logger.info(f"📊 Found {found_existing_count}/{total_tweets} existing tweets ({existing_ratio*100:.0f}%), stopping pagination")
    
    return saved_count, should_continue

def collect_account_tweets_with_retry(client: tweepy.Client, account_id: str, 
                                     username: str, retry_attempt: int = 0) -> Tuple[int, Optional[str]]:
    """
    Collect tweets for a single account with retry logic and rate limit handling.
    Returns (total_tweets_saved, newest_tweet_id).
    """
    total_saved = 0
    newest_tweet_id = None
    state_key = f"twitter_{username}"
    
    try:
        # Get last collection state from MongoDB
        state = get_collection_state(state_key)
        
        # Get the last tweet ID we collected for this account
        since_id = None
        if state and state.get("last_tweet_id"):
            since_id = state.get("last_tweet_id")
            logger.info(f"📍 Using since_id: {since_id} for @{username}")
        else:
            logger.info(f"🆕 First time collecting for @{username}")
        
        # Collect tweets with pagination
        logger.info(f"Collecting tweets for @{username} (ID: {account_id})")
        
        # Use Twitter API's pagination
        pagination_token = None
        pages_collected = 0
        consecutive_errors = 0
        
        while running and consecutive_errors < 3:
            try:
                # Call Twitter API using Tweepy
                api_params = {
                    'id': account_id,
                    'max_results': PER_PAGE_MAX_RESULTS,
                    'pagination_token': pagination_token,
                    'tweet_fields': ['created_at', 'public_metrics', 'referenced_tweets', 'entities', 'attachments'],
                    'media_fields': ['url', 'preview_image_url', 'alt_text', 'width', 'height', 'type', 'duration_ms'],
                    'expansions': ['attachments.media_keys', 'author_id']
                }
                
                # Add since_id if we have it - this gets only tweets newer than this ID
                if since_id:
                    api_params['since_id'] = since_id
                
                tweets_response = client.get_users_tweets(**api_params)
                
                # Update rate limit tracker if we have response headers
                rate_limiter.update_from_response(tweets_response)
                
                if not tweets_response or not tweets_response.data:
                    break
                
                # Convert Response objects to dicts
                tweets_data = []
                media_dict = {}
                
                # Process media if available
                if tweets_response.includes and 'media' in tweets_response.includes:
                    for media in tweets_response.includes['media']:
                        media_dict[media.media_key] = media.data
                
                # Process tweets
                for tweet in tweets_response.data:
                    tweet_dict = tweet.data
                    tweet_dict['author'] = {'username': username}
                    
                    # Add media if present
                    if 'attachments' in tweet_dict and 'media_keys' in tweet_dict['attachments']:
                        tweet_dict['media'] = []
                        for media_key in tweet_dict['attachments']['media_keys']:
                            if media_key in media_dict:
                                tweet_dict['media'].append(media_dict[media_key])
                    
                    tweets_data.append(tweet_dict)
                
                # Save to MongoDB
                saved, should_continue = save_tweets_to_mongodb(tweets_data)
                total_saved += saved
                
                # Track newest tweet ID from first page
                if pages_collected == 0 and tweets_data:
                    newest_tweet_id = tweets_data[0]["id"]
                
                pages_collected += 1
                consecutive_errors = 0  # Reset error counter on success
                rate_limiter.reset_backoff(username)  # Reset backoff on success
                
                logger.info(f"✅ Page {pages_collected} for @{username}: {saved} tweets saved")
                
                # Stop if we've found mostly existing tweets
                if not should_continue:
                    logger.info(f"🛑 Stopping pagination for @{username} - reached existing tweets")
                    break
                
                # Stop if we've reached max pages limit
                if pages_collected >= MAX_PAGES_PER_ACCOUNT:
                    logger.info(f"📄 Reached max pages limit ({MAX_PAGES_PER_ACCOUNT}) for @{username}")
                    break
                
                # Check for more pages
                pagination_token = tweets_response.meta.get("next_token") if tweets_response.meta else None
                if not pagination_token:
                    break
                
                # Smart delay between pages based on rate limit status
                if rate_limiter.remaining_requests and rate_limiter.remaining_requests < 10:
                    wait_time = rate_limiter.get_wait_time(username)
                    logger.info(f"⏸️ Low on API calls ({rate_limiter.remaining_requests} remaining), waiting {wait_time:.0f}s...")
                    time.sleep(wait_time)
                else:
                    time.sleep(2)  # Normal delay between pages
                
            except Exception as e:
                error_msg = str(e)
                consecutive_errors += 1
                
                if "429" in error_msg or "Too Many Requests" in error_msg:
                    rate_limiter.hit_rate_limit(username)
                    
                    # Check if this is user timeline specific rate limit
                    if "User" in error_msg or "timeline" in error_msg.lower():
                        # User timeline has its own rate limit (75 requests per 15 min window)
                        logger.info(f"📝 Hit user timeline rate limit (75 req/15min window)")
                        wait_time = 900  # Wait full 15 minute window for timeline limits
                    else:
                        wait_time = rate_limiter.get_wait_time(username)
                    
                    if retry_attempt < MAX_RETRY_ATTEMPTS:
                        logger.warning(f"⏱️ Rate limit hit for @{username} (attempt {retry_attempt + 1}/{MAX_RETRY_ATTEMPTS})")
                        logger.info(f"⏳ Waiting {wait_time:.0f} seconds ({wait_time/60:.1f} minutes) before retry...")
                        
                        # For long waits, show progress
                        if wait_time > 120:
                            for i in range(0, int(wait_time), 60):
                                if not running:
                                    break
                                remaining = wait_time - i
                                if remaining > 60:
                                    logger.info(f"   ... {remaining/60:.0f} minutes remaining")
                                    time.sleep(60)
                                else:
                                    time.sleep(remaining)
                                    break
                        else:
                            time.sleep(wait_time)
                        
                        # Recursive retry with incremented attempt counter
                        return collect_account_tweets_with_retry(
                            client, account_id, username, retry_attempt + 1
                        )
                    else:
                        logger.error(f"❌ Max retries reached for @{username}, skipping")
                        break
                        
                elif "401" in error_msg or "Unauthorized" in error_msg:
                    logger.error(f"🔒 Authentication error for @{username}: {error_msg}")
                    break
                elif "403" in error_msg or "Forbidden" in error_msg:
                    logger.error(f"🚫 Access forbidden for @{username}: {error_msg}")
                    break
                else:
                    logger.error(f"❌ Error on page {pages_collected + 1} for @{username}: {error_msg}")
                    if consecutive_errors >= 3:
                        logger.error(f"Too many consecutive errors for @{username}, stopping")
                        break
                    time.sleep(5)  # Brief pause before retry
        
        # Update collection state in MongoDB
        if total_saved > 0 or newest_tweet_id:
            update_collection_state(
                key=state_key,
                last_run=datetime.now(timezone.utc),
                last_tweet_id=newest_tweet_id,
                tweets_collected=total_saved
            )
        
        logger.info(f"📊 Total saved for @{username}: {total_saved} tweets across {pages_collected} pages")
        
    except Exception as e:
        logger.error(f"Error collecting tweets for @{username}: {e}")
    
    return total_saved, newest_tweet_id

def run_collection_cycle():
    """
    Run one complete collection cycle for all accounts with intelligent batching.
    """
    logger.info("=" * 60)
    logger.info("🚀 Starting collection cycle with improved rate limit handling")
    logger.info(f"📝 Collecting from {len(ACCOUNTS_TO_FOLLOW)} accounts in batches of {BATCH_SIZE}")
    
    total_tweets = 0
    accounts_processed = 0
    accounts_skipped = 0
    
    # Initialize Tweepy client
    bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
    if not bearer_token:
        logger.error("❌ TWITTER_BEARER_TOKEN not found in environment variables")
        logger.error("Please set your Twitter Bearer Token: export TWITTER_BEARER_TOKEN='your_token_here'")
        return
    
    logger.info(f"🔑 Using Twitter Bearer Token: {bearer_token[:10]}...{bearer_token[-4:]}")
    client = tweepy.Client(bearer_token=bearer_token, wait_on_rate_limit=False)
    
    # Test authentication and check rate limit status
    try:
        logger.info("🔍 Testing Twitter API authentication and rate limit status...")
        test_response = client.get_user(id=ACCOUNTS_TO_FOLLOW[0].get('id'))
        if test_response and test_response.data:
            logger.info(f"✅ Authentication successful!")
            rate_limiter.update_from_response(test_response)
            if rate_limiter.remaining_requests:
                logger.info(f"📊 Rate limit status: {rate_limiter.remaining_requests} requests remaining")
                if rate_limiter.remaining_requests < 5:
                    wait_time = rate_limiter.get_wait_time()
                    logger.warning(f"⚠️ Very low on API calls. Waiting {wait_time:.0f}s for rate limit reset...")
                    time.sleep(wait_time)
    except Exception as auth_error:
        if "429" in str(auth_error):
            # We're rate limited from the start - need to wait for reset
            logger.warning("⏱️ Already rate limited! Need to wait for reset window...")
            
            # Try to get reset time from a lightweight endpoint
            try:
                # Use application rate limit status endpoint (lighter weight)
                import requests
                headers = {'Authorization': f'Bearer {bearer_token}'}
                response = requests.get(
                    'https://api.twitter.com/2/tweets/1',  # Minimal endpoint
                    headers=headers
                )
                if 'x-rate-limit-reset' in response.headers:
                    reset_time = datetime.fromtimestamp(
                        int(response.headers['x-rate-limit-reset']),
                        tz=timezone.utc
                    )
                    wait_seconds = (reset_time - datetime.now(timezone.utc)).total_seconds()
                    if wait_seconds > 0:
                        logger.info(f"📅 Rate limit resets at: {reset_time.strftime('%H:%M:%S UTC')}")
                        logger.info(f"⏳ Waiting {wait_seconds:.0f} seconds ({wait_seconds/60:.1f} minutes)...")
                        
                        # Wait in chunks with progress updates
                        total_wait = int(wait_seconds)
                        for i in range(0, total_wait, 60):
                            if not running:
                                break
                            remaining = total_wait - i
                            if remaining > 60:
                                logger.info(f"   ... {remaining//60} minutes remaining")
                                time.sleep(60)
                            else:
                                time.sleep(remaining)
                                break
                        logger.info("✅ Rate limit should be reset, proceeding with collection")
                else:
                    # Fallback to standard wait
                    logger.info("⏳ Waiting 15 minutes for rate limit reset (standard window)...")
                    time.sleep(900)
            except:
                # If we can't get reset time, wait standard 15 minutes
                logger.info("⏳ Waiting 15 minutes for rate limit reset...")
                time.sleep(900)
                
        elif "401" in str(auth_error):
            logger.error(f"❌ Authentication failed: {auth_error}")
            return
    
    # Randomize account order to avoid always hitting the same accounts first
    accounts = ACCOUNTS_TO_FOLLOW.copy()
    random.shuffle(accounts)
    
    # Process accounts in batches
    for batch_num, i in enumerate(range(0, len(accounts), BATCH_SIZE), 1):
        if not running:
            logger.info("Stopping collection due to shutdown signal")
            break
        
        # Check if we should pause due to rate limits
        if rate_limiter.should_pause_collection():
            wait_time = rate_limiter.get_wait_time()
            logger.warning(f"⚠️ Rate limit threshold reached, pausing for {wait_time:.0f} seconds")
            time.sleep(wait_time)
        
        batch = accounts[i:i + BATCH_SIZE]
        logger.info(f"📦 Processing batch {batch_num} ({len(batch)} accounts)")
        
        for account in batch:
            if not running:
                break
            
            account_id = account.get('id')
            username = account.get('username')
            
            if not account_id or not username:
                logger.warning(f"Skipping account with missing data: {account}")
                accounts_skipped += 1
                continue
            
            try:
                saved, newest_id = collect_account_tweets_with_retry(client, account_id, username)
                total_tweets += saved
                accounts_processed += 1
                
                if saved == 0:
                    accounts_skipped += 1
                
                # Delay between accounts in same batch
                if running:
                    time.sleep(INTRA_BATCH_DELAY_SECONDS)
                    
            except Exception as e:
                logger.error(f"Error processing @{username}: {e}")
                accounts_skipped += 1
        
        # Longer delay between batches
        if batch_num * BATCH_SIZE < len(accounts) and running:
            logger.info(f"⏸️ Batch {batch_num} complete. Waiting {INTER_BATCH_DELAY_SECONDS}s before next batch...")
            time.sleep(INTER_BATCH_DELAY_SECONDS)
    
    # Final statistics
    logger.info("=" * 60)
    logger.info(f"📊 Collection cycle complete:")
    logger.info(f"   • Accounts processed: {accounts_processed}/{len(ACCOUNTS_TO_FOLLOW)}")
    logger.info(f"   • Accounts skipped: {accounts_skipped}")
    logger.info(f"   • Total tweets collected: {total_tweets}")
    
    # Database totals
    try:
        total_db_tweets = db.tweets.count_documents({})
        unique_authors = len(db.tweets.distinct("author_username"))
        logger.info(f"   • Database totals: {total_db_tweets} tweets, {unique_authors} unique authors")
    except Exception as e:
        logger.error(f"Error getting database statistics: {e}")
    
    logger.info("=" * 60)

def main():
    """
    Main service loop with intelligent scheduling
    """
    global running  # Declare global variable
    
    logger.info("=" * 50)
    logger.info("🚀 Tweet Collector Service (Enhanced) Starting")
    logger.info(f"📊 Configuration:")
    logger.info(f"   • Collection interval: {COLLECTION_INTERVAL_SECONDS}s")
    logger.info(f"   • Batch size: {BATCH_SIZE} accounts")
    logger.info(f"   • Intra-batch delay: {INTRA_BATCH_DELAY_SECONDS}s")
    logger.info(f"   • Inter-batch delay: {INTER_BATCH_DELAY_SECONDS}s")
    logger.info(f"   • Max retries: {MAX_RETRY_ATTEMPTS}")
    logger.info(f"   • Accounts to follow: {len(ACCOUNTS_TO_FOLLOW)} accounts")
    logger.info("=" * 50)
    
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
            
            # Calculate next run time with some jitter to avoid synchronized collectors
            jitter = random.uniform(-60, 60)  # +/- 1 minute jitter
            sleep_seconds = COLLECTION_INTERVAL_SECONDS + jitter
            sleep_seconds = max(60, sleep_seconds)  # Minimum 1 minute
            
            logger.info(f"💤 Sleeping for {sleep_seconds:.1f} seconds until next cycle...")
            logger.info(f"   (Press Ctrl+C to stop)")
            
            # Sleep in small increments to allow for clean shutdown
            sleep_end = time.time() + sleep_seconds
            while running and time.time() < sleep_end:
                time.sleep(1)
            
        except KeyboardInterrupt:
            logger.info("\n🛑 Keyboard interrupt received - shutting down gracefully...")
            running = False
            break
        except Exception as e:
            logger.error(f"💥 Unexpected error in main loop: {e}")
            if running:  # Only retry if not shutting down
                logger.info("⏳ Waiting 60 seconds before retrying...")
                # Sleep in chunks to allow for shutdown
                for _ in range(60):
                    if not running:
                        break
                    time.sleep(1)
    
    # Cleanup
    logger.info("🧹 Cleaning up resources...")
    try:
        mongo_client.close()
        logger.info("📁 MongoDB connection closed")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
    
    logger.info("" + "=" * 50)
    logger.info("🏁 Tweet Collector Service stopped gracefully")
    logger.info("=" * 50)

if __name__ == "__main__":
    import sys
    
    # Check for --check-rate-limit flag
    if len(sys.argv) > 1 and sys.argv[1] == "--check-rate-limit":
        logger.info("=" * 50)
        logger.info("📊 Checking Twitter API Rate Limit Status")
        logger.info("=" * 50)
        
        bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        if not bearer_token:
            logger.error("❌ TWITTER_BEARER_TOKEN not found")
            sys.exit(1)
        
        try:
            import requests
            headers = {'Authorization': f'Bearer {bearer_token}'}
            
            # Make a minimal API call to check rate limits
            response = requests.get(
                'https://api.twitter.com/2/users/1605',  # Check Sam Altman's account
                headers=headers
            )
            
            if response.status_code == 200:
                logger.info("✅ API is accessible")
                
                if 'x-rate-limit-remaining' in response.headers:
                    remaining = response.headers['x-rate-limit-remaining']
                    limit = response.headers.get('x-rate-limit-limit', 'unknown')
                    reset = response.headers.get('x-rate-limit-reset', 'unknown')
                    
                    logger.info(f"📊 Rate Limit Status:")
                    logger.info(f"   • Remaining calls: {remaining}/{limit}")
                    
                    if reset != 'unknown':
                        reset_time = datetime.fromtimestamp(int(reset), tz=timezone.utc)
                        wait_seconds = (reset_time - datetime.now(timezone.utc)).total_seconds()
                        logger.info(f"   • Reset time: {reset_time.strftime('%H:%M:%S UTC')}")
                        if wait_seconds > 0:
                            logger.info(f"   • Time until reset: {wait_seconds/60:.1f} minutes")
                        else:
                            logger.info(f"   • Rate limit already reset!")
                    
                    if int(remaining) < 5:
                        logger.warning("⚠️ Very low on API calls! Consider waiting for reset.")
                    elif int(remaining) < 50:
                        logger.warning("⚠️ API calls running low. Use cautiously.")
                    else:
                        logger.info("✅ Sufficient API calls available for collection.")
                        
            elif response.status_code == 429:
                logger.error("❌ Currently rate limited!")
                if 'x-rate-limit-reset' in response.headers:
                    reset_time = datetime.fromtimestamp(
                        int(response.headers['x-rate-limit-reset']),
                        tz=timezone.utc
                    )
                    wait_seconds = (reset_time - datetime.now(timezone.utc)).total_seconds()
                    logger.info(f"📅 Rate limit resets at: {reset_time.strftime('%H:%M:%S UTC')}")
                    logger.info(f"⏳ Wait {wait_seconds/60:.1f} minutes before collecting")
            else:
                logger.error(f"❌ API returned status {response.status_code}")
                logger.error(f"Response: {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Error checking rate limit: {e}")
        
        logger.info("=" * 50)
        sys.exit(0)
    
    # Normal operation
    main()