#!/usr/bin/env python3
"""
Update sha_hsg account with correct email
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from twscrape import API
import aiosqlite

async def update_account():
    print("📧 UPDATING ACCOUNT EMAIL")
    print("=" * 60)
    
    api = API()
    
    try:
        # First, remove the old account
        print("🔄 Removing old account entry...")
        
        # Direct database operation to remove old account
        db_path = "accounts.db"
        async with aiosqlite.connect(db_path) as db:
            await db.execute("DELETE FROM accounts WHERE username = 'sha_hsg'")
            await db.commit()
            print("✅ Old account removed")
        
        # Add account with correct email
        print("\n📝 Adding account with correct email...")
        
        await api.pool.add_account(
            username="sha_hsg",
            password="andy-mandrake-walkover-horizon",
            email="siegfried.handschuh@gmail.com",
            email_password="andy-mandrake-walkover-horizon"  # Using same as Twitter password
        )
        
        print("✅ Account updated with email: siegfried.handschuh@gmail.com")
        
        # Try to login
        print("\n🔐 Attempting login...")
        try:
            await api.pool.login("sha_hsg")
            print("✅ Login initiated successfully!")
        except Exception as e:
            print(f"⚠️  Login requires verification: {str(e)[:100]}")
        
        # Check account status
        print("\n📊 Account Status:")
        accounts = await api.pool.accounts_info()
        
        for acc in accounts:
            if isinstance(acc, dict) and acc.get('username') == 'sha_hsg':
                print(f"   Username: {acc.get('username')}")
                print(f"   Active: {acc.get('active', False)}")
                print(f"   Logged in: {acc.get('logged_in', False)}")
                print(f"   Error: {acc.get('error_msg', 'None')}")
        
        print("\n💡 Next Steps:")
        print("   1. Twitter may send a verification email to siegfried.handschuh@gmail.com")
        print("   2. Check your email for verification code")
        print("   3. You may need to login via browser first")
        print("\n📌 Alternative: Export cookies from browser")
        print("   1. Login to Twitter as @sha_hsg in Chrome/Firefox")
        print("   2. Use a cookie export extension")
        print("   3. Import cookies to twscrape")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(update_account())