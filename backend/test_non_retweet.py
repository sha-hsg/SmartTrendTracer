#!/usr/bin/env python3
"""
Test tag suggestion for a non-retweet
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.llm_service import LLMService
from app.models import get_db, Tweet

load_dotenv()

def test_non_retweet():
    """Test tag suggestion for non-retweets"""
    
    db = next(get_db())
    
    # Get a non-retweet tweet
    tweets = db.query(Tweet).filter(
        ~Tweet.text.like('RT @%')
    ).limit(3).all()
    
    if not tweets:
        print("No non-retweet tweets found!")
        return
    
    print("=" * 60)
    print("Testing Tag Suggestion for Non-Retweets")
    print("=" * 60)
    
    # Initialize LLM service
    llm_service = LLMService()
    
    for tweet in tweets:
        print(f"\nTweet ID: {tweet.id}")
        print(f"Author: @{tweet.author_username}")
        print(f"Text: {tweet.text[:100]}...")
        
        # Clear cache
        llm_service._cache = {}
        llm_service._cache_timestamps = {}
        
        try:
            tags = llm_service.suggest_tags(tweet.text, tweet.author_username)
            
            # Check for API marker
            if "__api_success__" in tags:
                api_used = True
                tags = [tag for tag in tags if tag != "__api_success__"]
            else:
                api_used = False
            
            print(f"API used: {api_used}")
            print(f"Tags: {tags}")
            print("-" * 40)
            
        except Exception as e:
            print(f"Error: {e}")
    
    db.close()

if __name__ == "__main__":
    test_non_retweet()