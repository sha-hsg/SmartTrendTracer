#!/usr/bin/env python3
"""Clean up unwanted authors and articles from the database"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import SessionLocal, SubstackAuthor, SubstackArticle

def main():
    db = SessionLocal()
    
    print("🧹 Cleaning up unwanted authors and articles...")
    
    # Define expected authors - only these should remain
    expected_authors = {
        'robotic@substack.com',           # Nathan Lambert (forwarded)
        'garymarcus@substack.com',        # Gary Marcus (forwarded) 
        'sebastianraschka@substack.com',  # Sebastian Raschka (forwarded)
        'oneusefulthing@substack.com',    # Ethan Mollick (direct subscription) - keep this one
        'emollick@substack.com'           # Alternative Ethan Mollick email (if exists)
    }
    
    # Find unwanted authors
    unwanted_authors = []
    all_authors = db.query(SubstackAuthor).all()
    
    for author in all_authors:
        if author.email not in expected_authors:
            unwanted_authors.append(author)
            
    print(f"Found {len(unwanted_authors)} unwanted authors:")
    for author in unwanted_authors:
        article_count = db.query(SubstackArticle).filter_by(author_id=author.id).count()
        print(f"  ❌ {author.name} ({author.email}) - {article_count} articles")
        
        # Show articles that will be deleted
        if article_count > 0:
            articles = db.query(SubstackArticle).filter_by(author_id=author.id).all()
            for article in articles:
                print(f"     - {article.title[:60]}...")
    
    # Delete unwanted articles and authors
    if unwanted_authors:
        print(f"\n🗑️  Deleting {len(unwanted_authors)} unwanted authors and their articles...")
        
        total_articles_deleted = 0
        for author in unwanted_authors:
            # Delete all articles by this author
            articles = db.query(SubstackArticle).filter_by(author_id=author.id).all()
            for article in articles:
                db.delete(article)
                total_articles_deleted += 1
            
            # Delete the author
            db.delete(author)
        
        db.commit()
        print(f"✅ Deleted {len(unwanted_authors)} authors and {total_articles_deleted} articles")
    else:
        print("✅ No unwanted authors found - database is clean!")
    
    # Show final state
    print(f"\n📊 FINAL DATABASE STATE:")
    remaining_authors = db.query(SubstackAuthor).all()
    total_articles = db.query(SubstackArticle).count()
    
    print(f"Total authors: {len(remaining_authors)}")
    print(f"Total articles: {total_articles}")
    
    for author in remaining_authors:
        article_count = db.query(SubstackArticle).filter_by(author_id=author.id).count()
        print(f"  ✓ {author.name} ({author.email}) - {article_count} articles")
    
    db.close()

if __name__ == "__main__":
    main()