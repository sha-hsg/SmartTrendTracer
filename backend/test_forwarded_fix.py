#!/usr/bin/env python3
"""Test the forwarded email content fix"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.collectors.gmail_substack_collector import GmailSubstackCollector
from app.models import SessionLocal, SubstackArticle

def main():
    collector = GmailSubstackCollector()
    collector.authenticate()
    
    # Test with the empty Gary Marcus article
    gmail_id = "1988ff69687b0fa3"  # GPT-5 hot take
    
    print(f"🧪 Testing forwarded content extraction...")
    print(f"Gmail ID: {gmail_id}")
    
    # Get the email and process it
    email_data = collector.get_email_content(gmail_id)
    
    if email_data:
        print(f"\n📧 Email data:")
        print(f"Subject: {email_data['subject']}")
        print(f"Author: {email_data['author']['name']}")
        
        # Debug the HTML content
        html_body = email_data.get('html_body', '')
        print(f"\n🔍 HTML Analysis:")
        print(f"Contains 'ms-outlook-mobile-reference-message': {'ms-outlook-mobile-reference-message' in html_body}")
        print(f"Contains 'From:' and 'Date:' and '@substack.com': {'From:' in html_body and 'Date:' in html_body and '@substack.com' in html_body}")
        
        # Manually test the parsing
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_body, 'html.parser')
        content_container = soup.find('div', class_='ms-outlook-mobile-reference-message')
        print(f"Found content container: {content_container is not None}")
        
        if content_container:
            paras = content_container.find_all(['p', 'h1', 'h2', 'h3', 'div'])
            print(f"Found {len(paras)} paragraph elements")
            
            # Show first few paragraphs
            for i, para in enumerate(paras[:5]):
                text = para.get_text(strip=True)
                print(f"  Para {i}: {text[:100]}...")
        
        article_info = email_data.get('article', {})
        print(f"\n📄 Article extraction:")
        print(f"Title: {article_info.get('title')}")
        print(f"Word count: {article_info.get('word_count')}")
        print(f"Content preview: {article_info.get('preview', '')[:200]}...")
        
        if article_info.get('word_count', 0) > 0:
            print("\n✅ SUCCESS: Content extracted from forwarded email!")
        else:
            print("\n❌ FAILED: Still no content extracted")
    else:
        print("❌ Failed to fetch email")

if __name__ == "__main__":
    main()