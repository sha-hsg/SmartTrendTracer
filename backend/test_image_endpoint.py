#!/usr/bin/env python3
"""Test the image serving endpoint to debug issues"""

import requests

# Test different variations of the image URL
test_urls = [
    # Using converted integer ID with full hierarchical path
    "http://localhost:8000/api/papers/4245617126/images/42/45/617126/figure_0_8dede0da.jpg",
    # Using MongoDB ID with full hierarchical path  
    "http://localhost:8000/api/papers/68ab70fe3e0caac2fd0ef9e6/images/42/45/617126/figure_0_8dede0da.jpg",
    # Using converted integer ID with just filename
    "http://localhost:8000/api/papers/4245617126/images/figure_0_8dede0da.jpg",
    # Using MongoDB ID with just filename
    "http://localhost:8000/api/papers/68ab70fe3e0caac2fd0ef9e6/images/figure_0_8dede0da.jpg",
]

print("Testing image endpoint URLs...")
print("=" * 60)

for url in test_urls:
    print(f"\nTesting: {url}")
    try:
        response = requests.get(url, timeout=5)
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print(f"  ✅ Success! Image size: {len(response.content)} bytes")
        else:
            print(f"  ❌ Error: {response.text[:200] if response.text else 'No error message'}")
    except Exception as e:
        print(f"  ❌ Exception: {e}")

print("\n" + "=" * 60)
print("Check the API logs for detailed error messages")