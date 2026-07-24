#!/usr/bin/env python3
"""Fix empty forwarded articles by re-extracting content"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.collectors.gmail_substack_collector import GmailSubstackCollector
from app.models import SessionLocal, SubstackArticle

def main():
    collector = GmailSubstackCollector()
    collector.authenticate()
    
    db = SessionLocal()
    
    print("🔧 Fixing forwarded articles with empty content...")
    
    # Find articles from Gary Marcus and Sebastian Raschka with 0 word count
    from app.models.substack import SubstackAuthor
    empty_articles = db.query(SubstackArticle).join(
        SubstackAuthor
    ).filter(
        SubstackArticle.word_count == 0,
        SubstackAuthor.name.in_(['Gary Marcus', 'Sebastian Raschka'])
    ).all()
    
    if not empty_articles:
        # Try a broader search for empty forwarded articles
        empty_articles = db.query(SubstackArticle).filter(
            SubstackArticle.word_count == 0,
            SubstackArticle.substack_id.like('gmail_%')
        ).all()
    
    print(f"Found {len(empty_articles)} empty articles to fix:")
    for article in empty_articles:
        print(f"  - {article.title} ({article.author.name if article.author else 'Unknown'})")
    
    # Fix each article
    fixed_count = 0
    for article in empty_articles:
        if not article.substack_id or not article.substack_id.startswith('gmail_'):
            print(f"  ⚠️  Skipping {article.title} - not a Gmail article")
            continue
        
        gmail_id = article.substack_id.replace('gmail_', '')
        
        print(f"\n🔧 Fixing: {article.title}")
        print(f"  Gmail ID: {gmail_id}")
        
        # Re-extract content from email
        email_data = collector.get_email_content(gmail_id)
        if not email_data:
            print(f"  ❌ Failed to fetch email")
            continue
        
        article_info = email_data.get('article', {})
        if not article_info or article_info.get('word_count', 0) == 0:
            print(f"  ❌ Still no content extracted")
            continue
        
        # Update the article
        article.content_html = article_info.get('content_html')
        article.content_markdown = article_info.get('content_markdown')
        article.preview = article_info.get('preview')
        article.word_count = article_info.get('word_count', 0)
        article.reading_time_minutes = article_info.get('reading_time_minutes', 1)
        
        # Update title if it was generic
        if article.title in ['Untitled', 'Forwarded Newsletter'] and article_info.get('title'):
            article.title = article_info.get('title')
        
        # Also update from email subject if still generic
        if article.title in ['Untitled', 'Forwarded Newsletter']:
            subject = email_data.get('subject', '')
            # Remove forward prefixes
            for prefix in ['FW: ', 'Fwd: ', 'Re: ', 'RE: ']:
                if subject.startswith(prefix):
                    subject = subject[len(prefix):]
            if subject:
                article.title = subject
        
        db.commit()
        fixed_count += 1
        
        print(f"  ✅ Fixed! Now {article.word_count} words")
        print(f"     Title: {article.title}")
        print(f"     Preview: {article.preview[:100]}...")
    
    db.close()
    
    print(f"\n✅ Fixed {fixed_count} articles!")

if __name__ == "__main__":
    main()