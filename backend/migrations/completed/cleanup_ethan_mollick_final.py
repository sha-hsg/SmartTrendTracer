#!/usr/bin/env python3
"""
Final cleanup for Ethan Mollick articles
Keep only articles that are confirmed to be from One Useful Thing
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db
from app.models.substack import SubstackAuthor, SubstackArticle

def cleanup_ethan_articles(dry_run=True):
    """Remove non-Ethan Mollick articles from his author record"""
    db = next(get_db())
    
    try:
        # Find Ethan Mollick author
        ethan = db.query(SubstackAuthor).filter(
            SubstackAuthor.name.ilike('%Ethan Mollick%')
        ).first()
        
        if not ethan:
            print("❌ Ethan Mollick author not found")
            return
        
        print(f"📊 Analyzing articles for: {ethan.name}")
        print(f"   Email: {ethan.email}")
        print()
        
        # Get all articles
        articles = db.query(SubstackArticle).filter(
            SubstackArticle.author_id == ethan.id
        ).all()
        
        print(f"📚 Found {len(articles)} articles currently attributed to Ethan Mollick")
        print()
        
        # Categorize articles
        confirmed_ethan = []
        to_remove = []
        
        for article in articles:
            is_ethan = False
            
            # Check for One Useful Thing / Ethan Mollick markers
            if article.content_markdown:
                content_lower = article.content_markdown.lower()
                
                # Strong indicators this is Ethan Mollick
                if any(marker in content_lower for marker in [
                    'one useful thing',
                    'ethan mollick',
                    'wharton',
                    'professor mollick',
                    'oneusefulthing.org'
                ]):
                    is_ethan = True
                
                # Check for non-Ethan patterns (these override)
                if any(marker in content_lower for marker in [
                    'lumberjack',
                    'david szabo',
                    'alfredos',
                    'n8n workflow',
                    'no-code',
                    'railway deploy',
                    'promptivity',
                    '100 days of no-code',
                    'weekend developer',
                    'verification code to sign in',  # Substack system emails
                    'owlstown newsletter'  # Different newsletter
                ]):
                    is_ethan = False
            
            # Also check title for suspicious patterns
            if article.title:
                title_lower = article.title.lower()
                
                # System/spam titles
                if any(pattern in title_lower for pattern in [
                    'has(>',  # CSS/HTML artifacts
                    'verification code',
                    'unread',
                    '💬',  # Chat notifications
                    'recommendations from your substacks',
                    'discount ends',
                    'owlstown'
                ]):
                    is_ethan = False
            
            if is_ethan:
                confirmed_ethan.append(article)
            else:
                to_remove.append(article)
        
        # Display results
        print("📈 Analysis Results:")
        print(f"   ✅ Confirmed Ethan Mollick articles: {len(confirmed_ethan)}")
        print(f"   ❌ Articles to remove: {len(to_remove)}")
        print()
        
        if to_remove:
            print("Articles to be removed:")
            for article in to_remove:
                print(f"   - {article.title[:60]}...")
                if article.content_markdown:
                    preview = article.content_markdown[:100].replace('\n', ' ')
                    print(f"     Preview: {preview}...")
            print()
        
        if confirmed_ethan:
            print("Articles to keep (sample):")
            for article in confirmed_ethan[:5]:
                print(f"   ✅ {article.title[:60]}...")
            if len(confirmed_ethan) > 5:
                print(f"   ... and {len(confirmed_ethan) - 5} more")
            print()
        
        if not dry_run and to_remove:
            response = input(f"\n⚠️  Remove {len(to_remove)} articles? (yes/no): ")
            
            if response.lower() == 'yes':
                for article in to_remove:
                    db.delete(article)
                    print(f"   ✓ Deleted: {article.title[:50]}...")
                
                db.commit()
                print(f"\n✅ Successfully removed {len(to_remove)} articles")
                print(f"   {len(confirmed_ethan)} Ethan Mollick articles remain")
            else:
                print("\n❌ Cleanup cancelled")
        elif dry_run:
            print("\n🔍 DRY RUN - No changes made")
            print(f"   Run with --execute to remove {len(to_remove)} articles")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean up Ethan Mollick articles")
    parser.add_argument("--execute", action="store_true", help="Actually remove articles (not dry run)")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("ETHAN MOLLICK ARTICLE CLEANUP")
    print("=" * 60)
    print()
    
    cleanup_ethan_articles(dry_run=not args.execute)