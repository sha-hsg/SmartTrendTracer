#!/usr/bin/env python3
"""
Test JSON cookie import functionality
"""
import requests
import json

# Your JSON cookies from Copy Cookie extension
cookie_json = """[{"domain":".magazine.sebastianraschka.com","expirationDate":1762537073.380713,"hostOnly":false,"httpOnly":false,"name":"cookie_storage_key","path":"/","sameSite":"no_restriction","secure":true,"session":false,"storeId":"0","value":"8b64c9e4-30c2-40df-bcf5-c1f061793691"},{"domain":"magazine.sebastianraschka.com","expirationDate":1763052117.943301,"hostOnly":true,"httpOnly":true,"name":"connect.sid","path":"/","sameSite":"unspecified","secure":false,"session":false,"storeId":"0","value":"s%3A-lfX3qmFqQQi1g-_4H7uZL-TeU6n7Pq2.zPWnyQdrNeR1s2b8G2TyZbXGcdTZlFenvqVahXeV4Bw"},{"domain":".magazine.sebastianraschka.com","expirationDate":1786810603,"hostOnly":false,"httpOnly":false,"name":"__stripe_mid","path":"/","sameSite":"strict","secure":true,"session":false,"storeId":"0","value":"7daab6a0-beb4-4237-8995-a9abe90921a9705b06"}]"""

# Test URL
test_url = "https://magazine.sebastianraschka.com/p/understanding-and-coding-self-attention"

print("Testing JSON Cookie Import")
print("=" * 60)

# Parse the JSON cookies
try:
    cookies_list = json.loads(cookie_json)
    print(f"✅ Parsed {len(cookies_list)} cookies from JSON")
    
    # Extract just the cookie names
    cookie_names = [c['name'] for c in cookies_list if 'name' in c]
    print(f"Cookie names: {cookie_names[:5]}")
except Exception as e:
    print(f"❌ Failed to parse JSON: {e}")
    exit(1)

# Test the API endpoint
print("\nTesting API Endpoint...")
print("-" * 40)

api_url = "http://localhost:8000/api/v2/articles/enhanced/import-with-cookies"
payload = {
    "url": test_url,
    "cookie_json": cookie_json
}

try:
    response = requests.post(api_url, json=payload, timeout=60)
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Result: {json.dumps(result, indent=2)}")
        
        if result.get('success'):
            print(f"\n✅ Success! Imported article:")
            print(f"   Title: {result.get('title')}")
            print(f"   Author: {result.get('author')}")
            print(f"   Word count: {result.get('word_count')}")
            print(f"   Article ID: {result.get('article_id')}")
        else:
            print(f"\n❌ Import failed: {result.get('error')}")
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        print(f"Response: {response.text}")
        
except requests.Timeout:
    print("❌ Request timed out")
except Exception as e:
    print(f"❌ Error: {e}")