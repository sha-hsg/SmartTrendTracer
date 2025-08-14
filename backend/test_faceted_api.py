#!/usr/bin/env python3
"""Test the faceted tweets API endpoint"""

import requests
import json

def test_faceted_search():
    """Test the faceted search endpoint"""
    url = "http://localhost:8000/api/v2/tweets/tweets/faceted-search"
    params = {
        "page": 1,
        "page_size": 5,
        "exclude_retweets": False
    }
    
    try:
        response = requests.get(url, params=params)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {data['total']} tweets")
            print(f"Authors: {len(data['facets']['authors'])}")
            print(f"Tags: {len(data['facets']['tags'])}")
            
            if data['tweets']:
                print("\nFirst tweet:")
                tweet = data['tweets'][0]
                print(f"  Author: {tweet['author_username']}")
                print(f"  Text: {tweet['text'][:100]}...")
                print(f"  Is Retweet: {tweet.get('is_retweet', 'N/A')}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text[:500])
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_faceted_search()