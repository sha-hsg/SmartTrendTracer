#!/usr/bin/env python3
"""
Test PDF endpoint availability
"""
import requests

paper_id = 1
base_url = "http://localhost:8000"

print("Testing PDF Endpoint")
print("=" * 60)

# Test 1: Check if paper exists
print(f"\n1. Checking if paper {paper_id} exists...")
try:
    response = requests.get(f"{base_url}/api/papers/{paper_id}")
    if response.status_code == 200:
        paper = response.json()
        print(f"✅ Paper found: {paper.get('title', 'Unknown')[:50]}...")
        print(f"   Processed: {paper.get('processed', False)}")
        print(f"   PDF Path: {paper.get('pdf_path', 'None')}")
    else:
        print(f"❌ Paper not found: {response.status_code}")
        exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# Test 2: Try different methods to access PDF
print(f"\n2. Testing PDF endpoint access methods...")

# Test GET with Range header
print("\n   a) GET with Range header:")
try:
    response = requests.get(
        f"{base_url}/api/papers/{paper_id}/pdf",
        headers={'Range': 'bytes=0-0'}
    )
    print(f"      Status: {response.status_code}")
    if response.status_code in [200, 206]:
        print(f"      ✅ PDF accessible via Range request")
    elif response.status_code == 404:
        print(f"      ❌ PDF not found")
    else:
        print(f"      ⚠️ Unexpected status: {response.status_code}")
except Exception as e:
    print(f"      ❌ Error: {e}")

# Test regular GET
print("\n   b) Regular GET request:")
try:
    response = requests.get(f"{base_url}/api/papers/{paper_id}/pdf", stream=True)
    print(f"      Status: {response.status_code}")
    if response.status_code == 200:
        content_type = response.headers.get('content-type', '')
        content_length = response.headers.get('content-length', 'unknown')
        print(f"      ✅ PDF accessible")
        print(f"      Content-Type: {content_type}")
        print(f"      Size: {content_length} bytes")
    elif response.status_code == 404:
        print(f"      ❌ PDF not found")
        print(f"      Response: {response.text[:200]}")
    else:
        print(f"      ⚠️ Unexpected status: {response.status_code}")
except Exception as e:
    print(f"      ❌ Error: {e}")

# Test HEAD request (which is failing)
print("\n   c) HEAD request (currently failing):")
try:
    response = requests.head(f"{base_url}/api/papers/{paper_id}/pdf")
    print(f"      Status: {response.status_code}")
    if response.status_code == 200:
        print(f"      ✅ HEAD method supported")
    elif response.status_code == 405:
        print(f"      ❌ HEAD method not allowed (expected)")
    else:
        print(f"      ⚠️ Unexpected status: {response.status_code}")
except Exception as e:
    print(f"      ❌ Error: {e}")

print("\n" + "=" * 60)
print("Recommendation: Use GET with Range header to check PDF availability")