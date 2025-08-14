#!/usr/bin/env python3
"""Debug images in forwarded emails"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.collectors.gmail_substack_collector import GmailSubstackCollector
from bs4 import BeautifulSoup

def main():
    collector = GmailSubstackCollector()
    collector.authenticate()
    
    # Test with Gary Marcus's GPT-5 hot take (known to have images)
    gmail_id = "1988ff69687b0fa3"
    
    print("🖼️  DEBUGGING IMAGES IN FORWARDED EMAIL")
    print("=" * 60)
    
    # Get email content
    email_data = collector.get_email_content(gmail_id)
    if not email_data:
        print("❌ Failed to fetch email")
        return
    
    html_body = email_data.get('html_body', '')
    soup = BeautifulSoup(html_body, 'html.parser')
    
    # Find all images
    all_images = soup.find_all('img')
    print(f"Found {len(all_images)} total images:")
    
    for i, img in enumerate(all_images, 1):
        src = img.get('src', '')
        alt = img.get('alt', '')
        width = img.get('width', '')
        height = img.get('height', '')
        
        print(f"\n📸 Image {i}:")
        print(f"  src: {src[:100]}..." if len(src) > 100 else f"  src: {src}")
        print(f"  alt: {alt}")
        print(f"  size: {width}x{height}")
        
        # Check if this is a content image vs tracking pixel
        is_tracking = (
            (width == '1' and height == '1') or
            'open?token=' in src or
            '/track' in src or
            'pixel' in src.lower()
        )
        
        is_substack_content = (
            'substack-post-media' in src or
            ('substackcdn.com/image/fetch' in src and 'substack-post-media' in src)
        )
        
        print(f"  is_tracking: {is_tracking}")
        print(f"  is_substack_content: {is_substack_content}")
        print(f"  should_keep: {is_substack_content and not is_tracking}")
        
        # Check parent elements
        parent = img.parent
        if parent:
            print(f"  parent: <{parent.name} class='{parent.get('class', [])}'>")
            
            # Check if it's in a table wrapper
            table_parent = img.find_parent('table', class_='image-wrapper')
            if table_parent:
                print(f"  in image-wrapper table: Yes")
            else:
                print(f"  in image-wrapper table: No")
    
    # Test image extraction specifically
    print(f"\n🧪 TESTING IMAGE EXTRACTION:")
    
    # Test current forwarded parsing
    print("\n1. Current forwarded email parsing:")
    article_info = collector._parse_substack_html(html_body)
    content_markdown = article_info.get('content_markdown', '')
    
    image_count = content_markdown.count('![')
    print(f"  Found {image_count} images in markdown")
    
    if image_count > 0:
        # Show image markdown
        lines = content_markdown.split('\n')
        for line in lines:
            if line.strip().startswith('!['):
                print(f"  Image: {line.strip()}")
    else:
        print(f"  ❌ No images found in extracted content")

if __name__ == "__main__":
    main()