#!/usr/bin/env python3
"""
Interactive script to import articles with your browser cookies
"""

import requests
import json
from datetime import datetime

def import_with_curl():
    """Import article using cURL command from browser"""
    
    print("=" * 60)
    print("📥 IMPORT SUBSCRIBER-ONLY ARTICLES")
    print("=" * 60)
    
    print("\n📋 INSTRUCTIONS:")
    print("1. Open the article in your browser and sign in")
    print("2. Open Developer Tools (F12)")
    print("3. Go to Network tab and refresh the page")
    print("4. Find the main article request")
    print("5. Right-click → Copy → Copy as cURL")
    print("=" * 60)
    
    # Get article URL
    article_url = input("\n🔗 Enter the article URL: ").strip()
    
    if not article_url:
        print("❌ No URL provided")
        return
    
    print(f"\n📄 Article: {article_url}")
    
    # Get cURL command
    print("\n📋 Paste your cURL command below (press Enter twice when done):")
    print("=" * 60)
    
    curl_lines = []
    while True:
        line = input()
        if not line and curl_lines and not curl_lines[-1]:
            break
        curl_lines.append(line)
    
    curl_command = ' '.join(curl_lines).strip()
    
    if not curl_command:
        print("❌ No cURL command provided")
        return
    
    print("\n🔄 Processing import...")
    
    # Call the API
    try:
        response = requests.post(
            "http://localhost:8000/api/v2/articles/enhanced/import-with-cookies",
            json={
                "url": article_url,
                "curl_command": curl_command
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                print("\n" + "=" * 60)
                print("✅ IMPORT SUCCESSFUL!")
                print("=" * 60)
                print(f"📄 Title: {data.get('title')}")
                print(f"✍️ Author: {data.get('author')}")
                print(f"📊 Word Count: {data.get('word_count'):,} words")
                
                if data.get('content_increase'):
                    print(f"📈 Content Increase: {data.get('content_increase')}")
                
                print(f"🆔 Article ID: {data.get('article_id')}")
                print("\n✨ You can now view the full article in SmartTrendTracer!")
                
            else:
                print(f"\n❌ Import failed: {data.get('error')}")
                if data.get('requires_auth'):
                    print("🔐 This article requires authentication")
                    print("   Make sure you're signed in and copied the correct cURL")
        else:
            print(f"\n❌ API Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Make sure the SmartTrendTracer API is running:")
        print("   cd backend && python -m uvicorn app.main:app --reload")


def import_with_cookie_string():
    """Import article using cookie string"""
    
    print("=" * 60)
    print("🍪 IMPORT WITH COOKIE STRING")
    print("=" * 60)
    
    print("\n📋 INSTRUCTIONS:")
    print("1. Open the article in your browser and sign in")
    print("2. Open Developer Tools (F12)")
    print("3. Go to Application → Storage → Cookies")
    print("4. Copy the important cookies (connect.sid, etc.)")
    print("=" * 60)
    
    # Get article URL
    article_url = input("\n🔗 Enter the article URL: ").strip()
    
    if not article_url:
        print("❌ No URL provided")
        return
    
    print(f"\n📄 Article: {article_url}")
    
    # Get cookie string
    print("\n🍪 Enter cookie string (format: name=value; name2=value2):")
    cookie_string = input().strip()
    
    if not cookie_string:
        print("❌ No cookies provided")
        return
    
    print("\n🔄 Processing import...")
    
    # Call the API
    try:
        response = requests.post(
            "http://localhost:8000/api/v2/articles/enhanced/import-with-cookie-string",
            json={
                "url": article_url,
                "cookies": cookie_string
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                print("\n" + "=" * 60)
                print("✅ IMPORT SUCCESSFUL!")
                print("=" * 60)
                print(f"📄 Title: {data.get('title')}")
                print(f"✍️ Author: {data.get('author')}")
                print(f"📊 Word Count: {data.get('word_count'):,} words")
                
                if data.get('content_increase'):
                    print(f"📈 Content Increase: {data.get('content_increase')}")
                
                print(f"🆔 Article ID: {data.get('article_id')}")
                print("\n✨ You can now view the full article in SmartTrendTracer!")
                
            else:
                print(f"\n❌ Import failed: {data.get('error')}")
                if data.get('requires_auth'):
                    print("🔐 Authentication may have failed - check cookies")
        else:
            print(f"\n❌ API Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Make sure the SmartTrendTracer API is running:")
        print("   cd backend && python -m uvicorn app.main:app --reload")


def main():
    print("\n🚀 SmartTrendTracer - Article Importer")
    print("=" * 60)
    print("\nChoose import method:")
    print("1. Import with cURL (recommended)")
    print("2. Import with cookie string")
    print("3. Exit")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        import_with_curl()
    elif choice == "2":
        import_with_cookie_string()
    elif choice == "3":
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice")


if __name__ == "__main__":
    main()