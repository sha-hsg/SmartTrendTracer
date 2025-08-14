#!/usr/bin/env python3
"""Test the improved image positioning for forwarded emails"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.collectors.gmail_substack_collector import GmailSubstackCollector

def main():
    collector = GmailSubstackCollector()
    collector.authenticate()
    
    # Test with Nathan Lambert's article
    gmail_id = "1988ffa6df74323b"  # GPT-5 and the arc of progress
    
    print("🧪 TESTING IMPROVED IMAGE POSITIONING")
    print("=" * 60)
    print(f"Gmail ID: {gmail_id}")
    print(f"Expected: Images distributed throughout the article")
    
    # Test the improved extraction
    email_data = collector.get_email_content(gmail_id)
    
    if email_data:
        article_info = email_data.get('article', {})
        content = article_info.get('content_markdown', '')
        
        print(f"\nExtraction results:")
        print(f"Title: {article_info.get('title')}")
        print(f"Word count: {article_info.get('word_count')}")
        print(f"Image count: {content.count('![')}")
        
        if content:
            # Analyze image positioning
            lines = content.split('\n')
            total_lines = len(lines)
            
            image_positions = []
            for i, line in enumerate(lines):
                if line.strip().startswith('!['):
                    image_positions.append(i)
            
            if image_positions:
                first_image_line = image_positions[0]
                last_image_line = image_positions[-1]
                
                first_image_percent = (first_image_line / total_lines) * 100
                last_image_percent = (last_image_line / total_lines) * 100
                
                print(f"\n📊 Image positioning analysis:")
                print(f"First image at line {first_image_line}/{total_lines} ({first_image_percent:.1f}%)")
                print(f"Last image at line {last_image_line}/{total_lines} ({last_image_percent:.1f}%)")
                print(f"Images span {(last_image_percent - first_image_percent):.1f}% of article")
                
                # Check if positioning improved
                if first_image_percent < 50:  # Images start in first half
                    print("✅ IMPROVED: Images now start early in the article!")
                elif first_image_percent < 80:  # Better than before but not perfect
                    print("🔄 PARTIAL IMPROVEMENT: Images start earlier than before")
                else:
                    print("❌ STILL ISSUE: Images still clustered at end")
                
                # Show first few lines with context
                print(f"\n🔍 First image context:")
                for i in range(max(0, first_image_line-2), min(total_lines, first_image_line+3)):
                    marker = ">>>>" if i == first_image_line else "    "
                    line_preview = lines[i][:80] + "..." if len(lines[i]) > 80 else lines[i]
                    print(f"{marker} {line_preview}")
            else:
                print("❌ No images found")
        else:
            print("❌ No content extracted")
    else:
        print("❌ Failed to extract email data")

if __name__ == "__main__":
    main()