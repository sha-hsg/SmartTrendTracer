#!/usr/bin/env python3
"""
Check for Nathan Lambert emails in Gmail
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.gmail_client import GmailClient

def main():
    print("Checking for Nathan Lambert emails...")
    
    gmail = GmailClient()
    
    # Search for emails from Nathan Lambert
    queries = [
        'from:nathan@interconnects.ai',
        'from:noreply@substack.com subject:"Nathan Lambert"',
        'from:substack.com "Nathan Lambert"',
        'from:interconnects.ai',
        '"Interconnects" from:substack.com'
    ]
    
    for query in queries:
        print(f"\nSearching: {query}")
        try:
            results = gmail.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=5
            ).execute()
            
            messages = results.get('messages', [])
            print(f"  Found {len(messages)} messages")
            
            if messages:
                # Get details of first message
                msg = gmail.service.users().messages().get(
                    userId='me',
                    id=messages[0]['id']
                ).execute()
                
                # Extract headers
                headers = msg['payload'].get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No subject')
                from_addr = next((h['value'] for h in headers if h['name'] == 'From'), 'No from')
                date = next((h['value'] for h in headers if h['name'] == 'Date'), 'No date')
                
                print(f"  Latest email:")
                print(f"    From: {from_addr}")
                print(f"    Subject: {subject}")
                print(f"    Date: {date}")
                
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    main()