#!/usr/bin/env python3
"""
Delete incorrectly collected articles
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import SessionLocal, SubstackArticle, SubstackAuthor

def main():
    db = SessionLocal()
    
    try:
        # Articles to delete - LinkedIn notifications, Manning books, etc.
        articles_to_delete = []
        
        # Find LinkedIn and Manning articles
        wrong_articles = db.query(SubstackArticle).filter(
            (SubstackArticle.title.like('%LinkedIn%')) |
            (SubstackArticle.title.like('%Manning%')) |
            (SubstackArticle.title.like('%liveBook%')) |
            (SubstackArticle.title.like('%Newsletter on LinkedIn%')) |
            (SubstackArticle.title.like('Siegfried, people who follow%')) |
            (SubstackArticle.title == 'Untitled')
        ).all()
        
        print(f"Found {len(wrong_articles)} articles to delete:")
        for article in wrong_articles:
            print(f"  - {article.id}: {article.title[:60]}...")
            articles_to_delete.append(article)
        
        # Also check for wrong content
        all_articles = db.query(SubstackArticle).all()
        for article in all_articles:
            # Check if it's actually not a newsletter
            if article.content_markdown:
                content = article.content_markdown[:500]
                # LinkedIn notifications
                if ('linkedin.com/school/university' in content or
                    'Manning Online Pro' in content or
                    'liveBook' in content or
                    'Lehrstuhlbücher' in content or  # German internal email
                    'Medium daily digest' in content or
                    'discord.gg' in article.title or
                    'https://discord' in article.title):
                    
                    if article not in articles_to_delete:
                        print(f"  - {article.id}: {article.title[:60]}... (wrong content)")
                        articles_to_delete.append(article)
        
        if articles_to_delete:
            confirm = input(f"\nDelete {len(articles_to_delete)} articles? (y/n): ")
            if confirm.lower() == 'y':
                for article in articles_to_delete:
                    db.delete(article)
                db.commit()
                print(f"✅ Deleted {len(articles_to_delete)} articles")
            else:
                print("❌ Cancelled")
        else:
            print("No articles to delete")
        
        # Clean up orphaned authors
        print("\nChecking for orphaned authors...")
        authors = db.query(SubstackAuthor).all()
        orphaned = []
        for author in authors:
            count = db.query(SubstackArticle).filter_by(author_id=author.id).count()
            if count == 0:
                print(f"  Orphaned author: {author.name}")
                orphaned.append(author)
        
        if orphaned:
            confirm = input(f"\nDelete {len(orphaned)} orphaned authors? (y/n): ")
            if confirm.lower() == 'y':
                for author in orphaned:
                    db.delete(author)
                db.commit()
                print(f"✅ Deleted {len(orphaned)} orphaned authors")
        
        # Show remaining articles
        print("\n📊 Remaining articles:")
        remaining = db.query(SubstackArticle).count()
        print(f"  Total: {remaining}")
        
        # By author
        from sqlalchemy import func
        author_stats = db.query(
            SubstackAuthor.name,
            func.count(SubstackArticle.id)
        ).join(
            SubstackArticle
        ).group_by(
            SubstackAuthor.name
        ).all()
        
        for name, count in author_stats:
            if count > 0:
                print(f"  {name}: {count} articles")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()