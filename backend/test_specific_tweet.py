#!/usr/bin/env python3
"""
Test tag suggestion for a specific tweet
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.llm_service import LLMService
from app.models import get_db, Tweet

load_dotenv()

def test_specific_tweet():
    """Test tag suggestion for the specific tweet"""
    
    db = next(get_db())
    
    # Get the specific tweet
    tweet = db.query(Tweet).filter(Tweet.id == "1953725835032068446").first()
    
    if not tweet:
        print("Tweet not found!")
        return
    
    print("=" * 60)
    print("Testing Tag Suggestion for Specific Tweet")
    print("=" * 60)
    print(f"Tweet ID: {tweet.id}")
    print(f"Author: @{tweet.author_username}")
    print(f"Text: {tweet.text}")
    print(f"Text length: {len(tweet.text)}")
    print()
    
    # Initialize LLM service
    llm_service = LLMService()
    
    # Clear cache for this tweet
    llm_service._cache = {}
    llm_service._cache_timestamps = {}
    
    print("Calling tag suggestion (cache cleared)...")
    
    try:
        tags = llm_service.suggest_tags(tweet.text, tweet.author_username)
        
        # Remove the marker if present
        if "__api_success__" in tags:
            api_used = True
            tags = [tag for tag in tags if tag != "__api_success__"]
        else:
            api_used = False
        
        print(f"\nAPI was used: {api_used}")
        print(f"Generated {len(tags)} tags:")
        for i, tag in enumerate(tags, 1):
            print(f"  {i}. {tag}")
            
    except Exception as e:
        print(f"Error: {e}")
    
    db.close()

if __name__ == "__main__":
    test_specific_tweet()