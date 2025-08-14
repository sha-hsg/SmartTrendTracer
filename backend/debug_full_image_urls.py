#!/usr/bin/env python3
"""Debug full image URLs in forwarded emails"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.collectors.gmail_substack_collector import GmailSubstackCollector
from bs4 import BeautifulSoup

def main():
    collector = GmailSubstackCollector()
    collector.authenticate()
    
    # Test with Gary Marcus's GPT-5 hot take
    gmail_id = "1988ff69687b0fa3"
    
    print("🔍 FULL IMAGE URL ANALYSIS")
    print("=" * 80)
    
    # Get email content
    email_data = collector.get_email_content(gmail_id)
    if not email_data:
        print("❌ Failed to fetch email")
        return
    
    html_body = email_data.get('html_body', '')
    soup = BeautifulSoup(html_body, 'html.parser')
    
    # Find only the content images that should be kept
    content_images = []
    
    # Check table.image-wrapper images
    for table in soup.find_all('table', class_='image-wrapper'):
        img = table.find('img')
        if img:
            src = img.get('src', '')
            print(f"\n📸 TABLE IMAGE:")
            print(f"Full URL: {src}")
            print(f"Contains 'substack-post-media': {'substack-post-media' in src}")
            print(f"Contains 'substackcdn.com/image/fetch': {'substackcdn.com/image/fetch' in src}")
            
            if len(src) > 100:
                # Try to decode the URL if it's encoded
                import urllib.parse
                try:
                    # Look for URL-encoded content in the fetch URL
                    if 'https%3A%2F%2F' in src:
                        # Find the encoded URL part
                        encoded_start = src.find('https%3A%2F%2F')
                        encoded_part = src[encoded_start:].split('/')[0] + '/' + src[encoded_start:].split('/')[1] + '/' + src[encoded_start:].split('/')[2]
                        decoded_url = urllib.parse.unquote(encoded_part)
                        print(f"Decoded part: {decoded_url}")
                        print(f"Decoded contains 'substack-post-media': {'substack-post-media' in decoded_url}")
                except:
                    pass
            
            content_images.append(('table', img, src))
    
    # Check standalone images
    for img in soup.find_all('img'):
        # Skip if it's already in a table.image-wrapper (we handled those above)
        if img.find_parent('table', class_='image-wrapper'):
            continue
            
        src = img.get('src', '')
        if 'substackcdn.com/image/fetch' in src:
            print(f"\n📸 STANDALONE IMAGE:")
            print(f"Full URL: {src}")
            print(f"Contains 'substack-post-media': {'substack-post-media' in src}")
            
            if len(src) > 100:
                import urllib.parse
                try:
                    if 'https%3A%2F%2F' in src:
                        encoded_start = src.find('https%3A%2F%2F')
                        encoded_part = src[encoded_start:].split('/')[0] + '/' + src[encoded_start:].split('/')[1] + '/' + src[encoded_start:].split('/')[2]
                        decoded_url = urllib.parse.unquote(encoded_part)
                        print(f"Decoded part: {decoded_url}")
                        print(f"Decoded contains 'substack-post-media': {'substack-post-media' in decoded_url}")
                except:
                    pass
            
            content_images.append(('standalone', img, src))
    
    print(f"\n📊 SUMMARY:")
    print(f"Found {len(content_images)} potential content images")
    
    # Test the current logic
    print(f"\n🧪 TESTING CURRENT EXTRACTION LOGIC:")
    for img_type, img, src in content_images:
        print(f"\n{img_type.upper()} IMAGE:")
        print(f"  URL: {src[:60]}...")
        
        if img_type == 'table':
            # Table logic: if 'substack-post-media' in src
            should_keep_table = 'substack-post-media' in src
            print(f"  Table logic result: {should_keep_table}")
        else:
            # Standalone logic: if ('substackcdn.com/image/fetch' in src and 'substack-post-media' in src)
            should_keep_standalone = ('substackcdn.com/image/fetch' in src and 'substack-post-media' in src)
            print(f"  Standalone logic result: {should_keep_standalone}")
        
        # Try alternative detection
        import urllib.parse
        decoded_contains_media = False
        if 'https%3A%2F%2F' in src:
            try:
                decoded_url = urllib.parse.unquote(src)
                decoded_contains_media = 'substack-post-media' in decoded_url
                print(f"  Alternative (decoded) logic: {decoded_contains_media}")
            except:
                pass

if __name__ == "__main__":
    main()