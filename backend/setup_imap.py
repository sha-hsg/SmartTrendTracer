#!/usr/bin/env python3
"""
Setup IMAP access for Substack collection (Simpler alternative to Gmail API)
"""
import os
import sys
from pathlib import Path
from getpass import getpass

def setup_imap():
    print("=" * 60)
    print("📧 IMAP Setup for Substack Collection")
    print("=" * 60)
    print()
    print("This is a simpler alternative to Gmail API.")
    print("Works with Gmail, Outlook, Yahoo, and most email providers.")
    print()
    
    # Check if .env exists
    env_path = Path(".env")
    if env_path.exists():
        print("Found existing .env file")
        overwrite = input("Update email settings? (y/n): ")
        if overwrite.lower() != 'y':
            print("Keeping existing settings.")
            return test_connection()
    
    print("\n📮 Choose your email provider:")
    print("1. Gmail")
    print("2. Outlook/Hotmail")
    print("3. Yahoo")
    print("4. Other (custom IMAP)")
    
    choice = input("\nEnter choice (1-4): ")
    
    # Set IMAP server based on choice
    if choice == '1':
        imap_server = "imap.gmail.com"
        imap_port = 993
        print("\n📌 Gmail Setup Instructions:")
        print("1. Enable 2-factor authentication in your Google Account")
        print("2. Generate an app-specific password:")
        print("   https://myaccount.google.com/apppasswords")
        print("3. Use that password (NOT your regular password)")
        print()
    elif choice == '2':
        imap_server = "outlook.office365.com"
        imap_port = 993
        print("\n📌 Outlook Setup Instructions:")
        print("1. Enable 2-factor authentication")
        print("2. Generate an app password:")
        print("   https://account.microsoft.com/security")
        print("3. Use that app password below")
        print()
    elif choice == '3':
        imap_server = "imap.mail.yahoo.com"
        imap_port = 993
        print("\n📌 Yahoo Setup Instructions:")
        print("1. Generate an app password:")
        print("   https://login.yahoo.com/account/security")
        print("2. Use that app password below")
        print()
    else:
        imap_server = input("Enter IMAP server (e.g., imap.gmail.com): ")
        imap_port = int(input("Enter IMAP port (usually 993): ") or "993")
    
    # Get credentials
    print("\n🔑 Enter Credentials:")
    email_address = input("Email address: ")
    email_password = getpass("App password (hidden): ")
    
    # Write to .env file
    print("\n💾 Saving configuration...")
    
    env_content = []
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                if not line.startswith(('EMAIL_ADDRESS=', 'EMAIL_PASSWORD=', 'IMAP_SERVER=', 'IMAP_PORT=')):
                    env_content.append(line)
    
    env_content.extend([
        f"\n# Email settings for Substack collection\n",
        f"EMAIL_ADDRESS={email_address}\n",
        f"EMAIL_PASSWORD={email_password}\n",
        f"IMAP_SERVER={imap_server}\n",
        f"IMAP_PORT={imap_port}\n"
    ])
    
    with open(env_path, 'w') as f:
        f.writelines(env_content)
    
    print("✅ Configuration saved to .env file")
    
    # Test connection
    return test_connection()

def test_connection():
    """Test IMAP connection"""
    print("\n🧪 Testing connection...")
    
    try:
        from app.collectors.imap_substack_collector import IMAPSubstackCollector
        
        collector = IMAPSubstackCollector()
        collector.connect()
        
        # Search for emails
        emails = collector.search_substack_emails(max_results=5)
        
        if emails:
            print(f"✅ Success! Found {len(emails)} Substack emails")
            print("\nYou can now collect newsletters with:")
            print("  python -m app.collectors.imap_substack_collector")
        else:
            print("⚠️  Connected but no Substack emails found.")
            print("This is normal if you haven't received any yet.")
            print("\nTry:")
            print("1. Forward a Substack email to this account")
            print("2. Subscribe to a Substack newsletter")
        
        # Disconnect
        if collector.imap:
            collector.imap.logout()
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check your email and password")
        print("2. For Gmail: Make sure you're using an app password")
        print("3. Check internet connection")
        print("4. Some accounts need 'less secure apps' enabled")
        return False

if __name__ == "__main__":
    print("Choose setup method:\n")
    print("1. IMAP (Simple, works with app passwords)")
    print("2. Gmail API (OAuth, more complex)")
    
    choice = input("\nEnter choice (1 or 2): ")
    
    if choice == '1':
        success = setup_imap()
    else:
        print("\nFor Gmail API setup, run:")
        print("  python setup_gmail.py")
        sys.exit(0)
    
    sys.exit(0 if success else 1)