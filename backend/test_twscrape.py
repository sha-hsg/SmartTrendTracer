#!/usr/bin/env python3
"""
Simple test of twscrape functionality
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from twscrape import API

async def test_twscrape():
    print("🧪 TESTING TWSCRAPE")
    print("=" * 60)
    
    api = API()
    
    try:
        # Check accounts
        accounts = await api.pool.accounts_info()
        print(f"✅ Found {len(accounts)} account(s)")
        
        # Try to get a single tweet from a known account
        print("\n🔄 Testing tweet collection from @OpenAI...")
        
        tweet_count = 0
        async for tweet in api.user_tweets("OpenAI", limit=1):
            tweet_count += 1
            print(f"\n✅ Successfully retrieved tweet!")
            print(f"   ID: {tweet.id}")
            print(f"   Date: {tweet.date}")
            print(f"   Text: {tweet.rawContent[:100]}...")
            break
        
        if tweet_count == 0:
            print("⚠️  No tweets retrieved (account may need login)")
            print("\n💡 Trying with user ID instead...")
            
            # Try with user ID
            async for tweet in api.user_tweets_and_replies(4398626122, limit=1):
                tweet_count += 1
                print(f"\n✅ Successfully retrieved tweet with ID!")
                print(f"   ID: {tweet.id}")
                print(f"   Date: {tweet.date}")
                print(f"   Text: {tweet.rawContent[:100]}...")
                break
        
        if tweet_count > 0:
            print("\n🎉 TWSCRAPE IS WORKING!")
            print("   You can now use:")
            print("   • python collect_twscrape.py")
            print("   • python smart_collect.py")
        else:
            print("\n⚠️  TWSCRAPE NEEDS CONFIGURATION")
            print("   The guest account may not work for all operations.")
            print("   Consider adding a real account (use at your own risk):")
            print("   python setup_twscrape.py")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Guest accounts have limitations")
        print("   2. Twitter may have changed their API")
        print("   3. Try updating twscrape: pip install --upgrade twscrape")

if __name__ == "__main__":
    print("This will test if twscrape can retrieve tweets.\n")
    asyncio.run(test_twscrape())