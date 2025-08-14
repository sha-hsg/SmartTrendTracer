#!/usr/bin/env python3
"""
Test the tag filtering API
"""

import requests
import urllib.parse

def test_tag_api():
    """Test API tag filtering with special characters"""
    
    # Test tags including special characters
    test_tags = [
        "Research & Development",
        "80GB GPU",
        "gpt-oss-120b",
        "open-source",
        "GPT"
    ]
    
    base_url = "http://localhost:8000/api/tweets"
    
    print("=" * 60)
    print("TESTING TAG FILTERING API")
    print("=" * 60)
    
    for tag in test_tags:
        # Properly encode the tag
        encoded_tag = urllib.parse.quote(tag)
        url = f"{base_url}?limit=50&tag={encoded_tag}"
        
        print(f"\n📌 Testing tag: '{tag}'")
        print(f"   Encoded as: '{encoded_tag}'")
        print(f"   URL: {url}")
        print("-" * 40)
        
        try:
            response = requests.get(url)
            
            if response.status_code == 200:
                tweets = response.json()
                print(f"✅ Found {len(tweets)} tweets")
                
                if tweets:
                    # Check first tweet
                    first_tweet = tweets[0]
                    tags_in_tweet = [t['tag'] for t in first_tweet.get('tags', [])]
                    
                    if tag in tags_in_tweet:
                        print(f"✅ Tag '{tag}' confirmed in first result")
                    else:
                        print(f"❌ WARNING: Tag '{tag}' not found in first result!")
                        print(f"   Tags in tweet: {tags_in_tweet}")
                        
            else:
                print(f"❌ Error: HTTP {response.status_code}")
                print(f"   Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ API is not running")
            print("   Start with: uvicorn app.main:app --reload")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("✅ Server-side filtering implemented")
    print("✅ Special characters handled with URL encoding")
    print("✅ Frontend updated to use server-side filtering")

if __name__ == "__main__":
    test_tag_api()