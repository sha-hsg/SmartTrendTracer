#!/usr/bin/env python3
"""
Test script for LLM tag suggestions
Run this to test automatic tag generation for tweets
"""
import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API base URL
API_BASE = "http://localhost:8000"

def test_single_tweet_suggestion():
    """Test suggesting tags for a single tweet"""
    print("\n=== Testing Single Tweet Tag Suggestion ===")
    
    # First, get a tweet
    response = requests.get(f"{API_BASE}/api/tweets?limit=1")
    if response.status_code != 200:
        print(f"Error fetching tweets: {response.status_code}")
        return
    
    tweets = response.json()
    if not tweets:
        print("No tweets found")
        return
    
    tweet = tweets[0]
    tweet_id = tweet['id']
    
    print(f"Tweet from @{tweet['author_username']}:")
    print(f"  {tweet['text'][:100]}...")
    print(f"\nExisting tags: {[t['tag'] for t in tweet.get('tags', [])]}")
    
    # Get tag suggestions
    print("\nRequesting AI tag suggestions...")
    response = requests.post(f"{API_BASE}/api/tags/suggest/{tweet_id}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ Suggested tags: {result['suggested_tags']}")
        print(f"   New suggestions: {result['new_suggestions']}")
        print(f"   Model used: {result['model_used']}")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")

def test_auto_tagging():
    """Test automatic tagging of tweets"""
    print("\n=== Testing Auto-Tagging ===")
    
    # Get an untagged tweet
    response = requests.get(f"{API_BASE}/api/tweets?limit=10")
    tweets = response.json()
    
    # Find a tweet with no tags
    untagged_tweet = None
    for tweet in tweets:
        if not tweet.get('tags'):
            untagged_tweet = tweet
            break
    
    if not untagged_tweet:
        print("No untagged tweets found")
        return
    
    tweet_id = untagged_tweet['id']
    print(f"Tweet from @{untagged_tweet['author_username']}:")
    print(f"  {untagged_tweet['text'][:100]}...")
    
    # Auto-tag the tweet
    print("\nAuto-tagging with AI...")
    response = requests.post(
        f"{API_BASE}/api/tags/auto-tag/{tweet_id}",
        params={"apply_threshold": 3}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ Auto-tagging successful!")
        print(f"   Suggested: {result['suggested_tags']}")
        print(f"   Applied: {result['applied_tags']}")
        print(f"   Already existed: {result['already_existed']}")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")

def test_batch_suggestions():
    """Test batch tag suggestions"""
    print("\n=== Testing Batch Tag Suggestions ===")
    
    # Get multiple tweets
    response = requests.get(f"{API_BASE}/api/tweets?limit=3")
    tweets = response.json()
    
    if len(tweets) < 2:
        print("Not enough tweets for batch test")
        return
    
    tweet_ids = [t['id'] for t in tweets[:3]]
    
    print(f"Getting suggestions for {len(tweet_ids)} tweets...")
    
    # Get batch suggestions
    response = requests.post(
        f"{API_BASE}/api/tags/suggest/batch",
        json=tweet_ids
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ Batch suggestions received!")
        for tweet_id, tags in result['suggestions'].items():
            # Find the tweet
            tweet = next((t for t in tweets if t['id'] == tweet_id), None)
            if tweet:
                print(f"\n@{tweet['author_username']}: {tweet['text'][:50]}...")
                print(f"  → Tags: {tags}")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")

def main():
    """Run all tests"""
    print("=" * 50)
    print("LLM TAG SUGGESTION TESTS")
    print("=" * 50)
    
    # Check if OPENAI_API_KEY is set
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  Warning: OPENAI_API_KEY not found in environment")
        print("   The LLM service will use fallback tag extraction")
    
    # Run tests
    test_single_tweet_suggestion()
    test_auto_tagging()
    test_batch_suggestions()
    
    print("\n" + "=" * 50)
    print("Tests complete!")

if __name__ == "__main__":
    main()