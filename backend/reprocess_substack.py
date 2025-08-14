#!/usr/bin/env python3
"""
Reprocess existing Substack articles to extract content properly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.collectors.gmail_substack_collector import GmailSubstackCollector
from app.models import SessionLocal, SubstackArticle
from bs4 import BeautifulSoup

def reprocess_article(article, collector):
    """Reprocess a single article's HTML to extract content"""
    if not article.content_html:
        return False
    
    # Use the collector's parsing method
    article_info = collector._parse_substack_html(article.content_html)
    
    if article_info and article_info.get('content_markdown'):
        # Update the article with new content
        article.content_markdown = article_info['content_markdown']
        article.preview = article_info.get('preview', '')
        article.word_count = article_info.get('word_count', 0)
        article.reading_time_minutes = article_info.get('reading_time_minutes', 1)
        
        # Update title if we found a better one
        if article_info.get('title') and article_info['title'] != 'Untitled':
            article.title = article_info['title']
        
        return True
    return False

def main():
    print("🔄 Reprocessing existing Substack articles...")
    
    db = SessionLocal()
    collector = GmailSubstackCollector()
    
    try:
        # Get all articles
        articles = db.query(SubstackArticle).all()
        print(f"Found {len(articles)} articles to reprocess")
        
        success_count = 0
        for i, article in enumerate(articles, 1):
            print(f"\n📄 Processing {i}/{len(articles)}: {article.title[:50]}...")
            
            if reprocess_article(article, collector):
                success_count += 1
                print(f"   ✅ Extracted {article.word_count} words")
                
                # Show preview
                if article.content_markdown:
                    preview = article.content_markdown[:200].replace('\n', ' ').strip()
                    # Skip tracking pixels in preview
                    if not preview.startswith('![]('):
                        print(f"   Preview: {preview[:150]}...")
            else:
                print(f"   ⚠️ No content extracted")
        
        # Commit all changes
        db.commit()
        print(f"\n✅ Successfully reprocessed {success_count}/{len(articles)} articles")
        
        # Show some statistics
        print("\n📊 Statistics:")
        good_articles = db.query(SubstackArticle).filter(SubstackArticle.word_count > 100).count()
        print(f"   Articles with content (>100 words): {good_articles}")
        
        from sqlalchemy import func
        avg_words = db.query(func.avg(SubstackArticle.word_count)).filter(
            SubstackArticle.word_count > 100
        ).scalar()
        if avg_words:
            print(f"   Average word count: {int(avg_words)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()