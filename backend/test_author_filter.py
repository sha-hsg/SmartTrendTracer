#!/usr/bin/env python3
"""
Test author filtering in Substack API
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db
from app.models.substack import SubstackAuthor, SubstackArticle

def main():
    print("=" * 60)
    print("📚 Testing Author Filter")
    print("=" * 60)
    
    db = next(get_db())
    
    # Get all authors
    authors = db.query(SubstackAuthor).all()
    print(f"\n📝 Found {len(authors)} authors:")
    
    for author in authors:
        # Count articles for this author
        article_count = db.query(SubstackArticle).filter(
            SubstackArticle.author_id == author.id,
            SubstackArticle.deleted == False
        ).count()
        
        print(f"  ID: {author.id} - {author.name}: {article_count} articles")
    
    # Test filtering for each author
    print("\n🧪 Testing filter for each author:")
    for author in authors[:3]:  # Test first 3 authors
        articles = db.query(SubstackArticle).filter(
            SubstackArticle.author_id == author.id,
            SubstackArticle.deleted == False
        ).limit(5).all()
        
        print(f"\n  Author: {author.name} (ID: {author.id})")
        if articles:
            for article in articles:
                print(f"    - {article.title[:50]}...")
        else:
            print("    No articles found")
    
    db.close()

if __name__ == "__main__":
    main()