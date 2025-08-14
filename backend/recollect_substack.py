#!/usr/bin/env python3
"""
Re-collect Substack articles to fix content extraction
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.collectors.gmail_substack_collector import GmailSubstackCollector
from app.models import SessionLocal, SubstackArticle

def main():
    print("🔄 Re-collecting Substack articles with improved extraction...")
    
    # First, clear existing articles with fragments
    db = SessionLocal()
    try:
        # Check current articles
        articles = db.query(SubstackArticle).all()
        print(f"Found {len(articles)} existing articles")
        
        # Delete articles that are fragments (very short content)
        fragment_count = 0
        for article in articles:
            if article.content_markdown:
                # Check if it's a fragment (contains forwarding metadata)
                if 'From:**' in article.content_markdown or \
                   'Date:**' in article.content_markdown or \
                   len(article.content_markdown) < 1000:
                    print(f"  Removing fragment: {article.title[:50]}...")
                    db.delete(article)
                    fragment_count += 1
        
        if fragment_count > 0:
            db.commit()
            print(f"✅ Removed {fragment_count} fragment articles")
        
        # Now re-collect
        print("\n📥 Collecting articles from Gmail...")
        collector = GmailSubstackCollector()
        
        # Build query for recent Substack emails
        query = 'subject:(substack OR interconnects OR "marcus on ai") newer_than:30d'
        
        # Collect articles
        article_count = collector.collect_newsletters(query=query, max_results=50)
        
        print(f"\n✅ Processed {article_count} emails")
        
        # Get newly collected articles
        new_articles = db.query(SubstackArticle).order_by(SubstackArticle.collected_at.desc()).limit(5).all()
        
        # Show sample of collected content
        if new_articles:
            for i, sample in enumerate(new_articles[:2], 1):
                print(f"\n📄 Sample {i}: {sample.title[:60]}...")
                print(f"   Author: {sample.author.name if sample.author else 'Unknown'}")
                print(f"   Word count: {sample.word_count}")
                if sample.content_markdown:
                    # Skip any remaining forward headers
                    content = sample.content_markdown
                    if 'From:**' in content:
                        # Try to find actual content after headers
                        lines = content.split('\n')
                        for idx, line in enumerate(lines):
                            if line and not any(x in line for x in ['From:', 'Date:', 'To:', 'Subject:', '|', '---']):
                                content = '\n'.join(lines[idx:])
                                break
                    preview = content[:200].replace('\n', ' ').strip()
                    print(f"   Preview: {preview}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()