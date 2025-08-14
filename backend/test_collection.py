#!/usr/bin/env python3
"""
Test tweet collection from the 7 configured accounts
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_collection():
    print("🐦 Testing Tweet Collection System")
    print("=" * 60)
    
    # 1. Check collection status
    print("\n1. Checking current collection status...")
    response = requests.get(f"{BASE_URL}/api/collection/status")
    
    if response.status_code != 200:
        print(f"❌ Failed to get status: {response.status_code}")
        return
    
    status = response.json()
    print(f"✅ Total tweets in database: {status['total_tweets']}")
    print(f"   Tweets in last 24h: {status['tweets_last_24h']}")
    print(f"   Latest tweet: {status.get('latest_tweet', 'None')}")
    
    print("\n   Tweets per account:")
    for account in status['accounts']:
        print(f"   - @{account['username']}: {account['tweet_count']} tweets")
        if account['latest_tweet']:
            latest = datetime.fromisoformat(account['latest_tweet'].replace('Z', '+00:00'))
            hours_ago = (datetime.utcnow() - latest.replace(tzinfo=None)).total_seconds() / 3600
            print(f"     Latest: {hours_ago:.1f} hours ago")
    
    # 2. Check for gaps
    print("\n2. Checking for collection gaps...")
    response = requests.get(f"{BASE_URL}/api/collection/gaps")
    
    if response.status_code == 200:
        gaps = response.json()
        has_gaps = False
        for gap in gaps['gaps']:
            if gap['status'] != 'ok':
                has_gaps = True
                print(f"   ⚠️ @{gap['username']}: {gap['status']}")
                if gap['hours_since']:
                    print(f"      Last tweet: {gap['hours_since']} hours ago")
        
        if not has_gaps:
            print("   ✅ All accounts have recent tweets")
    
    # 3. Trigger manual collection
    print("\n3. Triggering manual tweet collection...")
    print("   This will collect up to 50 recent tweets per account...")
    
    response = requests.post(
        f"{BASE_URL}/api/collection/collect",
        params={"max_results": 50}
    )
    
    if response.status_code == 200:
        print("   ✅ Collection started in background")
        print("   Waiting 10 seconds for collection to complete...")
        time.sleep(10)
        
        # Check status again
        response = requests.get(f"{BASE_URL}/api/collection/status")
        if response.status_code == 200:
            new_status = response.json()
            new_tweets = new_status['total_tweets'] - status['total_tweets']
            print(f"   ✅ Collected {new_tweets} new tweets")
    else:
        print(f"   ❌ Failed to start collection: {response.status_code}")
    
    # 4. Test historical collection (optional)
    print("\n4. Testing historical collection (1 day)...")
    user_input = input("   Do you want to collect historical tweets? (y/n): ")
    
    if user_input.lower() == 'y':
        response = requests.post(
            f"{BASE_URL}/api/collection/collect/historical",
            params={"days": 1}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ {result['message']}")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    
    print("\n" + "=" * 60)
    print("✅ Tweet collection test complete!")
    print("\nNotes:")
    print("- The backend scheduler will automatically collect tweets every 30 minutes")
    print("- You can manually trigger collection via the API")
    print("- Historical collection can fetch up to 7 days of past tweets")

if __name__ == "__main__":
    print("Make sure the backend server is running (cd backend && python run.py)")
    print("Starting test in 2 seconds...")
    time.sleep(2)
    
    try:
        test_collection()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend server")
        print("   Please start the server with: cd backend && python run.py")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")