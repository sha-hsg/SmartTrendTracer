#!/usr/bin/env python3
"""
Setup twscrape with browser cookies
This allows full access including retweets!
"""
import asyncio
import sys
import os
import json
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from twscrape import API

async def setup_with_cookies():
    print("🍪 TWSCRAPE COOKIE SETUP")
    print("=" * 60)
    print()
    print("📖 INSTRUCTIONS:")
    print()
    print("Step 1: Login to Twitter in your browser")
    print("   • Open Chrome or Firefox")
    print("   • Go to twitter.com")
    print("   • Login as @sha_hsg")
    print()
    print("Step 2: Export cookies")
    print("   • Install browser extension: 'Cookie-Editor' or 'EditThisCookie'")
    print("   • Click the extension icon while on twitter.com")
    print("   • Export/Copy all cookies (JSON format)")
    print()
    print("Step 3: Save cookies to file")
    print("   • Create file: cookies.json")
    print("   • Paste the exported cookies")
    print("   • Save in this directory")
    print()
    print("=" * 60)
    
    # Check if cookies file exists
    cookies_file = Path("cookies.json")
    
    if not cookies_file.exists():
        print()
        print("❌ cookies.json not found!")
        print()
        print("💡 Quick method for Chrome:")
        print("   1. Open Chrome DevTools (F12)")
        print("   2. Go to Application > Cookies > https://twitter.com")
        print("   3. You need these cookies:")
        print("      - auth_token (most important!)")
        print("      - ct0")
        print("      - guest_id")
        print()
        print("📄 Create cookies.json with this format:")
        print(json.dumps([
            {
                "name": "auth_token",
                "value": "YOUR_AUTH_TOKEN_HERE",
                "domain": ".twitter.com"
            },
            {
                "name": "ct0",
                "value": "YOUR_CT0_HERE",
                "domain": ".twitter.com"
            }
        ], indent=2))
        return
    
    print("✅ Found cookies.json")
    print()
    
    # Load cookies
    try:
        with open(cookies_file, 'r') as f:
            cookies = json.load(f)
        
        print(f"🍪 Loaded {len(cookies)} cookies")
        
        # Extract important cookies
        auth_token = None
        ct0 = None
        
        for cookie in cookies:
            if cookie.get('name') == 'auth_token':
                auth_token = cookie.get('value')
            elif cookie.get('name') == 'ct0':
                ct0 = cookie.get('value')
        
        if not auth_token:
            print("❌ auth_token not found in cookies!")
            return
        
        print(f"✅ Found auth_token: {auth_token[:10]}...")
        if ct0:
            print(f"✅ Found ct0: {ct0[:10]}...")
        
        # Setup twscrape with cookies
        api = API()
        
        print("\n🔄 Setting up account with cookies...")
        
        # Add account with cookies
        # Twscrape will use the cookies for authentication
        await api.pool.add_account(
            username="sha_hsg",
            password="cookie_auth",  # Not used with cookies
            email="siegfried.handschuh@gmail.com",
            email_password="cookie_auth",
            cookies={
                'auth_token': auth_token,
                'ct0': ct0
            }
        )
        
        print("✅ Account added with cookies!")
        
        # Test the setup
        print("\n🧪 Testing cookie authentication...")
        
        test_success = False
        async for tweet in api.user_tweets("OpenAI", limit=1):
            print(f"✅ SUCCESS! Can retrieve tweets!")
            print(f"   Tweet: {tweet.rawContent[:60]}...")
            test_success = True
            break
        
        if test_success:
            print("\n" + "=" * 60)
            print("🎉 COOKIE SETUP SUCCESSFUL!")
            print("=" * 60)
            print()
            print("🚀 You can now:")
            print("   • Collect ALL tweets (including retweets!)")
            print("   • No rate limits")
            print("   • Run: python collect_with_cookies.py")
        else:
            print("\n⚠️  Cookies might be expired or invalid")
            print("   Try logging in again and exporting fresh cookies")
        
    except json.JSONDecodeError:
        print("❌ Invalid JSON in cookies.json")
        print("   Make sure it's valid JSON format")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(setup_with_cookies())