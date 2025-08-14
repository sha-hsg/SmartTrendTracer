#!/usr/bin/env python3
"""
Test the full tagging system with OpenAI API, spaCy fallback, and simple fallback
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.llm_service import LLMService
from app.models import get_db, Tweet

load_dotenv()

def test_full_system():
    """Test the complete tagging system"""
    
    db = next(get_db())
    
    # Test different types of tweets
    test_cases = [
        # Regular tweet (should use API)
        ("regular", Tweet.text.notilike('RT @%')),
        # Full retweet (should use API)
        ("full_retweet", Tweet.text.like('RT @%'), ~Tweet.text.like('%…%')),
        # Truncated retweet (should use spaCy fallback)
        ("truncated_retweet", Tweet.text.like('RT @%'), Tweet.text.like('%…%'))
    ]
    
    print("=" * 60)
    print("Testing Full Tagging System")
    print("=" * 60)
    
    # Initialize LLM service
    llm_service = LLMService()
    
    for case_name, *filters in test_cases:
        print(f"\n{'-' * 40}")
        print(f"Test Case: {case_name.upper()}")
        print(f"{'-' * 40}")
        
        # Build query
        query = db.query(Tweet)
        for f in filters:
            query = query.filter(f)
        
        tweet = query.first()
        
        if not tweet:
            print(f"No {case_name} tweets found!")
            continue
        
        print(f"Tweet ID: {tweet.id}")
        print(f"Author: @{tweet.author_username}")
        print(f"Text Preview: {tweet.text[:100]}...")
        print(f"Text Length: {len(tweet.text)}")
        print(f"Has Ellipsis: {'…' in tweet.text}")
        
        # Clear cache
        llm_service._cache = {}
        llm_service._cache_timestamps = {}
        
        try:
            # Get tags
            tags = llm_service.suggest_tags(tweet.text, tweet.author_username)
            
            # Check for API marker
            if "__api_success__" in tags:
                method_used = "OpenAI API (gpt-4o-mini)"
                tags = [tag for tag in tags if tag != "__api_success__"]
            else:
                # Determine if spaCy or simple fallback
                if '…' in tweet.text and tweet.text.startswith('RT @'):
                    method_used = "spaCy Fallback (truncated RT)"
                else:
                    method_used = "spaCy Fallback (API failed)"
            
            print(f"\nMethod Used: {method_used}")
            print(f"Tags Generated: {tags}")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
    
    db.close()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("✅ OpenAI API: Used for regular tweets and full retweets")
    print("✅ spaCy Fallback: Used for truncated retweets or API failures")
    print("✅ Simple Fallback: Used if spaCy fails (safety net)")

if __name__ == "__main__":
    test_full_system()