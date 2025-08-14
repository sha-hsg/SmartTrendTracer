#!/usr/bin/env python3
"""Direct test of the _parse_substack_html method"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.collectors.gmail_substack_collector import GmailSubstackCollector

def main():
    collector = GmailSubstackCollector()
    collector.authenticate()
    
    # Get the email content
    gmail_id = "1988ff69687b0fa3"
    email_data = collector.get_email_content(gmail_id)
    
    if email_data:
        html_body = email_data.get('html_body', '')
        
        print("🧪 TESTING _parse_substack_html DIRECTLY")
        print("=" * 60)
        
        # Test the method directly
        result = collector._parse_substack_html(html_body)
        
        print(f"Title: {result.get('title', 'N/A')}")
        print(f"Word count: {result.get('word_count', 0)}")
        print(f"Content length: {len(result.get('content_markdown', ''))}")
        print(f"Preview: {result.get('preview', 'N/A')[:200]}...")

if __name__ == "__main__":
    main()