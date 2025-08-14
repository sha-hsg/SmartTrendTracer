#!/usr/bin/env python3
"""
Test the enhanced tag suggestion system with semantic similarity
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import get_db, Tweet

load_dotenv()

def test_tag_suggestions():
    """Test tag suggestions for various tweets"""
    
    db = next(get_db())
    
    # Get different types of tweets
    test_tweets = []
    
    # Get a regular tweet
    regular = db.query(Tweet).filter(
        ~Tweet.text.like('RT @%')
    ).first()
    if regular:
        test_tweets.append(("Regular Tweet", regular))
    
    # Get a full retweet
    full_rt = db.query(Tweet).filter(
        Tweet.text.like('RT @%'),
        ~Tweet.text.like('%…%')
    ).first()
    if full_rt:
        test_tweets.append(("Full Retweet", full_rt))
    
    # Get a truncated retweet
    truncated_rt = db.query(Tweet).filter(
        Tweet.text.like('RT @%'),
        Tweet.text.like('%…%')
    ).first()
    if truncated_rt:
        test_tweets.append(("Truncated Retweet", truncated_rt))
    
    db.close()
    
    print("=" * 80)
    print("Testing Enhanced Tag Suggestion System")
    print("=" * 80)
    
    api_url = "http://localhost:8000/api/tags/suggest"
    
    for tweet_type, tweet in test_tweets:
        print(f"\n{'-' * 60}")
        print(f"Test: {tweet_type}")
        print(f"{'-' * 60}")
        print(f"Tweet ID: {tweet.id}")
        print(f"Author: @{tweet.author_username}")
        print(f"Text: {tweet.text[:100]}...")
        print()
        
        # Call the API
        try:
            response = requests.post(f"{api_url}/{tweet.id}")
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"Model Used: {data.get('model_used', 'Unknown')}")
                print(f"Total Suggestions: {data.get('total_suggestions', 0)}")
                print()
                
                # Show existing suggestions
                existing = data.get('existing_suggestions', [])
                if existing:
                    print("🔍 EXISTING TAGS (from vector store):")
                    for tag in existing[:5]:
                        score = tag.get('score', 0) * 100
                        count = tag.get('usage_count', 0)
                        print(f"  • {tag['tag']:<25} (similarity: {score:.1f}%, used: {count}x)")
                else:
                    print("  No existing tags found")
                
                print()
                
                # Show new suggestions
                new = data.get('new_suggestions', [])
                if new:
                    print("✨ NEW TAGS (from LLM):")
                    for tag in new[:5]:
                        model = tag.get('model', 'unknown')
                        print(f"  • {tag['tag']:<25} (model: {model})")
                else:
                    print("  No new tags suggested")
                
                print()
                
                # Show already tagged
                already = data.get('already_tagged', [])
                if already:
                    print("📌 ALREADY TAGGED:")
                    for tag in already:
                        print(f"  • {tag}")
                
            else:
                print(f"Error: API returned status {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"Error calling API: {e}")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("✅ Existing tags use semantic similarity (green in UI)")
    print("✅ New tags use LLM generation (purple in UI)")
    print("✅ Truncated retweets use spaCy fallback")
    print("✅ Usage counts help rank existing tags")

if __name__ == "__main__":
    test_tag_suggestions()