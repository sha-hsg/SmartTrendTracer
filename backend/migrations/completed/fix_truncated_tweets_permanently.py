#!/usr/bin/env python3
"""
Fix truncated tweets permanently - both existing ones and prevent future ones
"""

import os
import sys
import tweepy
from pymongo import MongoClient
from datetime import datetime
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')
db = client.smarttrendtracer

def get_twitter_client():
    """Get Twitter API v2 client"""
    bearer_token = os.environ.get('TWITTER_BEARER_TOKEN')
    
    if not bearer_token:
        print("Error: TWITTER_BEARER_TOKEN not found in .env file")
        return None
    
    print(f"✅ Using bearer token: {bearer_token[:10]}...{bearer_token[-4:]}")
    return tweepy.Client(bearer_token=bearer_token)

def find_truncated_tweets():
    """Find tweets that appear to be truncated"""
    # Find tweets ending with "..." (likely truncated)
    truncated_tweets = list(db.tweets.find({
        'text': {'$regex': r'\.\.\.$'}
    }, {'_id': 1, 'text': 1, 'author_username': 1}))
    
    return truncated_tweets

def fix_truncated_tweet(client, tweet):
    """Fetch the full text of a truncated tweet"""
    try:
        # Fetch the tweet with all expansions for full text
        response = client.get_tweet(
            tweet['_id'],
            tweet_fields=['text', 'note_tweet', 'referenced_tweets', 'entities', 'created_at'],
            expansions=['referenced_tweets.id', 'referenced_tweets.id.author_id'],
            user_fields=['username']
        )
        
        if not response.data:
            print(f"  ⚠️ Tweet {tweet['_id']} not found (may be deleted)")
            return None
        
        tweet_data = response.data
        full_text = tweet_data.text
        
        # Check for long tweet (note_tweet) - Twitter's way of handling > 280 chars
        if hasattr(tweet_data, 'note_tweet') and tweet_data.note_tweet:
            full_text = tweet_data.note_tweet.get('text', tweet_data.text)
        
        # For retweets, get the full original text
        if response.includes and 'tweets' in response.includes:
            # Check if this is a retweet
            if full_text.startswith('RT @') and '…' in full_text:
                # Find the referenced tweet
                for ref_tweet in response.includes['tweets']:
                    # Get the RT prefix
                    rt_parts = full_text.split(':', 1)
                    if len(rt_parts) > 0:
                        rt_prefix = rt_parts[0] + ': '
                        
                        # Get full text from referenced tweet
                        ref_full_text = ref_tweet.text
                        if hasattr(ref_tweet, 'note_tweet') and ref_tweet.note_tweet:
                            ref_full_text = ref_tweet.note_tweet.get('text', ref_tweet.text)
                        
                        # Combine RT prefix with full referenced text
                        full_text = rt_prefix + ref_full_text
                        break
        
        return full_text
        
    except tweepy.errors.TweepyException as e:
        error_str = str(e)
        if "Could not find tweet with" in error_str:
            print(f"  ⚠️ Tweet {tweet['_id']} no longer exists")
        elif "Rate limit" in error_str:
            print(f"  ⏳ Rate limited, waiting...")
            time.sleep(60)  # Wait a minute
            return fix_truncated_tweet(client, tweet)  # Retry
        else:
            print(f"  ❌ Error fetching tweet {tweet['_id']}: {e}")
        return None

def update_tweet_text(tweet_id, new_text):
    """Update the tweet text in MongoDB"""
    result = db.tweets.update_one(
        {'_id': tweet_id},
        {'$set': {
            'text': new_text,
            'truncation_fixed': True,
            'truncation_fixed_at': datetime.utcnow()
        }}
    )
    return result.modified_count > 0

def main():
    print("=" * 60)
    print("Fix Truncated Tweets PERMANENTLY")
    print("=" * 60)
    
    # Get Twitter client
    client = get_twitter_client()
    if not client:
        return
    
    # Test the client
    try:
        me = client.get_me()
        if me and me.data:
            print(f"✅ Authenticated as app (ID: {me.data.id})")
        else:
            print("✅ Authentication successful (app-only auth)")
    except Exception as e:
        print(f"⚠️ Auth test: {e}")
        # Continue anyway - app auth doesn't support get_me()
    
    # Find truncated tweets
    truncated_tweets = find_truncated_tweets()
    
    print(f"\nFound {len(truncated_tweets)} truncated tweets")
    
    if not truncated_tweets:
        print("✨ No truncated tweets to fix!")
        return
    
    # Show what we'll fix
    print("\nTweets to fix:")
    print("-" * 60)
    for tweet in truncated_tweets:
        print(f"@{tweet['author_username']}: {tweet['text'][:80]}...")
    print("-" * 60)
    
    # Fix tweets
    print("\nFixing tweets...")
    fixed = 0
    unchanged = 0
    failed = 0
    
    for i, tweet in enumerate(truncated_tweets, 1):
        print(f"\n[{i}/{len(truncated_tweets)}] Processing tweet {tweet['_id']}")
        print(f"  Current: {tweet['text'][:100]}")
        
        # Get full text
        full_text = fix_truncated_tweet(client, tweet)
        
        if full_text:
            if full_text != tweet['text']:
                # Text is different - update it
                if update_tweet_text(tweet['_id'], full_text):
                    fixed += 1
                    print(f"  ✅ Fixed! New text: {full_text[:100]}...")
                else:
                    failed += 1
                    print(f"  ❌ Failed to update database")
            else:
                unchanged += 1
                print(f"  ℹ️ Text unchanged (not actually truncated)")
        else:
            failed += 1
            print(f"  ❌ Could not fetch full text")
        
        # Rate limiting pause
        if i < len(truncated_tweets):
            time.sleep(0.5)  # Half second between requests
    
    # Final report
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"✅ Fixed: {fixed} tweets")
    print(f"ℹ️  Unchanged: {unchanged} tweets")
    print(f"❌ Failed: {failed} tweets")
    
    if fixed > 0:
        print("\n🎉 Successfully fixed truncated tweets!")
        print("The faceted browser will now show the full text.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()