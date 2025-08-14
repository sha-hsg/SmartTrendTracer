#!/usr/bin/env python3
"""
Test the forwarded email cleaning on existing articles
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.substack import SubstackArticle, SubstackAuthor
from app.services.document_converter import DocumentConverter
from app.services.forwarded_email_cleaner import ForwardedEmailCleaner
from app.collectors.gmail_substack_collector import remove_substack_footer

# Database setup
DATABASE_URL = "sqlite:///data/tweets.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_cleaning():
    """Test the forwarded email cleaning"""
    db = SessionLocal()
    converter = DocumentConverter()
    cleaner = ForwardedEmailCleaner()
    
    try:
        # Get a Sebastian Raschka article (these are forwarded)
        author = db.query(SubstackAuthor).filter(
            SubstackAuthor.name == "Sebastian Raschka"
        ).first()
        
        if not author:
            print("❌ Sebastian Raschka not found")
            return
        
        article = db.query(SubstackArticle).filter(
            SubstackArticle.author_id == author.id
        ).order_by(
            SubstackArticle.published_at.desc()
        ).first()
        
        if not article:
            print("❌ No articles found")
            return
        
        print(f"\n📚 Testing cleaning on: {article.title}")
        print(f"   Original markdown length: {len(article.content_markdown)}")
        print(f"   Original word count: {article.word_count}")
        
        if article.content_html:
            # Step 1: Clean HTML
            cleaned_html = cleaner.clean_html(article.content_html)
            
            # Step 2: Convert to markdown
            new_markdown = converter.html_to_markdown(cleaned_html, preserve_images=True)
            
            # Step 3: Clean markdown artifacts
            new_markdown = cleaner.clean_markdown(new_markdown)
            
            # Step 4: Remove Substack footer
            new_markdown = remove_substack_footer(new_markdown)
            
            # Calculate stats
            new_word_count = len(new_markdown.split())
            
            print(f"\n   ✨ Cleaned markdown length: {len(new_markdown)}")
            print(f"   ✨ Cleaned word count: {new_word_count}")
            
            if new_word_count > article.word_count:
                improvement = new_word_count / max(article.word_count, 1)
                print(f"   ✅ Improvement: {improvement:.1f}x more content")
            else:
                print(f"   ⚠️  No improvement")
            
            # Show preview
            print(f"\n   Preview of cleaned content:")
            print("   " + "-" * 60)
            lines = new_markdown.split('\n')
            shown = 0
            for line in lines[:30]:  # Show first 30 lines
                if line.strip() and not line.startswith('|'):  # Skip table artifacts
                    print(f"   {line[:100]}")
                    shown += 1
                    if shown >= 10:
                        break
            print("   " + "-" * 60)
            
            # Check for common artifacts
            artifacts_found = []
            if 'From:' in new_markdown[:500]:
                artifacts_found.append("'From:' header")
            if 'Date:' in new_markdown[:500]:
                artifacts_found.append("'Date:' header")
            if 'Subject:' in new_markdown[:500]:
                artifacts_found.append("'Subject:' header")
            if '| --- |' in new_markdown[:500]:
                artifacts_found.append("Table formatting")
            if 'Original Message' in new_markdown[:500]:
                artifacts_found.append("'Original Message'")
            
            if artifacts_found:
                print(f"\n   ⚠️  Remaining artifacts: {', '.join(artifacts_found)}")
            else:
                print(f"\n   ✅ No forwarding artifacts detected in preview!")
            
        else:
            print("   ❌ No HTML content available")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_cleaning()