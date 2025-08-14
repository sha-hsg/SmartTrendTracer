#!/usr/bin/env python3
"""
Test what the API returns for tweets
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import get_db, Tweet, Tag

load_dotenv()

def test_api_response():
    """Test API response for tweets with special character tags"""
    
    # First check database directly
    db = next(get_db())
    
    # Get a tweet with "Research & Development" tag
    tweet_with_rd = db.query(Tweet).join(Tag).filter(
        Tag.tag == "Research & Development"
    ).first()
    
    if tweet_with_rd:
        print("=" * 60)
        print("DATABASE CHECK")
        print("=" * 60)
        print(f"Tweet ID: {tweet_with_rd.id}")
        print(f"Author: @{tweet_with_rd.author_username}")
        
        # Get all tags for this tweet
        tags = db.query(Tag).filter(Tag.tweet_id == tweet_with_rd.id).all()
        print(f"Tags in DB: {[t.tag for t in tags]}")
    
    db.close()
    
    # Now test API (assuming it's running on port 8000)
    print("\n" + "=" * 60)
    print("API RESPONSE CHECK")
    print("=" * 60)
    
    try:
        # Get tweets from API
        response = requests.get("http://localhost:8000/api/tweets?limit=200")
        
        if response.status_code == 200:
            tweets = response.json()
            print(f"API returned {len(tweets)} tweets")
            
            # Look for tweets with our test tags
            test_tags = ["Research & Development", "80GB GPU", "gpt-oss-120b"]
            
            for tag_name in test_tags:
                print(f"\n📌 Looking for tag: '{tag_name}'")
                found_count = 0
                
                for tweet in tweets:
                    tweet_tags = [t['tag'] for t in tweet.get('tags', [])]
                    if tag_name in tweet_tags:
                        found_count += 1
                        if found_count == 1:  # Show first match
                            print(f"  Found in tweet {tweet['id']}")
                            print(f"  Tweet tags from API: {tweet_tags}")
                
                print(f"  Total tweets with this tag: {found_count}")
        else:
            print(f"API error: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("API is not running. Start it with: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api_response()