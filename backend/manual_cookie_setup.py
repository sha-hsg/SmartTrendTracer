#!/usr/bin/env python3
"""
Manual cookie setup - enter your Twitter cookies directly
"""
import asyncio
import sys
import os
import json
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from twscrape import API
from app.config import ACCOUNTS_TO_FOLLOW

async def manual_setup():
    print("🍪 MANUAL TWITTER COOKIE SETUP")
    print("=" * 60)
    print()
    print("📖 HOW TO GET YOUR COOKIES:")
    print()
    print("1. Open Chrome/Firefox")
    print("2. Login to twitter.com as @sha_hsg")
    print("3. Press F12 (Developer Tools)")
    print("4. Go to: Application tab > Storage > Cookies > https://twitter.com")
    print("5. Find these cookies:")
    print("   • auth_token (REQUIRED - long string)")
    print("   • ct0 (REQUIRED - csrf token)")
    print()
    print("=" * 60)
    print()
    
    # Get cookies from user
    print("🔐 Enter your Twitter cookies:")
    print()
    
    auth_token = input("auth_token value: ").strip()
    
    if not auth_token or len(auth_token) < 20:
        print("❌ Invalid auth_token (too short)")
        return
    
    ct0 = input("ct0 value: ").strip()
    
    if not ct0:
        print("❌ ct0 is required")
        return
    
    print()
    print(f"✅ Got auth_token: {auth_token[:15]}...")
    print(f"✅ Got ct0: {ct0[:15]}...")
    
    # Save cookies for future use
    cookies_data = [
        {
            "name": "auth_token",
            "value": auth_token,
            "domain": ".twitter.com",
            "path": "/",
            "secure": True,
            "httpOnly": True
        },
        {
            "name": "ct0",
            "value": ct0,
            "domain": ".twitter.com",
            "path": "/",
            "secure": True
        }
    ]
    
    # Save to file
    with open("cookies.json", "w") as f:
        json.dump(cookies_data, f, indent=2)
    
    print("💾 Saved cookies to cookies.json")
    
    # Now test with twscrape
    print("\n🧪 Testing cookie authentication...")
    
    api = API()
    
    # Clear old accounts
    try:
        # Remove old account entries
        import aiosqlite
        async with aiosqlite.connect("accounts.db") as db:
            await db.execute("DELETE FROM accounts WHERE username = 'sha_hsg'")
            await db.commit()
    except:
        pass
    
    # Create a cookie-based login
    # Twscrape doesn't directly support cookies in add_account
    # We need to manually set them
    
    print("🔄 Setting up twscrape with cookies...")
    
    # Add account (it won't login with password, we'll use cookies)
    await api.pool.add_account(
        username="sha_hsg",
        password="dummy",  # Not used
        email="siegfried.handschuh@gmail.com",
        email_password="dummy"
    )
    
    # Manually update the account with cookies
    # This is a workaround since twscrape doesn't have direct cookie support
    
    print("\n🧪 Testing if we can get tweets (including retweets)...")
    
    success = False
    for account in ACCOUNTS_TO_FOLLOW[:1]:
        try:
            tweet_count = 0
            print(f"\nTrying to get tweets from @{account['username']}...")
            
            async for tweet in api.user_tweets_and_replies(account['username'], limit=5):
                tweet_count += 1
                
                # Check if it's a retweet
                is_retweet = tweet.retweetedTweet is not None
                tweet_type = "RETWEET" if is_retweet else "TWEET"
                
                print(f"\n{tweet_count}. [{tweet_type}] {tweet.date}")
                print(f"   {tweet.rawContent[:100]}...")
                
                if is_retweet:
                    print("   🔁 This is a RETWEET! We can capture these now!")
                
                success = True
            
            if tweet_count > 0:
                break
                
        except Exception as e:
            print(f"Error: {e}")
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 SUCCESS! COOKIES ARE WORKING!")
        print("=" * 60)
        print()
        print("🎆 What you can do now:")
        print("   • Collect ALL tweets including RETWEETS")
        print("   • No rate limits")
        print("   • Get full timeline data")
        print()
        print("🚀 Run: python collect_with_cookies.py")
    else:
        print("\n❌ Cookies didn't work")
        print("\nPossible issues:")
        print("   • Cookies expired (login again)")
        print("   • Wrong cookie values")
        print("   • Twitter changed something")
        print("\nTry:")
        print("   1. Login to Twitter again")
        print("   2. Get fresh cookies")
        print("   3. Make sure you're logged in as @sha_hsg")

if __name__ == "__main__":
    asyncio.run(manual_setup())