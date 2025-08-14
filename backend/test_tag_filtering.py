#!/usr/bin/env python3
"""
Test tag filtering issue
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import get_db, Tweet, Tag

load_dotenv()

def test_tag_filtering():
    """Test tag filtering with special characters"""
    
    db = next(get_db())
    
    # Test tags with special characters
    test_tags = [
        "Research & Development",
        "80GB GPU",
        "GPT",  # A simple one for comparison
    ]
    
    print("=" * 60)
    print("TESTING TAG FILTERING")
    print("=" * 60)
    
    for tag_name in test_tags:
        print(f"\n📌 Testing tag: '{tag_name}'")
        print("-" * 40)
        
        # Method 1: Join query (what API should be doing)
        tweets_with_tag = db.query(Tweet).join(Tag).filter(
            Tag.tag == tag_name
        ).all()
        
        print(f"Found {len(tweets_with_tag)} tweets with join query")
        
        # Method 2: Check tags directly
        tags = db.query(Tag).filter(Tag.tag == tag_name).all()
        print(f"Found {len(tags)} tag records in database")
        
        # Show sample tweet
        if tweets_with_tag:
            tweet = tweets_with_tag[0]
            print(f"\nSample tweet:")
            print(f"  ID: {tweet.id}")
            print(f"  Author: @{tweet.author_username}")
            print(f"  Text: {tweet.text[:100]}...")
            
            # Check tags on this tweet
            tweet_tags = db.query(Tag).filter(Tag.tweet_id == tweet.id).all()
            print(f"  Tags on this tweet: {[t.tag for t in tweet_tags]}")
    
    # Now test what the API endpoint returns
    print("\n" + "=" * 60)
    print("CHECKING API BEHAVIOR")
    print("=" * 60)
    
    # Get all tweets with their tags (like the API does)
    all_tweets = db.query(Tweet).all()
    
    for tag_name in test_tags:
        print(f"\n📌 Filtering for: '{tag_name}'")
        
        # Simulate frontend filtering
        filtered = []
        for tweet in all_tweets:
            tweet_tags = [t.tag for t in tweet.tags]
            if tag_name in tweet_tags:
                filtered.append(tweet)
        
        print(f"Frontend filtering would find: {len(filtered)} tweets")
        
        # Check exact string matching
        for tweet in all_tweets[:5]:  # Check first 5 tweets
            for tag in tweet.tags:
                if tag.tag == tag_name:
                    print(f"  ✅ Found exact match: '{tag.tag}' == '{tag_name}'")
                elif tag_name.lower() in tag.tag.lower():
                    print(f"  ⚠️ Partial match: '{tag.tag}' contains '{tag_name}'")
    
    db.close()

if __name__ == "__main__":
    test_tag_filtering()