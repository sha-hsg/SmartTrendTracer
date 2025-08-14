#!/usr/bin/env python3
"""
Check and debug twscrape accounts
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from twscrape import API

async def check_accounts():
    print("🔍 TWSCRAPE ACCOUNT DETAILS")
    print("=" * 60)
    
    api = API()
    
    try:
        # Get all accounts
        accounts = await api.pool.accounts_info()
        
        print(f"\n📊 Found {len(accounts)} account(s):\n")
        
        for i, acc in enumerate(accounts, 1):
            print(f"Account #{i}:")
            
            # Check if it's a dict or object
            if isinstance(acc, dict):
                for key, value in acc.items():
                    print(f"   {key}: {value}")
            else:
                # Try to access attributes
                for attr in dir(acc):
                    if not attr.startswith('_'):
                        try:
                            value = getattr(acc, attr)
                            if not callable(value):
                                print(f"   {attr}: {value}")
                        except:
                            pass
            print()
        
        # Try to login the sha_hsg account specifically
        print("🔐 Attempting to activate sha_hsg account...")
        
        # Get all accounts as raw data
        all_accounts = await api.pool.get_all()
        for username, acc_data in all_accounts.items():
            if username == 'sha_hsg':
                print(f"\nFound sha_hsg account data:")
                print(f"   Username: {username}")
                print(f"   Data: {acc_data}")
                
                # Try to login this specific account
                try:
                    print("\n🔄 Attempting login for sha_hsg...")
                    await api.pool.login(username)
                    print("✅ Login command sent")
                except Exception as e:
                    print(f"⚠️  Login error: {e}")
        
        # Check if we can use the account now
        print("\n🧪 Testing if account works...")
        
        # Re-check accounts after login attempt
        accounts = await api.pool.accounts_info()
        for acc in accounts:
            if isinstance(acc, dict) and acc.get('username') == 'sha_hsg':
                if acc.get('active'):
                    print("🎉 Account is ACTIVE! You can collect tweets now!")
                else:
                    print(f"⚠️  Account status: {acc}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_accounts())