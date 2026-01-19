#!/usr/bin/env python3
"""
Test media collection for tweets
"""

import os
import sys
import tweepy
from datetime import datetime, timezone
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

# Test with @emollick recent tweets
print("🔍 Testing media collection for @emollick")
print("=" * 60)

try:
    # Get user ID for @emollick
    user_response = twitter_client.get_user(username='emollick')
    if not user_response or not user_response.data:
        print("❌ Could not find @emollick")
        sys.exit(1)
    
    user_id = user_response.data.id
    print(f"User ID: {user_id}")
    
    # Get recent tweets with media expansion
    tweets_response = twitter_client.get_users_tweets(
        id=user_id,
        max_results=10,
        tweet_fields=['created_at', 'public_metrics', 'referenced_tweets', 'entities', 'attachments'],
        media_fields=['url', 'preview_image_url', 'alt_text', 'width', 'height', 'type', 'duration_ms', 'media_key'],
        expansions=['attachments.media_keys', 'author_id']
    )
    
    if not tweets_response or not tweets_response.data:
        print("❌ No tweets found")
        sys.exit(1)
    
    # Process media
    media_dict = {}
    if tweets_response.includes and 'media' in tweets_response.includes:
        print(f"\n📸 Found {len(tweets_response.includes['media'])} media items")
        for media in tweets_response.includes['media']:
            media_dict[media.media_key] = media.data
            print(f"  - {media.media_key}: {media.data.get('type')}")
    else:
        print("\n📸 No media found in response")
    
    # Process tweets
    tweets_with_media = 0
    for tweet in tweets_response.data:
        tweet_data = tweet.data
        
        # Check for attachments
        if 'attachments' in tweet_data and 'media_keys' in tweet_data['attachments']:
            tweets_with_media += 1
            print(f"\n✅ Tweet {tweet_data['id']} has media:")
            print(f"   Text: {tweet_data['text'][:100]}...")
            print(f"   Media keys: {tweet_data['attachments']['media_keys']}")
            
            # Get media details
            for media_key in tweet_data['attachments']['media_keys']:
                if media_key in media_dict:
                    media = media_dict[media_key]
                    print(f"   📷 {media.get('type')}: {media.get('url', 'No URL')}")
                    
                    # Update the tweet in database if it exists
                    existing = db.tweets.find_one({"_id": tweet_data['id']})
                    if existing:
                        # Update with media
                        media_list = []
                        for mk in tweet_data['attachments']['media_keys']:
                            if mk in media_dict:
                                m = media_dict[mk]
                                media_list.append({
                                    "media_key": mk,
                                    "type": m.get("type"),
                                    "url": m.get("url"),
                                    "preview_image_url": m.get("preview_image_url"),
                                    "alt_text": m.get("alt_text"),
                                    "width": m.get("width"),
                                    "height": m.get("height"),
                                    "duration_ms": m.get("duration_ms")
                                })
                        
                        db.tweets.update_one(
                            {"_id": tweet_data['id']},
                            {"$set": {
                                "media": media_list,
                                "media_count": len(media_list)
                            }}
                        )
                        print(f"   ✅ Updated tweet in database with {len(media_list)} media items")
    
    print(f"\n📊 Summary:")
    print(f"   Total tweets checked: {len(tweets_response.data)}")
    print(f"   Tweets with media: {tweets_with_media}")
    print(f"   Media items found: {len(media_dict)}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()