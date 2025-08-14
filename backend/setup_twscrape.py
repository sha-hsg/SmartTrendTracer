#!/usr/bin/env python3
"""
Setup twscrape accounts
You can add your own Twitter accounts here for better access
"""
import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from twscrape import API

async def setup_accounts():
    print("🔧 TWSCRAPE ACCOUNT SETUP")
    print("=" * 60)
    
    api = API()
    
    # Check existing accounts
    accounts = await api.pool.accounts_info()
    
    if accounts:
        print(f"\n📊 Current accounts ({len(accounts)}):")
        for username, info in accounts.items():
            status = "Active" if info.get('active') else "Inactive"
            print(f"   • @{username}: {status}")
    else:
        print("\n📝 No accounts configured")
    
    print("\n💡 Options:")
    print("1. Use guest account (limited but works)")
    print("2. Add your own Twitter account (better access)")
    print("3. Skip setup")
    
    choice = input("\nChoose option (1-3): ")
    
    if choice == "1":
        print("\n🔄 Setting up guest account...")
        try:
            # Guest account doesn't need real credentials
            await api.pool.add_account(
                username="_guest_",
                password="_guest_",
                email="guest@example.com",
                email_password="_guest_"
            )
            print("✅ Guest account added")
            print("   Note: Guest access has limitations")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    elif choice == "2":
        print("\n🔐 Add Twitter Account")
        print("⚠️  WARNING: Use at your own risk!")
        print("   - Use a secondary/burner account")
        print("   - Account may be suspended")
        print("   - Violates Twitter ToS")
        
        proceed = input("\nContinue? (y/n): ")
        if proceed.lower() == 'y':
            username = input("Username (without @): ")
            password = input("Password: ")
            email = input("Email: ")
            email_password = input("Email password (for 2FA, or press Enter to skip): ") or password
            
            try:
                await api.pool.add_account(
                    username=username,
                    password=password,
                    email=email,
                    email_password=email_password
                )
                print(f"\n✅ Account @{username} added")
                
                print("\n🔄 Attempting login...")
                await api.pool.login(username)
                print("✅ Login successful!")
                
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("   Account may need manual verification")
    
    else:
        print("\n⏸ Setup skipped")
    
    # Show final status
    accounts = await api.pool.accounts_info()
    if accounts:
        print(f"\n📊 Final account status ({len(accounts)}):")
        for username, info in accounts.items():
            status = "Active" if info.get('active') else "Inactive"
            print(f"   • @{username}: {status}")
    
    print("\n" + "=" * 60)
    print("💡 Next steps:")
    print("   1. Run: python collect_twscrape.py")
    print("   2. No rate limits!")
    print("   3. Collect as much as you want")

if __name__ == "__main__":
    asyncio.run(setup_accounts())