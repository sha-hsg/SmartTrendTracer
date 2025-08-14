#!/usr/bin/env python3
"""Debug author parsing logic for forwarded emails"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.collectors.gmail_substack_collector import GmailSubstackCollector

def main():
    collector = GmailSubstackCollector()
    collector.authenticate()
    
    # Test with one of the misattributed LumberjackAI articles
    gmail_id = "1975ec1a161c5438"  # "I'm shutting Lumberjack down"
    
    print("🔍 DEBUGGING AUTHOR PARSING FOR MISATTRIBUTED ARTICLE")
    print("=" * 80)
    print(f"Gmail ID: {gmail_id}")
    print(f"Expected: David Szabo-Stuban (lumberjackai@substack.com)")
    print(f"Currently attributed to: Ethan Mollick")
    
    # Get email content and debug the parsing
    message = collector.service.users().messages().get(
        userId='me',
        id=gmail_id,
        format='full'
    ).execute()
    
    if not message:
        print("❌ Failed to fetch message")
        return
    
    # Extract headers
    headers = message['payload'].get('headers', [])
    header_dict = {h['name']: h['value'] for h in headers}
    
    subject = header_dict.get('Subject', '')
    sender = header_dict.get('From', '')
    
    print(f"\n📧 EMAIL HEADERS:")
    print(f"Subject: {subject}")
    print(f"From: {sender}")
    
    # Extract HTML body
    html_body = collector._extract_html_body(message['payload'])
    print(f"HTML body length: {len(html_body)}")
    
    # Test author parsing
    print(f"\n🧪 TESTING AUTHOR PARSING:")
    author_info = collector._parse_author_from_sender(sender, html_body)
    
    print(f"Parsed author result:")
    print(f"  Name: {author_info['name']}")
    print(f"  Subdomain: {author_info['subdomain']}")
    print(f"  Email: {author_info['email']}")
    
    # Debug the parsing logic step by step
    print(f"\n🔍 DEBUGGING PARSE LOGIC:")
    
    # Check if this is recognized as forwarded
    is_self_forwarded = ('siegfried.handschuh@gmail.com' in sender or 
                        'siegfried.handschuh@unisg.ch' in sender or 
                        'from:me to:me' in str(html_body))
    
    print(f"Recognized as self-forwarded: {is_self_forwarded}")
    
    if is_self_forwarded:
        # Load forwarded authors config
        from pathlib import Path
        import json
        
        config_path = Path(__file__).parent.parent / 'forwarded_authors.json'
        forwarded_authors = {}
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
                forwarded_authors = {
                    author['email'].lower(): author 
                    for author in config.get('forwarded_authors', [])
                }
        
        print(f"Loaded {len(forwarded_authors)} configured forwarded authors")
        for email, author in forwarded_authors.items():
            print(f"  - {author['name']} ({email})")
        
        # Check if any configured authors are found in content
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_body, 'html.parser')
        text_content = soup.get_text()
        
        print(f"\nSearching for author indicators in email content...")
        print(f"Content length: {len(text_content)} chars")
        print(f"Content preview: {text_content[:500]}...")
        
        # Look for each configured author
        for email, author_config in forwarded_authors.items():
            author_indicators = [
                author_config['name'],                    # "Nathan Lambert"
                author_config.get('newsletter', ''),     # "Interconnects"  
                email,                                    # "robotic@substack.com"
                email.split('@')[0]                       # "robotic"
            ]
            
            print(f"\nChecking for {author_config['name']}:")
            for indicator in author_indicators:
                if indicator and indicator.lower() in text_content.lower():
                    print(f"  ✓ Found indicator: '{indicator}'")
                else:
                    print(f"  ✗ Missing: '{indicator}'")
        
        # Look for LumberjackAI specifically
        lumberjack_indicators = [
            'lumberjackai@substack.com',
            'david szabo',
            'lumberjack',
            'david szabo-stuban'
        ]
        
        print(f"\nChecking for LumberjackAI indicators (not in config):")
        for indicator in lumberjack_indicators:
            if indicator.lower() in text_content.lower():
                print(f"  ✓ Found: '{indicator}'")
            else:
                print(f"  ✗ Missing: '{indicator}'")

if __name__ == "__main__":
    main()