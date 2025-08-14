#!/usr/bin/env python3
"""Debug the fix process step by step"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.collectors.gmail_substack_collector import GmailSubstackCollector

def main():
    collector = GmailSubstackCollector()
    collector.authenticate()
    
    # Test with the known working email ID
    gmail_id = "1988ff69687b0fa3"
    
    print("🔍 DEBUGGING FIX PROCESS")
    print("=" * 60)
    
    # Get email content step by step
    print("1. Fetching raw email...")
    message = collector.service.users().messages().get(
        userId='me',
        id=gmail_id,
        format='full'
    ).execute()
    
    if not message:
        print("❌ Failed to fetch message")
        return
    
    print("✓ Message fetched")
    
    # Extract HTML body
    print("\n2. Extracting HTML body...")
    html_body = collector._extract_html_body(message['payload'])
    print(f"✓ HTML body extracted: {len(html_body)} chars")
    
    # Parse author info
    print("\n3. Parsing author info...")
    headers = message['payload'].get('headers', [])
    header_dict = {h['name']: h['value'] for h in headers}
    sender = header_dict.get('From', '')
    print(f"Sender: {sender}")
    
    author_info = collector._parse_author_from_sender(sender, html_body)
    print(f"Author: {author_info}")
    
    # Clean forwarded content
    print("\n4. Cleaning forwarded content...")
    cleaned_html = collector._clean_forwarded_content(html_body)
    print(f"✓ Cleaned HTML: {len(cleaned_html)} chars")
    
    # Parse Substack HTML
    print("\n5. Parsing Substack HTML...")
    article_info = collector._parse_substack_html(cleaned_html)
    print(f"Article info:")
    print(f"  Title: {article_info.get('title')}")
    print(f"  Word count: {article_info.get('word_count')}")
    print(f"  Content length: {len(article_info.get('content_markdown', ''))}")
    
    # Show the full process with get_email_content
    print("\n6. Full get_email_content process...")
    email_data = collector.get_email_content(gmail_id)
    if email_data:
        article_data = email_data.get('article', {})
        print(f"Full process result:")
        print(f"  Title: {article_data.get('title')}")
        print(f"  Word count: {article_data.get('word_count')}")
        print(f"  Content length: {len(article_data.get('content_markdown', ''))}")

if __name__ == "__main__":
    main()