#!/usr/bin/env python3
"""
Preview articles from an author before deletion
"""
import sys
import os
import argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db
from app.models.substack import SubstackAuthor, SubstackArticle
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description='Preview author articles')
    parser.add_argument('--author-id', type=int, help='Author ID to preview')
    parser.add_argument('--author-name', type=str, help='Author name (partial match)')
    parser.add_argument('--show-content', action='store_true', help='Show article content preview')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("📚 Author Articles Preview")
    print("=" * 60)
    
    db = next(get_db())
    
    # Find the author
    author = None
    if args.author_id:
        author = db.query(SubstackAuthor).filter(SubstackAuthor.id == args.author_id).first()
    elif args.author_name:
        # Find by partial name match
        authors = db.query(SubstackAuthor).filter(
            SubstackAuthor.name.ilike(f"%{args.author_name}%")
        ).all()
        
        if len(authors) == 0:
            print(f"❌ No author found matching '{args.author_name}'")
            return
        elif len(authors) == 1:
            author = authors[0]
        else:
            print(f"🔍 Multiple authors found matching '{args.author_name}':")
            for a in authors:
                article_count = db.query(SubstackArticle).filter(
                    SubstackArticle.author_id == a.id,
                    SubstackArticle.deleted == False
                ).count()
                print(f"  ID {a.id}: {a.name} ({article_count} articles)")
            print("\nPlease specify --author-id with the exact ID")
            return
    else:
        print("❌ Please specify either --author-id or --author-name")
        return
    
    if not author:
        print(f"❌ Author not found")
        return
    
    # Get all articles from this author
    articles = db.query(SubstackArticle).filter(
        SubstackArticle.author_id == author.id
    ).order_by(SubstackArticle.published_at.desc()).all()
    
    active_articles = [a for a in articles if not a.deleted]
    deleted_articles = [a for a in articles if a.deleted]
    
    print(f"\n📚 Author: {author.name} (ID: {author.id})")
    print(f"   Subdomain: {author.subdomain}")
    print(f"   URL: {author.url}")
    print(f"   Description: {author.description}")
    print(f"\n   Total articles: {len(articles)}")
    print(f"   Active articles: {len(active_articles)}")
    print(f"   Soft-deleted: {len(deleted_articles)}")
    
    if not articles:
        print("\n   No articles found for this author")
        return
    
    # Show active articles
    if active_articles:
        print("\n" + "=" * 60)
        print("📖 ACTIVE ARTICLES")
        print("=" * 60)
        
        for i, article in enumerate(active_articles, 1):
            print(f"\n{i}. Article ID: {article.id}")
            print(f"   Title: {article.title[:100]}")
            if article.subtitle:
                print(f"   Subtitle: {article.subtitle[:100]}")
            
            # Show dates
            if article.published_at:
                pub_date = article.published_at.strftime("%Y-%m-%d %H:%M")
                print(f"   Published: {pub_date}")
            if article.collected_at:
                coll_date = article.collected_at.strftime("%Y-%m-%d %H:%M")
                print(f"   Collected: {coll_date}")
            
            # Show metadata
            if article.word_count:
                print(f"   Words: {article.word_count}")
            if article.reading_time_minutes:
                print(f"   Reading time: {article.reading_time_minutes} min")
            
            # Show URL
            if article.url:
                print(f"   URL: {article.url[:80]}...")
            
            # Show preview if requested
            if args.show_content and article.preview:
                preview = article.preview.replace('\n', ' ')[:200]
                print(f"   Preview: {preview}...")
            
            # Check if summarized
            if article.summary:
                print("   ✅ Has AI summary")
            
            # Count snippets
            snippet_count = len(article.snippets) if hasattr(article, 'snippets') else 0
            if snippet_count > 0:
                print(f"   📌 {snippet_count} highlights/snippets")
            
            # Show tags
            if hasattr(article, 'tags') and article.tags:
                tags = [tag.tag for tag in article.tags[:5]]
                print(f"   🏷️ Tags: {', '.join(tags)}")
    
    # Show deleted articles summary
    if deleted_articles:
        print("\n" + "=" * 60)
        print("🗑️ SOFT-DELETED ARTICLES (not shown in dashboard)")
        print("=" * 60)
        
        for article in deleted_articles[:5]:  # Show max 5
            print(f"   • ID {article.id}: {article.title[:60]}...")
    
    # Ask for confirmation to delete
    print("\n" + "=" * 60)
    if active_articles:
        print(f"\n⚠️ This author has {len(active_articles)} active articles")
        print("To delete this author and all articles, run:")
        print(f"   python delete_author_and_articles.py --author-id {author.id}")
        print("\nTo delete in the UI:")
        print("   1. Go to Substack dashboard")
        print(f"   2. Click on '{author.name}' in the author list")
        print("   3. Click the 🗑️ button that appears")
    else:
        print("\n✅ This author has no active articles")
        print("Safe to delete if not needed")
    
    db.close()

if __name__ == "__main__":
    main()