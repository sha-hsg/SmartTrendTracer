#!/usr/bin/env python3
"""
Test the API directly without HTTP
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.api.substack import get_articles, get_authors
from app.models import get_db

def main():
    print("=" * 60)
    print("📚 Testing API Functions Directly")
    print("=" * 60)
    
    db = next(get_db())
    
    # Test get_authors
    print("\n📝 Testing get_authors():")
    authors = get_authors(db)
    print(f"  Found {len(authors)} authors")
    for author in authors[:3]:
        print(f"  - ID: {author['id']}, Name: {author['name']}, Articles: {author['article_count']}")
    
    # Test get_articles without filter
    print("\n📖 Testing get_articles() - no filter:")
    result = get_articles(skip=0, limit=5, author_id=None, search=None, tag=None, db=db)
    print(f"  Total articles: {result['total']}")
    print(f"  Returned: {len(result['articles'])} articles")
    
    # Test get_articles with author filter
    if authors and authors[0]['article_count'] > 0:
        author_id = authors[0]['id']
        print(f"\n📖 Testing get_articles() - filtered by author ID {author_id}:")
        result = get_articles(skip=0, limit=5, author_id=author_id, search=None, tag=None, db=db)
        print(f"  Total articles for this author: {result['total']}")
        print(f"  Returned: {len(result['articles'])} articles")
        for article in result['articles'][:3]:
            print(f"    - {article['title'][:50]}... by {article['author']['name']}")
    
    db.close()

if __name__ == "__main__":
    main()