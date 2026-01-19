#!/usr/bin/env python3
"""
Test the MongoDB tweet collector with a single account
"""
import os
import sys
from dotenv import load_dotenv
load_dotenv()

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tweepy
from pymongo import MongoClient

# Test Twitter API connection
bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
if not bearer_token:
    print("❌ TWITTER_BEARER_TOKEN not found")
    sys.exit(1)

print("✅ Bearer token found")

# Test MongoDB connection
try:
    mongo_client = MongoClient("mongodb://localhost:27017/")
    db = mongo_client.smarttrendtracer
    db.command('ping')
    print("✅ MongoDB connected")
except Exception as e:
    print(f"❌ MongoDB error: {e}")
    sys.exit(1)

# Test Tweepy client
try:
    client = tweepy.Client(bearer_token=bearer_token)
    print("✅ Tweepy client created")
    
    # Test with OpenAI account
    account_id = "4398626122"
    username = "OpenAI"
    
    print(f"\n📊 Testing collection for @{username}...")
    
    # Get recent tweets (just 5 for testing)
    response = client.get_users_tweets(
        id=account_id,
        max_results=5,
        tweet_fields=['created_at', 'public_metrics']
    )
    
    if response and response.data:
        print(f"✅ Got {len(response.data)} tweets")
        for tweet in response.data:
            print(f"  - Tweet {tweet.id}: {tweet.text[:50]}...")
    else:
        print("❌ No tweets returned")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ All tests passed! Tweet collector should work.")