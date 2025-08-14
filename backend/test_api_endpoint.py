#!/usr/bin/env python3
"""
Test the tag suggestion API endpoint directly
"""

import requests
import json

def test_api():
    """Test the API endpoint"""
    
    # Get a tweet ID from the database
    tweets_response = requests.get("http://localhost:8000/api/tweets/?limit=1")
    
    if tweets_response.status_code != 200:
        print(f"❌ Could not fetch tweets: {tweets_response.status_code}")
        return
    
    tweets = tweets_response.json()
    if not tweets:
        print("❌ No tweets found in database")
        return
    
    tweet_id = tweets[0]['id']
    tweet_text = tweets[0]['text'][:100]
    
    print("=" * 60)
    print("Testing Tag Suggestion API Endpoint")
    print("=" * 60)
    print(f"Tweet ID: {tweet_id}")
    print(f"Tweet: {tweet_text}...")
    print("\nCalling /api/tags/suggest/{tweet_id}...")
    
    # Call the tag suggestion endpoint
    response = requests.post(f"http://localhost:8000/api/tags/suggest/{tweet_id}")
    
    print(f"\nResponse Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\nResponse Data:")
        print(json.dumps(data, indent=2))
        
        print("\nKey Fields:")
        print(f"  model_used: {data.get('model_used', 'NOT FOUND')}")
        print(f"  confidence: {data.get('confidence', 'NOT FOUND')}")
        print(f"  suggested_tags: {data.get('suggested_tags', [])}")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_api()