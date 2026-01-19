#!/usr/bin/env python3
"""
Fix truncated tweets in the database by re-fetching them from Twitter API
"""

import os
import tweepy
from pymongo import MongoClient
from datetime import datetime
import time

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')
db = client.smarttrendtracer

def get_twitter_client():
    """Get Twitter API v2 client"""
    # You'll need to set these environment variables
    bearer_token = os.environ.get('TWITTER_BEARER_TOKEN')
    
    if not bearer_token:
        print("Error: TWITTER_BEARER_TOKEN environment variable not set")
        print("You can find this in your Twitter Developer Portal")
        return None
    
    return tweepy.Client(bearer_token=bearer_token)

def find_truncated_tweets():
    """Find tweets that appear to be truncated"""
    # Find tweets ending with "..." (likely truncated)
    truncated_tweets = list(db.tweets.find({
        'text': {'$regex': r'\.\.\.$'}
    }, {'_id': 1, 'text': 1, 'author_username': 1}).limit(100))
    
    print(f"Found {len(truncated_tweets)} potentially truncated tweets (limited to first 100)")
    return truncated_tweets

def main():
    print("=" * 60)
    print("Truncated Tweets Analysis")
    print("=" * 60)
    
    # Find truncated tweets
    truncated_tweets = find_truncated_tweets()
    
    if not truncated_tweets:
        print("No truncated tweets found")
        return
    
    # Show examples
    print("\nExamples of truncated tweets:")
    print("-" * 60)
    for tweet in truncated_tweets[:5]:
        print(f"ID: {tweet['_id']}")
        print(f"Author: @{tweet['author_username']}")
        print(f"Text: {tweet['text']}")
        print(f"Length: {len(tweet['text'])} characters")
        print("-" * 60)
    
    print(f"\nTotal truncated tweets in database: {db.tweets.count_documents({'text': {'$regex': r'\.\.\.$'}})}")
    
    print("\n" + "=" * 60)
    print("NOTE: These tweets are truncated because:")
    print("1. They are retweets (RT) that Twitter API v2 truncates")
    print("2. They are replies that were cut off")
    print("3. They reference other tweets")
    print("\nTo fix this, you would need to:")
    print("1. Set up TWITTER_BEARER_TOKEN environment variable")
    print("2. Re-fetch these tweets with full expansions")
    print("3. Update the collector to better handle retweets")
    print("=" * 60)

if __name__ == "__main__":
    main()
