#!/usr/bin/env python3
"""
Setup Gmail API for Substack collection

This script guides you through setting up Gmail API access for collecting Substack newsletters.
"""

import sys
import os
from pathlib import Path

def setup_gmail():
    print("=" * 60)
    print("📧 Gmail API Setup for Substack Collection")
    print("=" * 60)
    print()
    
    print("This setup will help you configure Gmail access to collect Substack newsletters.")
    print()
    
    print("📋 Prerequisites:")
    print("1. A Google account with Gmail")
    print("2. Substack newsletters arriving in that Gmail account")
    print()
    
    input("Press Enter to continue...")
    print()
    
    print("🔧 Step 1: Enable Gmail API")
    print("-" * 40)
    print("1. Go to: https://console.cloud.google.com/")
    print("2. Create a new project (or select an existing one)")
    print("3. Search for 'Gmail API' in the search bar")
    print("4. Click on 'Gmail API' and then 'Enable'")
    print()
    
    input("Press Enter after enabling Gmail API...")
    print()
    
    print("🔐 Step 2: Create OAuth 2.0 Credentials")
    print("-" * 40)
    print("1. In Google Cloud Console, go to 'APIs & Services' > 'Credentials'")
    print("2. Click '+ CREATE CREDENTIALS' > 'OAuth client ID'")
    print("3. If prompted, configure the OAuth consent screen:")
    print("   - Choose 'External' user type")
    print("   - Fill in app name: 'SmartTrendTracer'")
    print("   - Add your email as support email")
    print("   - Add your email to test users")
    print("4. For Application type, choose 'Desktop app'")
    print("5. Name it: 'SmartTrendTracer Gmail Client'")
    print("6. Click 'Create'")
    print()
    
    input("Press Enter after creating credentials...")
    print()
    
    print("💾 Step 3: Download Credentials")
    print("-" * 40)
    print("1. Click the download button (⬇️) next to your new OAuth client")
    print("2. Save the file as 'credentials.json'")
    print(f"3. Move it to: {os.path.abspath('.')}")
    print()
    
    # Check if credentials.json exists
    creds_path = Path("credentials.json")
    
    while not creds_path.exists():
        print("⚠️  credentials.json not found in current directory")
        print(f"   Please place it in: {os.path.abspath('.')}")
        response = input("\nHave you placed credentials.json? (y/n): ")
        if response.lower() != 'y':
            print("\nPlease download and place credentials.json, then run this script again.")
            return False
    
    print("✅ credentials.json found!")
    print()
    
    print("🚀 Step 4: Authenticate")
    print("-" * 40)
    print("Now we'll authenticate with Gmail.")
    print("This will open a browser window where you'll:")
    print("1. Sign in to your Google account")
    print("2. Grant permission to read emails")
    print()
    
    response = input("Ready to authenticate? (y/n): ")
    if response.lower() != 'y':
        print("\nRun this script again when you're ready to authenticate.")
        return False
    
    print()
    print("Authenticating...")
    
    try:
        # Import and run authentication
        from app.collectors.gmail_substack_collector import GmailSubstackCollector
        
        collector = GmailSubstackCollector()
        collector.authenticate()
        
        print()
        print("✅ Authentication successful!")
        print("   Token saved to 'token.pickle'")
        print()
        
        # Test by searching for Substack emails
        print("📧 Testing: Searching for Substack emails...")
        message_ids = collector.search_substack_emails('from:substack.com', max_results=5)
        
        if message_ids:
            print(f"✅ Found {len(message_ids)} Substack emails!")
            print("   Gmail integration is working correctly.")
        else:
            print("⚠️  No Substack emails found.")
            print("   This might be normal if you haven't received any yet.")
            print("   Try forwarding some Substack emails to this Gmail account.")
        
    except ImportError as e:
        print(f"❌ Error: Missing dependencies")
        print(f"   Please run: pip install -r requirements_substack.txt")
        return False
    except Exception as e:
        print(f"❌ Error during authentication: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure credentials.json is valid")
        print("2. Check your internet connection")
        print("3. Try running the script again")
        return False
    
    print()
    print("=" * 60)
    print("🎉 Setup Complete!")
    print("=" * 60)
    print()
    print("You can now collect Substack newsletters with:")
    print("  python -m app.collectors.gmail_substack_collector")
    print()
    print("Or use the automated collection:")
    print("  npm run collect:substack")
    print()
    
    return True

if __name__ == "__main__":
    success = setup_gmail()
    sys.exit(0 if success else 1)