#!/usr/bin/env python3
"""Test the API tag filtering directly"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from urllib.parse import quote

client = TestClient(app)

# Test problematic tags
test_tags = [
    '3D interface generation',
    '16GB devices',
    'Communication Strategy',
    'AI Ethics & Future',
]

print("Testing API tag filtering...")
print("="*50)

for tag in test_tags:
    # Test with URL encoding (as browser would send)
    encoded_tag = quote(tag)
    
    print(f"\nTag: '{tag}'")
    print(f"Encoded: '{encoded_tag}'")
    
    # Make API request
    response = client.get(f"/api/tweets?tag={encoded_tag}&limit=5")
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Results: {len(data)} tweets")
        
        if data:
            for tweet in data[:2]:
                print(f"  - @{tweet['author_username']}: {tweet['text'][:50]}...")
        else:
            print("  ⚠️  No tweets returned (but status 200)")
    else:
        print(f"  ❌ Error: {response.text}")

# Also test without encoding
print("\n" + "="*50)
print("Testing without URL encoding (raw tag):")

tag = 'AI Ethics & Future'
response = client.get("/api/tweets", params={"tag": tag, "limit": 5})
print(f"\nTag: '{tag}'")
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Results: {len(data)} tweets")