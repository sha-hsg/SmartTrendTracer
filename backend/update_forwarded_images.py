#!/usr/bin/env python3
"""Update forwarded articles to include images"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.collectors.gmail_substack_collector import GmailSubstackCollector
from app.models import SessionLocal, SubstackArticle, SubstackAuthor

def main():
    collector = GmailSubstackCollector()
    collector.authenticate()
    
    db = SessionLocal()
    
    print("🖼️  Updating forwarded articles to include images...")
    
    # Find forwarded articles (from Gmail IDs)
    forwarded_articles = db.query(SubstackArticle).filter(
        SubstackArticle.substack_id.like('gmail_%')
    ).join(SubstackAuthor).filter(
        SubstackAuthor.email.in_(['robotic@substack.com', 'garymarcus@substack.com', 'sebastianraschka@substack.com'])
    ).all()
    
    print(f"Found {len(forwarded_articles)} forwarded articles to update:")
    for article in forwarded_articles:
        current_image_count = article.content_markdown.count('![') if article.content_markdown else 0
        print(f"  - {article.title[:50]}... (currently {current_image_count} images)")
    
    # Update each article
    updated_count = 0
    for article in forwarded_articles:
        gmail_id = article.substack_id.replace('gmail_', '')
        
        print(f"\n🔄 Updating: {article.title}")
        print(f"   Gmail ID: {gmail_id}")
        print(f"   Current images: {article.content_markdown.count('![') if article.content_markdown else 0}")
        
        # Re-extract content with images
        email_data = collector.get_email_content(gmail_id)
        if not email_data:
            print(f"   ❌ Failed to fetch email")
            continue
        
        article_info = email_data.get('article', {})
        if not article_info:
            print(f"   ❌ No article info extracted")
            continue
        
        new_image_count = article_info.get('content_markdown', '').count('![')
        new_word_count = article_info.get('word_count', 0)
        
        print(f"   New extraction: {new_word_count} words, {new_image_count} images")
        
        if new_image_count > 0 or new_word_count != article.word_count:
            # Update the article
            article.content_html = article_info.get('content_html')
            article.content_markdown = article_info.get('content_markdown')
            article.preview = article_info.get('preview')
            article.word_count = new_word_count
            article.reading_time_minutes = article_info.get('reading_time_minutes', 1)
            
            # Update title if it was generic and we have a better one
            if article.title in ['Untitled', 'Forwarded Newsletter'] and article_info.get('title'):
                article.title = article_info.get('title')
            
            db.commit()
            updated_count += 1
            
            print(f"   ✅ Updated! Now {new_word_count} words and {new_image_count} images")
            if new_image_count > 0:
                # Show first image as sample
                lines = article.content_markdown.split('\n')
                for line in lines:
                    if line.strip().startswith('!['):
                        print(f"      Sample image: {line.strip()[:80]}...")
                        break
        else:
            print(f"   ⚪ No changes needed")
    
    db.close()
    
    print(f"\n✅ Updated {updated_count} articles with improved content and images!")

if __name__ == "__main__":
    main()