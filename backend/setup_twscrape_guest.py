#!/usr/bin/env python3
"""
Quick setup of twscrape with guest account (non-interactive)
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from twscrape import API

async def setup_guest():
    print("🔧 TWSCRAPE GUEST SETUP")
    print("=" * 60)
    
    api = API()
    
    try:
        # Check existing accounts
        accounts = await api.pool.accounts_info()
        
        if accounts:
            print(f"\n✅ Already have {len(accounts)} account(s) configured")
            # accounts is a list of account objects
            for account in accounts:
                username = account.username if hasattr(account, 'username') else str(account)
                status = "Active" if (hasattr(account, 'active') and account.active) else "Inactive"
                print(f"   • {username}: {status}")
        else:
            print("\n🔄 Setting up guest account...")
            
            # Add guest account
            await api.pool.add_account(
                username="_guest_",
                password="_guest_",
                email="guest@example.com",
                email_password="_guest_"
            )
            
            print("✅ Guest account added successfully!")
            print("\n💡 Note: Guest account has limitations but works without login")
        
        print("\n🎯 Next steps:")
        print("   1. Run: python collect_twscrape.py")
        print("   2. Or: python smart_collect.py (hybrid mode)")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 This is normal if account already exists")

if __name__ == "__main__":
    asyncio.run(setup_guest())