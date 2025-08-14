#!/usr/bin/env python3
"""
Test the interactive tagging system
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_interactive_tagging():
    print("🧪 Testing Interactive Tagging System")
    print("=" * 50)
    
    # 1. Get some tweets
    print("\n1. Fetching tweets...")
    response = requests.get(f"{BASE_URL}/api/tweets?limit=5")
    if response.status_code != 200:
        print(f"❌ Failed to fetch tweets: {response.status_code}")
        return
    
    tweets = response.json()
    if not tweets:
        print("❌ No tweets found in database")
        return
    
    print(f"✅ Found {len(tweets)} tweets")
    
    # 2. Test tag suggestion for first tweet
    test_tweet = tweets[0]
    tweet_id = test_tweet['id']
    
    print(f"\n2. Testing tag suggestions for tweet ID: {tweet_id}")
    print(f"   Author: @{test_tweet['author_username']}")
    print(f"   Text: {test_tweet['text'][:100]}...")
    
    # Get tag suggestions
    print("\n3. Getting AI tag suggestions...")
    start_time = time.time()
    
    response = requests.post(f"{BASE_URL}/api/tags/suggest/{tweet_id}")
    elapsed = time.time() - start_time
    
    if response.status_code != 200:
        print(f"❌ Failed to get suggestions: {response.status_code}")
        print(f"   Error: {response.text}")
        return
    
    suggestions = response.json()
    print(f"✅ Got suggestions in {elapsed:.2f} seconds")
    print(f"   Model used: {suggestions.get('model_used', 'Unknown')}")
    print(f"   Confidence: {suggestions.get('confidence', 'N/A')}")
    print(f"   Suggested tags: {suggestions['suggested_tags']}")
    print(f"   Existing tags: {suggestions['existing_tags']}")
    print(f"   New suggestions: {suggestions['new_suggestions']}")
    
    # 4. Apply some tags
    if suggestions['new_suggestions']:
        print("\n4. Applying first two suggested tags...")
        tags_to_apply = suggestions['new_suggestions'][:2]
        
        for tag in tags_to_apply:
            response = requests.post(
                f"{BASE_URL}/api/tags/tweet/{tweet_id}",
                json={"tag": tag, "tag_type": "llm", "confidence": 0.9}
            )
            if response.status_code == 200:
                print(f"   ✅ Applied tag: {tag}")
            else:
                print(f"   ⚠️  Failed to apply tag: {tag}")
    
    # 5. Verify tags were applied
    print("\n5. Verifying tags...")
    response = requests.get(f"{BASE_URL}/api/tags/tweet/{tweet_id}")
    if response.status_code == 200:
        current_tags = response.json()
        print(f"✅ Tweet now has {len(current_tags)} tags:")
        for tag in current_tags:
            print(f"   - {tag['tag']} (type: {tag['tag_type']}, confidence: {tag['confidence']})")
    
    # 6. Test batch suggestions
    print("\n6. Testing batch tag suggestions...")
    tweet_ids = [t['id'] for t in tweets[:3]]
    
    response = requests.post(
        f"{BASE_URL}/api/tags/suggest/batch",
        json=tweet_ids
    )
    
    if response.status_code == 200:
        batch_results = response.json()
        print(f"✅ Got batch suggestions for {batch_results['count']} tweets")
        print(f"   Model used: {batch_results['model_used']}")
        for tweet_id, tags in batch_results['suggestions'].items():
            print(f"   Tweet {tweet_id}: {tags}")
    else:
        print(f"⚠️  Batch suggestions failed: {response.status_code}")
    
    print("\n" + "=" * 50)
    print("✅ Interactive tagging system test complete!")
    print("\nNOTE: The frontend modal should now work when you:")
    print("1. Click on any tweet card")
    print("2. Or click the 'Suggest Tags' button")
    print("3. The modal will show AI suggestions you can accept/reject")

if __name__ == "__main__":
    print("Make sure the backend server is running (python run.py)")
    print("Starting test in 2 seconds...")
    time.sleep(2)
    
    try:
        test_interactive_tagging()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend server")
        print("   Please start the server with: cd backend && python run.py")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")