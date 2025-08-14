#!/usr/bin/env python3
"""Debug the cleaning process"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.collectors.gmail_substack_collector import GmailSubstackCollector

def main():
    collector = GmailSubstackCollector()
    collector.authenticate()
    
    gmail_id = "1988ff69687b0fa3"
    
    print("🔍 DEBUGGING CLEANING PROCESS")
    print("=" * 60)
    
    # Get original HTML
    message = collector.service.users().messages().get(
        userId='me',
        id=gmail_id,
        format='full'
    ).execute()
    
    html_body = collector._extract_html_body(message['payload'])
    print(f"Original HTML: {len(html_body)} chars")
    
    # Apply cleaning step by step
    from bs4 import BeautifulSoup
    import re
    
    print("\nCleaning step by step...")
    
    soup = BeautifulSoup(html_body, 'html.parser')
    print(f"After BeautifulSoup: {len(str(soup))} chars")
    
    # Step 1: Remove forwarding tables
    print("\n1. Removing forwarding tables...")
    tables_removed = 0
    for table in soup.find_all('table'):
        table_text = table.get_text(strip=True)[:500]
        if all(indicator in table_text for indicator in ['From:', 'Date:', 'To:', 'Subject:']):
            print(f"   Removing table with text: {table_text[:100]}...")
            table.decompose()
            tables_removed += 1
    print(f"   Removed {tables_removed} forwarding tables")
    print(f"   HTML after table removal: {len(str(soup))} chars")
    
    # Step 2: Remove forwarding divs
    print("\n2. Removing forwarding divs...")
    divs_removed = 0
    for div in soup.find_all('div'):
        div_text = div.get_text(strip=True)[:300]
        if 'From:' in div_text and 'Date:' in div_text and 'Subject:' in div_text:
            if len(div_text) < 500:
                print(f"   Removing div with text: {div_text[:100]}...")
                div.decompose()
                divs_removed += 1
    print(f"   Removed {divs_removed} forwarding divs")
    print(f"   HTML after div removal: {len(str(soup))} chars")
    
    # Step 3: Pattern removal
    print("\n3. Applying regex patterns...")
    html_str = str(soup)
    original_len = len(html_str)
    
    patterns_to_remove = [
        r'<table[^>]*>.*?From:.*?Date:.*?Subject:.*?</table>',
        r'Handschuh, Siegfried.*?to me',
        r'---------- Forwarded message ---------.*?Subject:.*?\n',
        r'Begin forwarded message:.*?Subject:.*?\n',
    ]
    
    for i, pattern in enumerate(patterns_to_remove):
        before_len = len(html_str)
        html_str = re.sub(pattern, '', html_str, flags=re.MULTILINE | re.DOTALL | re.IGNORECASE)
        after_len = len(html_str)
        print(f"   Pattern {i+1}: Removed {before_len - after_len} chars")
    
    print(f"   Final HTML: {len(html_str)} chars")
    
    # Show what's left
    print(f"\nFinal cleaned HTML (first 1000 chars):")
    print(html_str[:1000])
    
    print(f"\nFinal cleaned HTML (last 1000 chars):")
    print(html_str[-1000:])

if __name__ == "__main__":
    main()