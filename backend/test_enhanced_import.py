#!/usr/bin/env python3
"""
Test the enhanced article import API endpoints
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v2/articles/enhanced"

def test_check_paywall():
    """Test the paywall check endpoint"""
    print("=" * 60)
    print("Testing Paywall Check")
    print("=" * 60)
    
    url = "https://magazine.sebastianraschka.com/p/llm-research-papers-2025-list-one"
    
    response = requests.post(
        f"{BASE_URL}/check-paywall",
        params={"url": url}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"📄 URL: {data.get('url')}")
        print(f"🔒 Has Paywall: {data.get('has_paywall')}")
        print(f"💳 Needs Subscription: {data.get('needs_subscription')}")
        print(f"📏 Preview Length: {data.get('content_preview_length')} chars")
        print(f"✂️ Is Truncated: {data.get('is_truncated')}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
    
    return response.json() if response.status_code == 200 else None


def test_basic_import():
    """Test basic import without authentication"""
    print("\n" + "=" * 60)
    print("Testing Basic Import")
    print("=" * 60)
    
    # Try with a public article first
    url = "https://blog.pragmaticengineer.com/how-big-tech-runs-tech-projects-and-the-curious-absence-of-scrum/"
    
    response = requests.post(
        f"{BASE_URL}/import-basic",
        json={"url": url}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        if data.get('success'):
            print(f"📄 Title: {data.get('title')}")
            print(f"✍️ Author: {data.get('author')}")
            print(f"📊 Word Count: {data.get('word_count')}")
            print(f"🆔 Article ID: {data.get('article_id')}")
        else:
            print(f"⚠️ Import failed: {data.get('error')}")
            if data.get('requires_auth'):
                print("🔐 This article requires authentication")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
    
    return response.json() if response.status_code == 200 else None


def test_cookie_import_with_sample():
    """Test cookie import with a sample cookie string"""
    print("\n" + "=" * 60)
    print("Testing Cookie Import (with sample cookies)")
    print("=" * 60)
    
    url = "https://magazine.sebastianraschka.com/p/llm-research-papers-2025-list-one"
    
    # Sample cookie string (won't work without real cookies)
    cookie_string = "session_id=abc123; auth_token=xyz789"
    
    response = requests.post(
        f"{BASE_URL}/import-with-cookie-string",
        json={
            "url": url,
            "cookies": cookie_string
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        if data.get('success'):
            print(f"📄 Title: {data.get('title')}")
            print(f"✍️ Author: {data.get('author')}")
            print(f"📊 Word Count: {data.get('word_count')}")
            if data.get('content_increase'):
                print(f"📈 Content Increase: {data.get('content_increase')}")
        else:
            print(f"⚠️ Import failed: {data.get('error')}")
            if data.get('requires_auth'):
                print("🔐 Authentication may have failed - check cookies")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
    
    return response.json() if response.status_code == 200 else None


def test_curl_import():
    """Test import with cURL command"""
    print("\n" + "=" * 60)
    print("Testing cURL Import")
    print("=" * 60)
    
    url = "https://magazine.sebastianraschka.com/p/llm-research-papers-2025-list-one"
    
    # Sample cURL command (won't work without real cookies)
    curl_command = """curl 'https://magazine.sebastianraschka.com/p/llm-research-papers-2025-list-one' -H 'cookie: session_id=abc123; auth_token=xyz789'"""
    
    response = requests.post(
        f"{BASE_URL}/import-with-cookies",
        json={
            "url": url,
            "curl_command": curl_command
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        if data.get('success'):
            print(f"📄 Title: {data.get('title')}")
            print(f"✍️ Author: {data.get('author')}")
            print(f"📊 Word Count: {data.get('word_count')}")
        else:
            print(f"⚠️ Import failed: {data.get('error')}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
    
    return response.json() if response.status_code == 200 else None


def main():
    print("🚀 Testing Enhanced Article Import API")
    print("=" * 60)
    
    # Test paywall check
    paywall_result = test_check_paywall()
    
    # Test basic import
    basic_result = test_basic_import()
    
    # Test cookie import (will fail without real cookies)
    cookie_result = test_cookie_import_with_sample()
    
    # Test cURL import (will fail without real cookies)
    curl_result = test_curl_import()
    
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    print(f"✅ Paywall Check: {'Success' if paywall_result else 'Failed'}")
    print(f"✅ Basic Import: {'Success' if basic_result and basic_result.get('success') else 'Failed'}")
    print(f"⚠️ Cookie Import: {'Success' if cookie_result and cookie_result.get('success') else 'Expected failure (no real cookies)'}")
    print(f"⚠️ cURL Import: {'Success' if curl_result and curl_result.get('success') else 'Expected failure (no real cookies)'}")
    
    print("\n💡 To test with real authentication:")
    print("1. Sign in to the Substack publication in your browser")
    print("2. Open Developer Tools (F12)")
    print("3. Go to Application/Storage → Cookies")
    print("4. Copy the cookie string and use it in the API")


if __name__ == "__main__":
    main()