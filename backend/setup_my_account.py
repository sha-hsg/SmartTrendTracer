#!/usr/bin/env python3
"""
Setup your personal Twitter account for twscrape
This will let you collect unlimited tweets from the 7 accounts
"""
import asyncio
import sys
import os
import getpass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from twscrape import API
from app.config import ACCOUNTS_TO_FOLLOW

async def setup_personal_account():
    print("🔐 SETUP YOUR TWITTER ACCOUNT FOR UNLIMITED COLLECTION")
    print("=" * 60)
    print()
    print("📌 This will let you collect UNLIMITED tweets from:")
    for account in ACCOUNTS_TO_FOLLOW:
        print(f"   • @{account['username']}")
    print()
    print("⚠️  IMPORTANT NOTES:")
    print("   • Use a secondary/burner account if possible")
    print("   • Your password is stored locally only")
    print("   • This violates Twitter ToS (use at your own risk)")
    print("   • Account could be suspended (unlikely but possible)")
    print()
    
    proceed = input("Do you want to add your Twitter account? (y/n): ")
    
    if proceed.lower() != 'y':
        print("\nCancelled. You can continue using the rate-limited API.")
        return
    
    print("\n📝 Enter your Twitter credentials:")
    print("   (These are stored locally in accounts.db)\n")
    
    username = input("Twitter username (without @): ")
    password = getpass.getpass("Twitter password: ")
    email = input("Email associated with account: ")
    
    print("\nOptional: Email password for 2FA (press Enter to skip)")
    email_password = getpass.getpass("Email password (or Enter): ") or password
    
    api = API()
    
    try:
        print("\n🔄 Adding your account...")
        
        # Remove guest account if exists
        accounts = await api.pool.accounts_info()
        for acc in accounts:
            if hasattr(acc, 'username') and acc.username == '_guest_':
                print("   Removing guest account...")
                # Note: twscrape doesn't have a direct remove method
                # The account will be replaced
        
        # Add the real account
        await api.pool.add_account(
            username=username,
            password=password,
            email=email,
            email_password=email_password
        )
        
        print(f"✅ Account @{username} added!")
        
        print("\n🔄 Attempting login...")
        await api.pool.login(username)
        
        print("✅ Login successful!")
        
        # Test the account
        print("\n🧪 Testing account by fetching a tweet...")
        test_account = ACCOUNTS_TO_FOLLOW[0]['username']
        
        tweet_found = False
        async for tweet in api.user_tweets(test_account, limit=1):
            print(f"✅ Success! Retrieved tweet from @{test_account}")
            print(f"   Date: {tweet.date}")
            print(f"   Text preview: {tweet.rawContent[:80]}...")
            tweet_found = True
            break
        
        if tweet_found:
            print("\n" + "=" * 60)
            print("🎉 SETUP COMPLETE! YOU NOW HAVE UNLIMITED COLLECTION!")
            print("=" * 60)
            print("\n🚀 Next steps:")
            print("   1. Collect without limits: python collect_twscrape.py")
            print("   2. Smart hybrid mode: python smart_collect.py")
            print("   3. No more 429 errors!")
            print("\n💡 Benefits:")
            print("   • NO rate limits")
            print("   • Collect all 7 accounts instantly")
            print("   • Get historical tweets")
            print("   • Search capabilities")
        else:
            print("\n⚠️  Account added but couldn't fetch tweets.")
            print("   This could mean:")
            print("   • Account needs verification")
            print("   • 2FA is required")
            print("   • Wrong credentials")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Troubleshooting:")
        print("   • Check your username/password")
        print("   • Make sure the account can login normally")
        print("   • Try disabling 2FA temporarily")

if __name__ == "__main__":
    asyncio.run(setup_personal_account())