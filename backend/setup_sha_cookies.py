#!/usr/bin/env python3
"""
Setup sha_hsg account with cookies
"""
import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from twscrape import API
import aiosqlite

async def setup_with_sha_cookies():
    print("🍪 SETTING UP TWITTER WITH YOUR COOKIES")
    print("=" * 60)
    
    # Your cookies
    auth_token = "8a9436096a3a228509a01a63659538d58332aec5"
    ct0 = "fab91742a9bda85ada33f4435e0793ce4ead14b6c07b88210ce59afac02d68d35ca0e1f6c052a22d67835e4d063f2d8eecf74ca7e23a62d21529209d00bf5ecd741c8daaa948bd2083085d813036c1d0"
    
    print(f"✅ Found auth_token: {auth_token[:20]}...")
    print(f"✅ Found ct0: {ct0[:20]}...")
    
    # Save cookies to file for future use
    cookies_data = [
        {
            "name": "auth_token",
            "value": auth_token,
            "domain": ".twitter.com"
        },
        {
            "name": "ct0",
            "value": ct0,
            "domain": ".twitter.com"
        }
    ]
    
    with open("cookies.json", "w") as f:
        json.dump(cookies_data, f, indent=2)
    print("💾 Saved cookies to cookies.json")
    
    # Setup twscrape
    api = API()
    
    # Clear old accounts
    try:
        async with aiosqlite.connect("accounts.db") as db:
            await db.execute("DELETE FROM accounts WHERE username = 'sha_hsg' OR username = '_guest_'")
            await db.commit()
            print("🔄 Cleared old accounts")
    except:
        pass
    
    # Add account with cookies
    print("\n🔐 Adding account with cookies...")
    
    # Twscrape stores cookies differently - we need to add as logged-in account
    await api.pool.add_account(
        username="sha_hsg",
        password="cookie_auth",
        email="siegfried.handschuh@gmail.com",
        email_password="cookie_auth"
    )
    
    # Mark as logged in with cookies
    async with aiosqlite.connect("accounts.db") as db:
        await db.execute(
            "UPDATE accounts SET active = 1, locked = 0, logged_in = 1 WHERE username = 'sha_hsg'"
        )
        await db.commit()
    
    print("✅ Account configured with cookies!")
    
    # Test the setup
    print("\n🧪 Testing cookie authentication...")
    print("Trying to get tweets (including RETWEETS!)...\n")
    
    success = False
    try:
        # Test with OpenAI account
        tweet_count = 0
        async for tweet in api.user_tweets("OpenAI", limit=5):
            tweet_count += 1
            
            # Check if it's a retweet
            is_retweet = tweet.retweetedTweet is not None
            tweet_type = "🔁 RETWEET" if is_retweet else "📝 TWEET"
            
            print(f"{tweet_count}. [{tweet_type}] {tweet.date.strftime('%Y-%m-%d %H:%M')}")
            print(f"   {tweet.rawContent[:80]}...")
            
            if is_retweet:
                print("   ✨ This is a RETWEET - we can capture these now!")
            
            success = True
        
        if tweet_count == 0:
            print("⚠️  No tweets retrieved - cookies might need refresh")
    
    except Exception as e:
        print(f"❌ Error: {str(e)[:200]}")
        print("\n💡 Cookies might be expired. Try:")
        print("   1. Login to Twitter again")
        print("   2. Get fresh cookies")
        print("   3. Run this script again")
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 SUCCESS! COOKIES ARE WORKING!")
        print("=" * 60)
        print("\n🚀 You can now:")
        print("   • Collect ALL tweets including RETWEETS")
        print("   • No rate limits!")
        print("   • See everything Hugging Face retweeted")
        print("\n📊 Run collection:")
        print("   python collect_all_with_retweets.py")
        print("\n🔄 Your scheduled collector will now get retweets too!")

if __name__ == "__main__":
    asyncio.run(setup_with_sha_cookies())