#!/usr/bin/env python3
"""Debug what emails are being found by the search query"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.collectors.gmail_substack_collector import GmailSubstackCollector

def main():
    collector = GmailSubstackCollector()
    collector.authenticate()
    
    # Test the --forwarded query
    query = '(from:siegfried.handschuh@unisg.ch AND substack) OR (from:me to:me AND substack) OR "robotic@substack.com" OR "garymarcus@substack.com" OR "sebastianraschka@substack.com"'
    
    print("🔍 TESTING FORWARDED QUERY:")
    print(f"Query: {query}")
    print("=" * 80)
    
    message_ids = collector.search_substack_emails(query, 20)
    print(f"Found {len(message_ids)} emails")
    
    for i, msg_id in enumerate(message_ids[:10], 1):  # Check first 10
        print(f"\n📧 Email {i}: {msg_id}")
        
        # Get email metadata
        try:
            message = collector.service.users().messages().get(
                userId='me',
                id=msg_id,
                format='full'
            ).execute()
            
            headers = message['payload'].get('headers', [])
            header_dict = {h['name']: h['value'] for h in headers}
            
            subject = header_dict.get('Subject', '')
            sender = header_dict.get('From', '')
            
            print(f"  Subject: {subject}")
            print(f"  From: {sender}")
            
            # Parse author info
            html_body = collector._extract_html_body(message['payload'])
            author_info = collector._parse_author_from_sender(sender, html_body)
            print(f"  Parsed Author: {author_info['name']} ({author_info['email']})")
            
            # Check if this should be collected
            expected_emails = ['robotic@substack.com', 'garymarcus@substack.com', 'sebastianraschka@substack.com', 'emollick@substack.com']
            should_collect = author_info['email'] in expected_emails
            print(f"  Should collect: {should_collect}")
            if not should_collect:
                print(f"  ❌ PROBLEM: This email shouldn't be collected!")
            
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    main()