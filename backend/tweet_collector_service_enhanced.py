#!/usr/bin/env python3
"""
Enhanced MongoDB-based Tweet Collector Service
- Fetches full text for retweets (not truncated)
- Includes media from original tweets in retweets
- Uses MongoDB for all data storage
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
# Main collection interval (default 15 min)
COLLECTION_INTERVAL_SECONDS = int(os.getenv("COLLECTION_INTERVAL_SECONDS", "900"))
# Minimum minutes between runs (for multi-instance safety)
MIN_SKIP_MINUTES = float(os.getenv("MIN_SKIP_MINUTES", "5"))
# Delay between accounts to be nice to API
INTER_ACCOUNT_DELAY_SECONDS = float(os.getenv("INTER_ACCOUNT_DELAY_SECONDS", "2"))
# Add +/- jitter (fraction) to main sleep to avoid synchronized clients
SLEEP_JITTER_PCT = float(os.getenv("SLEEP_JITTER_PCT", "0.1"))
# Max tweets per page (most APIs allow up to 100)
PER_PAGE_MAX_RESULTS = int(os.getenv("PER_PAGE_MAX_RESULTS", "50"))
# Max pages to fetch per account (prevent runaway)
MAX_PAGES_PER_ACCOUNT = int(os.getenv("MAX_PAGES_PER_ACCOUNT", "10"))

# =========================
# Twitter API Configuration
# =========================
def get_tweepy_client() -> tweepy.Client:
    """Initialize Tweepy client."""
    bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
    if not bearer_token:
        raise ValueError("TWITTER_BEARER_TOKEN environment variable not set")
    return tweepy.Client(bearer_token=bearer_token)

# =========================
# Logging Setup
# =========================
def setup_logging():
    """Configure logging with rotation."""
    Path("logs").mkdir(exist_ok=True)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
    console_handler.setFormatter(console_formatter)
    
    # File handler with rotation
    file_handler = TimedRotatingFileHandler(
        filename="tweet_collector_mongodb.log",
        when="midnight",
        interval=1,
        backupCount=7
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logging()

# =========================
# Graceful Shutdown
# =========================
running = True

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global running
    logger.info(f"🛑 Received signal {signum}. Shutting down gracefully...")
    running = False

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# =========================
# MongoDB State Management
# =========================
def get_collection_state(key: str) -> Optional[Dict[str, Any]]:
    """Get collection state from MongoDB."""
    return db.collection_state.find_one({"_id": key})

def update_collection_state(key: str, state: Dict[str, Any]):
    """Update collection state in MongoDB."""
    state["_id"] = key
    state["updated_at"] = datetime.now(timezone.utc)
    db.collection_state.replace_one({"_id": key}, state, upsert=True)

# =========================
# Core Collection Logic
# =========================
def save_tweets_to_mongodb(tweets_data: List[dict], username: str) -> int:
    """
    Save tweets to MongoDB, handling duplicates.
    Returns the number of tweets saved.
    """
    saved_count = 0
    
    for tweet_data in tweets_data:
        try:
            tweet_id = tweet_data.get("id")
            if not tweet_id:
                continue
            
            # Check if tweet already exists
            if db.tweets.find_one({"_id": tweet_id}):
                logger.debug(f"Tweet {tweet_id} already exists, skipping")
                continue
            
            # Extract author info
            author = tweet_data.get("author", {})
            
            # Parse created_at timestamp
            created_at_str = tweet_data.get("created_at")
            created_at = None
            if created_at_str:
                # Twitter API returns ISO format with Z suffix
                if created_at_str.endswith('Z'):
                    created_at_str = created_at_str[:-1] + '+00:00'
                created_at = datetime.fromisoformat(created_at_str)
            
            # Build tweet document for MongoDB
            tweet_doc = {
                "_id": tweet_id,  # Use Twitter's ID as MongoDB _id
                "text": tweet_data.get("text", ""),
                "full_text": tweet_data.get("full_text", ""),  # Store full text if available
                "author_id": tweet_data.get("author_id"),
                "author_username": author.get("username", username),
                "created_at": created_at,
                "collected_at": datetime.now(timezone.utc),
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
                "original_media": [],  # Media from original tweet if this is a retweet
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
            
            # If this is a retweet, store the original tweet's data
            if "referenced_tweet_data" in tweet_data:
                original = tweet_data["referenced_tweet_data"]
                # Store the full text from the original tweet
                tweet_doc["full_text"] = original.get("text", tweet_doc["text"])
                
                # Store media from original tweet
                if "media" in original:
                    for media in original["media"]:
                        tweet_doc["original_media"].append({
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

def collect_account_tweets(client: tweepy.Client, account_id: str, 
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
                # Ensure last_run has timezone info
                if last_run.tzinfo is None:
                    # Assume naive datetime is UTC
                    last_run = last_run.replace(tzinfo=timezone.utc)
                
                # Check if we've collected recently
                minutes_since = (datetime.now(timezone.utc) - last_run).total_seconds() / 60
                if minutes_since < MIN_SKIP_MINUTES:
                    logger.info(f"Skipping @{username} - collected {minutes_since:.1f} minutes ago")
                    return 0, None
        
        # Get the last tweet ID we collected for this account
        since_id = None
        if state and state.get("last_tweet_id"):
            since_id = state.get("last_tweet_id")
            logger.info(f"📍 Using since_id: {since_id} (only fetching newer tweets)")
        else:
            logger.info(f"🆕 First time collecting for @{username} or no previous state")
        
        # Collect tweets with pagination
        logger.info(f"Collecting tweets for @{username} (ID: {account_id})")
        
        # Use Twitter API's pagination
        pagination_token = None
        pages_collected = 0
        
        while running:
            try:
                # Call Twitter API using Tweepy - with since_id to get only new tweets
                api_params = {
                    'id': account_id,
                    'max_results': PER_PAGE_MAX_RESULTS,
                    'pagination_token': pagination_token,
                    'tweet_fields': ['created_at', 'public_metrics', 'referenced_tweets', 'entities', 'attachments'],
                    'media_fields': ['url', 'preview_image_url', 'alt_text', 'width', 'height', 'type', 'duration_ms'],
                    # IMPORTANT: Add referenced_tweets.id to get full original tweets
                    'expansions': ['attachments.media_keys', 'author_id', 'referenced_tweets.id']
                }
                
                # Add since_id if we have it - this gets only tweets newer than this ID
                if since_id:
                    api_params['since_id'] = since_id
                
                tweets_response = client.get_users_tweets(**api_params)
                
                if not tweets_response or not tweets_response.data:
                    break
                
                # Convert Response objects to dicts
                tweets_data = []
                media_dict = {}
                referenced_tweets_dict = {}
                
                # Process media if available
                if tweets_response.includes and 'media' in tweets_response.includes:
                    for media in tweets_response.includes['media']:
                        media_dict[media.media_key] = media.data
                
                # Process referenced tweets (original tweets for retweets)
                if tweets_response.includes and 'tweets' in tweets_response.includes:
                    for ref_tweet in tweets_response.includes['tweets']:
                        referenced_tweets_dict[ref_tweet.id] = ref_tweet.data
                
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
                    
                    # If this is a retweet, get the original tweet's data
                    if 'referenced_tweets' in tweet_dict:
                        for ref in tweet_dict['referenced_tweets']:
                            if ref['type'] == 'retweeted' and ref['id'] in referenced_tweets_dict:
                                original_tweet = referenced_tweets_dict[ref['id']]
                                tweet_dict['referenced_tweet_data'] = original_tweet
                                
                                # Get media from the original tweet
                                if 'attachments' in original_tweet and 'media_keys' in original_tweet['attachments']:
                                    original_tweet['media'] = []
                                    for media_key in original_tweet['attachments']['media_keys']:
                                        if media_key in media_dict:
                                            original_tweet['media'].append(media_dict[media_key])
                    
                    tweets_data.append(tweet_dict)
                
                # Track newest tweet for state
                if tweets_data and not newest_tweet_id:
                    newest_tweet_id = tweets_data[0].get('id')
                
                # Save tweets to MongoDB
                saved = save_tweets_to_mongodb(tweets_data, username)
                total_saved += saved
                
                logger.info(f"  Page {pages_collected + 1}: Saved {saved}/{len(tweets_data)} tweets")
                
                # Get next page token
                if tweets_response.meta and 'next_token' in tweets_response.meta:
                    pagination_token = tweets_response.meta['next_token']
                    pages_collected += 1
                    if pages_collected >= MAX_PAGES_PER_ACCOUNT:
                        logger.info(f"  Reached max pages ({MAX_PAGES_PER_ACCOUNT}), stopping")
                        break
                else:
                    # No more pages
                    break
                    
            except tweepy.TooManyRequests as e:
                logger.warning(f"Rate limit reached: {e}")
                logger.info("Waiting 15 minutes before retrying...")
                time.sleep(900)  # Wait 15 minutes
                continue
            except Exception as e:
                logger.error(f"Error fetching page: {e}")
                break
        
        # Update state with the newest tweet ID
        if newest_tweet_id:
            update_collection_state(state_key, {
                "last_tweet_id": newest_tweet_id,
                "last_run": datetime.now(timezone.utc),
                "tweets_collected": total_saved
            })
        elif state:
            # Even if no new tweets, update last_run
            state["last_run"] = datetime.now(timezone.utc)
            update_collection_state(state_key, state)
        
        return total_saved, newest_tweet_id
        
    except Exception as e:
        logger.error(f"Error collecting tweets for @{username}: {e}")
        return total_saved, newest_tweet_id

def collect_all_accounts(client: tweepy.Client) -> int:
    """Collect tweets for all configured accounts."""
    total_collected = 0
    
    for account in ACCOUNTS_TO_FOLLOW:
        if not running:
            break
            
        account_id = account["id"]
        username = account["username"]
        
        try:
            tweets_saved, newest_id = collect_account_tweets(client, account_id, username)
            total_collected += tweets_saved
            
            if tweets_saved > 0:
                logger.info(f"✅ Collected {tweets_saved} new tweets from @{username}")
            else:
                logger.info(f"📭 No new tweets from @{username}")
                
            # Small delay between accounts
            if running:
                time.sleep(INTER_ACCOUNT_DELAY_SECONDS)
                
        except Exception as e:
            logger.error(f"Failed to collect from @{username}: {e}")
            continue
    
    return total_collected

def test_twitter_connection(client: tweepy.Client) -> bool:
    """Test if Twitter API connection works."""
    try:
        # Try to get user info for @Twitter
        test_user_id = "783214"  # Twitter's official account
        test_response = client.get_user(id=test_user_id, user_fields=['username', 'name'])
        
        if test_response and test_response.data:
            logger.info(f"✅ Twitter API connection successful: {test_response.data.username}")
            return True
        else:
            logger.error("❌ Twitter API returned no data")
            return False
            
    except Exception as e:
        logger.error(f"❌ Twitter API connection failed: {e}")
        return False

def main():
    """Main collection loop with MongoDB."""
    logger.info("=" * 60)
    logger.info("🚀 MongoDB Tweet Collector Service Starting...")
    logger.info(f"Collection interval: {COLLECTION_INTERVAL_SECONDS} seconds")
    logger.info(f"Accounts to follow: {len(ACCOUNTS_TO_FOLLOW)}")
    logger.info("=" * 60)
    
    # Initialize Twitter client
    try:
        client = get_tweepy_client()
    except Exception as e:
        logger.error(f"Failed to initialize Twitter client: {e}")
        return
    
    # Test connection
    if not test_twitter_connection(client):
        logger.error("Cannot proceed without Twitter API connection")
        return
    
    # Test MongoDB connection
    try:
        db.command('ping')
        logger.info("✅ MongoDB connection successful")
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        return
    
    iteration = 0
    while running:
        iteration += 1
        logger.info(f"\n🔄 Starting collection iteration #{iteration}")
        
        try:
            start_time = time.time()
            total_collected = collect_all_accounts(client)
            elapsed = time.time() - start_time
            
            logger.info(f"📊 Iteration #{iteration} complete: {total_collected} tweets in {elapsed:.1f}s")
            
            # Calculate sleep time with jitter
            base_sleep = COLLECTION_INTERVAL_SECONDS
            jitter = random.uniform(-SLEEP_JITTER_PCT, SLEEP_JITTER_PCT) * base_sleep
            sleep_time = max(60, base_sleep + jitter)  # At least 1 minute
            
            if running:
                logger.info(f"💤 Sleeping for {sleep_time:.0f} seconds (until {(datetime.now() + timedelta(seconds=sleep_time)).strftime('%H:%M:%S')})...")
                
                # Sleep in small chunks to allow for graceful shutdown
                sleep_end = time.time() + sleep_time
                while running and time.time() < sleep_end:
                    time.sleep(min(10, sleep_end - time.time()))
                    
        except Exception as e:
            logger.error(f"Error in collection iteration: {e}")
            if running:
                logger.info("Waiting 60 seconds before retry...")
                time.sleep(60)
    
    logger.info("👋 Tweet collector service stopped")

if __name__ == "__main__":
    main()