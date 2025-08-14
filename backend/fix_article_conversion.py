#!/usr/bin/env python3
"""
Fix HTML to Markdown conversion for existing Substack articles
Tests the improved converter and re-processes articles if needed
"""
import sys
import os
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.models.substack import SubstackArticle, SubstackAuthor
from app.services.document_converter import DocumentConverter
from app.collectors.gmail_substack_collector import remove_substack_footer

# Database setup
DATABASE_URL = "sqlite:///data/tweets.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_conversion(limit=5):
    """Test the improved HTML to Markdown conversion"""
    db = SessionLocal()
    converter = DocumentConverter()
    
    try:
        # Get recent articles from Sebastian Raschka
        author = db.query(SubstackAuthor).filter(
            SubstackAuthor.name == "Sebastian Raschka"
        ).first()
        
        if not author:
            print("❌ Sebastian Raschka not found in database")
            return
        
        articles = db.query(SubstackArticle).filter(
            SubstackArticle.author_id == author.id
        ).order_by(
            SubstackArticle.published_at.desc()
        ).limit(limit).all()
        
        print(f"\n📚 Testing conversion on {len(articles)} articles from {author.name}\n")
        
        for i, article in enumerate(articles, 1):
            print(f"\n{i}. {article.title}")
            print(f"   Original markdown length: {len(article.content_markdown)}")
            print(f"   Word count: {article.word_count}")
            
            # Re-convert HTML to Markdown
            if article.content_html:
                new_markdown = converter.html_to_markdown(
                    article.content_html,
                    preserve_images=True
                )
                
                # Clean footer
                new_markdown = remove_substack_footer(new_markdown)
                
                # Calculate new stats
                new_word_count = len(new_markdown.split())
                
                print(f"   ✨ New markdown length: {len(new_markdown)}")
                print(f"   ✨ New word count: {new_word_count}")
                
                # Check if content improved
                if new_word_count > article.word_count * 1.5:  # 50% more content
                    print(f"   ✅ Significant improvement! ({new_word_count / max(article.word_count, 1):.1f}x more content)")
                    
                    # Show preview of new content
                    preview = new_markdown[:500] if len(new_markdown) > 500 else new_markdown
                    print(f"\n   Preview of improved content:")
                    print("   " + "-" * 60)
                    for line in preview.split('\n')[:10]:
                        if line.strip():
                            print(f"   {line[:80]}")
                    print("   " + "-" * 60)
                    
                elif new_word_count > article.word_count:
                    print(f"   ✓ Some improvement ({new_word_count - article.word_count} more words)")
                else:
                    print(f"   ⚠️  No improvement")
            else:
                print(f"   ❌ No HTML content available")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing conversion: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def fix_all_articles(author_name=None, dry_run=True):
    """Re-process all articles with the improved converter"""
    db = SessionLocal()
    converter = DocumentConverter()
    
    try:
        # Get articles to fix
        query = db.query(SubstackArticle)
        
        if author_name:
            author = db.query(SubstackAuthor).filter(
                SubstackAuthor.name == author_name
            ).first()
            if author:
                query = query.filter(SubstackArticle.author_id == author.id)
        
        articles = query.all()
        
        print(f"\n🔧 Processing {len(articles)} articles (dry_run={dry_run})\n")
        
        improved_count = 0
        failed_count = 0
        
        for article in articles:
            try:
                if not article.content_html:
                    continue
                
                # Re-convert HTML to Markdown
                new_markdown = converter.html_to_markdown(
                    article.content_html,
                    preserve_images=True
                )
                
                # Clean footer
                new_markdown = remove_substack_footer(new_markdown)
                
                # Calculate new stats
                new_word_count = len(new_markdown.split())
                new_preview = new_markdown[:500] if len(new_markdown) > 500 else new_markdown
                
                # Check if content improved significantly
                if new_word_count > article.word_count * 1.2:  # 20% more content
                    improved_count += 1
                    
                    if not dry_run:
                        # Update article
                        article.content_markdown = new_markdown
                        article.word_count = new_word_count
                        article.preview = new_preview
                        article.reading_time_minutes = max(1, new_word_count // 200)
                        
                    print(f"✅ {article.title[:50]}... ({article.word_count} → {new_word_count} words)")
                    
            except Exception as e:
                failed_count += 1
                print(f"❌ Failed: {article.title[:50]}... - {e}")
        
        if not dry_run:
            db.commit()
            print(f"\n✅ Updated {improved_count} articles")
        else:
            print(f"\n🔍 Would update {improved_count} articles (run with --fix to apply)")
        
        if failed_count > 0:
            print(f"⚠️  {failed_count} articles failed to process")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing articles: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Fix HTML to Markdown conversion for Substack articles')
    parser.add_argument('--test', action='store_true', help='Test conversion on sample articles')
    parser.add_argument('--fix', action='store_true', help='Re-process all articles')
    parser.add_argument('--author', type=str, help='Filter by author name')
    parser.add_argument('--limit', type=int, default=5, help='Number of articles to test')
    
    args = parser.parse_args()
    
    if args.test or (not args.test and not args.fix):
        # Default to test mode
        print("🧪 Testing improved HTML to Markdown conversion...")
        test_conversion(limit=args.limit)
    
    if args.fix:
        print("\n🔧 Fixing article conversions...")
        fix_all_articles(author_name=args.author, dry_run=False)
    elif not args.test:
        print("\n💡 Tip: Run with --fix to apply the improvements to all articles")

if __name__ == "__main__":
    main()