#!/usr/bin/env python3
"""
Update existing tweets with missing media by re-fetching from Twitter API
"""

import os
import sys
import tweepy
import time
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')
db = client.smarttrendtracer

# Twitter API setup
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
if not BEARER_TOKEN:
    print("❌ TWITTER_BEARER_TOKEN not found in environment")
    sys.exit(1)

# Create Twitter client
twitter_client = tweepy.Client(bearer_token=BEARER_TOKEN)

def update_tweets_with_media(username='emollick', limit=50):
    """
    Update recent tweets with media information
    """
    print(f"🔍 Updating media for @{username} tweets")
    print("=" * 60)
    
    # Get recent tweets from database
    recent_tweets = list(db.tweets.find({
        'author_username': username,
        '$or': [
            {'media': []},
            {'media': {'$exists': False}},
            {'media_count': 0},
            {'media_count': {'$exists': False}}
        ]
    }).sort('created_at', -1).limit(limit))
    
    print(f"Found {len(recent_tweets)} tweets without media")
    
    if not recent_tweets:
        print("No tweets to update")
        return
    
    # Collect tweet IDs
    tweet_ids = [str(tweet['_id']) for tweet in recent_tweets]
    
    # Fetch tweets from Twitter API in batches of 100
    batch_size = 100
    updated_count = 0
    
    for i in range(0, len(tweet_ids), batch_size):
        batch_ids = tweet_ids[i:i+batch_size]
        
        try:
            print(f"\n📡 Fetching batch {i//batch_size + 1} ({len(batch_ids)} tweets)")
            
            # Get tweets with media expansion
            tweets_response = twitter_client.get_tweets(
                ids=batch_ids,
                tweet_fields=['created_at', 'public_metrics', 'referenced_tweets', 'entities', 'attachments'],
                media_fields=['url', 'preview_image_url', 'alt_text', 'width', 'height', 'type', 'duration_ms', 'media_key'],
                expansions=['attachments.media_keys']
            )
            
            if not tweets_response or not tweets_response.data:
                print("  No data returned")
                continue
            
            # Process media
            media_dict = {}
            if tweets_response.includes and 'media' in tweets_response.includes:
                print(f"  📸 Found {len(tweets_response.includes['media'])} media items")
                for media in tweets_response.includes['media']:
                    media_dict[media.media_key] = media.data
            
            # Update tweets with media
            for tweet in tweets_response.data:
                tweet_data = tweet.data
                
                # Check for attachments
                if 'attachments' in tweet_data and 'media_keys' in tweet_data['attachments']:
                    media_list = []
                    for media_key in tweet_data['attachments']['media_keys']:
                        if media_key in media_dict:
                            m = media_dict[media_key]
                            media_list.append({
                                "media_key": media_key,
                                "type": m.get("type"),
                                "url": m.get("url"),
                                "preview_image_url": m.get("preview_image_url"),
                                "alt_text": m.get("alt_text"),
                                "width": m.get("width"),
                                "height": m.get("height"),
                                "duration_ms": m.get("duration_ms")
                            })
                    
                    if media_list:
                        # Update tweet in database - tweet ID should be string
                        tweet_id = str(tweet_data['id'])
                        result = db.tweets.update_one(
                            {"_id": tweet_id},
                            {"$set": {
                                "media": media_list,
                                "media_count": len(media_list)
                            }}
                        )
                        
                        if result.modified_count > 0:
                            updated_count += 1
                            print(f"  ✅ Updated tweet {tweet_data['id']} with {len(media_list)} media items")
                            
                            # Show first media URL
                            if media_list[0].get('url'):
                                print(f"     Preview: {media_list[0]['url'][:80]}...")
            
            # Rate limiting - be respectful
            time.sleep(1)
            
        except tweepy.errors.TooManyRequests:
            print("⏱️ Rate limit reached. Please wait 15 minutes and try again.")
            break
        except Exception as e:
            print(f"❌ Error processing batch: {e}")
            continue
    
    print(f"\n📊 Summary:")
    print(f"  Total tweets checked: {len(recent_tweets)}")
    print(f"  Tweets updated with media: {updated_count}")
    
    # Show current stats
    total_with_media = db.tweets.count_documents({
        'author_username': username,
        'media_count': {'$gt': 0}
    })
    print(f"  Total @{username} tweets with media in DB: {total_with_media}")

if __name__ == "__main__":
    # Update media for specific accounts
    accounts = ['emollick', 'sama', 'OpenAI', 'AnthropicAI']
    
    for account in accounts:
        try:
            update_tweets_with_media(account, limit=20)
            time.sleep(2)  # Small delay between accounts
        except tweepy.errors.TooManyRequests:
            print(f"⏱️ Rate limit hit. Stopping updates.")
            break
        except Exception as e:
            print(f"Error updating {account}: {e}")
            continue