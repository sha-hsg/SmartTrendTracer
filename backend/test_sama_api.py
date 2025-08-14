#!/usr/bin/env python3
"""Test Twitter API for sama's account specifically"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.collectors.twitter_collector import TwitterCollector
from app.models import SessionLocal

def test_sama_collection():
    collector = TwitterCollector()
    db = SessionLocal()
    
    # sama's account info
    sama_account = {
        'id': '1605',  # sama's Twitter user ID
        'username': 'sama'
    }
    
    print("Testing Twitter API for @sama...")
    print("="*50)
    
    # Test 1: Get latest tweets without since_id (should get his most recent)
    print("\n1. Getting latest tweets (no since_id filter):")
    try:
        tweets = collector.client.get_users_tweets(
            id=sama_account['id'],
            max_results=10,
            tweet_fields=['created_at', 'public_metrics'],
        )
        
        if tweets.data:
            print(f"   Found {len(tweets.data)} tweets from API")
            for i, tweet in enumerate(tweets.data[:5]):
                print(f"   {i+1}. {tweet.created_at}: {tweet.text[:60]}...")
        else:
            print("   No tweets returned by API")
            
    except Exception as e:
        print(f"   API Error: {e}")
    
    # Test 2: Get tweets since our latest stored tweet
    print(f"\n2. Getting tweets since ID 1953649128707366957:")
    try:
        tweets = collector.client.get_users_tweets(
            id=sama_account['id'],
            max_results=10,
            since_id="1953649128707366957",  # Latest tweet in our DB
            tweet_fields=['created_at', 'public_metrics'],
        )
        
        if tweets.data:
            print(f"   Found {len(tweets.data)} NEW tweets since our latest")
            for i, tweet in enumerate(tweets.data[:5]):
                print(f"   {i+1}. {tweet.created_at}: {tweet.text[:60]}...")
        else:
            print("   No new tweets since our latest (this explains the issue!)")
            
    except Exception as e:
        print(f"   API Error: {e}")
    
    # Test 3: Check what our database thinks is the latest
    from app.models import Tweet
    latest_tweet = db.query(Tweet).filter(
        Tweet.author_username == 'sama'
    ).order_by(Tweet.created_at.desc()).first()
    
    print(f"\n3. Our database info:")
    print(f"   Latest tweet ID: {latest_tweet.id}")
    print(f"   Latest tweet date: {latest_tweet.created_at}")
    print(f"   Latest tweet text: {latest_tweet.text[:60]}...")
    
    db.close()

if __name__ == "__main__":
    test_sama_collection()