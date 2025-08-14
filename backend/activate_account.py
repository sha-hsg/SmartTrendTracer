#!/usr/bin/env python3
"""
Activate and verify the sha_hsg account
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from twscrape import API

async def activate_account():
    print("🔄 ACTIVATING TWITTER ACCOUNT")
    print("=" * 60)
    
    api = API()
    
    try:
        # Check current accounts
        print("📊 Checking account status...")
        accounts = await api.pool.accounts_info()
        
        sha_account = None
        for acc in accounts:
            print(f"   Found: {acc}")
            if hasattr(acc, 'username') and acc.username == 'sha_hsg':
                sha_account = acc
        
        if not sha_account:
            print("❌ Account sha_hsg not found. Run setup_sha_account.py first")
            return
        
        # Try to login all accounts
        print("\n🔐 Attempting to login all accounts...")
        await api.pool.login_all()
        
        print("✅ Login process completed")
        
        # Check status again
        print("\n📊 Checking updated status...")
        accounts = await api.pool.accounts_info()
        
        for acc in accounts:
            if hasattr(acc, 'username'):
                status = "Active" if acc.active else "Inactive"
                print(f"   @{acc.username}: {status}")
                if acc.username == 'sha_hsg' and acc.active:
                    print("\n🎉 SUCCESS! Your account is now active!")
                    print("   You can now collect unlimited tweets!")
                    return
        
        print("\n⚠️  Account still needs verification")
        print("\n💡 Alternative: Use cookies from your browser")
        print("   1. Login to Twitter in your browser")
        print("   2. Export cookies")
        print("   3. Use with twscrape")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 The account may need manual verification on Twitter's website")

if __name__ == "__main__":
    asyncio.run(activate_account())