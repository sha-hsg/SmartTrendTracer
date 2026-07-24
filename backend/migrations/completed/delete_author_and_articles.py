#!/usr/bin/env python3
"""
Delete all articles from an author and optionally the author itself
"""
import sys
import os
import argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db
from app.models.substack import SubstackAuthor, SubstackArticle, ArticleSnippet, ArticleTag

def main():
    parser = argparse.ArgumentParser(description='Delete author and all their articles')
    parser.add_argument('--author-id', type=int, help='Author ID to delete')
    parser.add_argument('--author-name', type=str, help='Author name (partial match)')
    parser.add_argument('--list', action='store_true', help='List all authors')
    parser.add_argument('--force', action='store_true', help='Skip confirmation')
    parser.add_argument('--keep-author', action='store_true', help='Keep author, only delete articles')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🗑️ Delete Author and Articles Utility")
    print("=" * 60)
    
    db = next(get_db())
    
    if args.list:
        # List all authors
        authors = db.query(SubstackAuthor).all()
        print("\n📚 All authors in database:")
        for author in authors:
            article_count = db.query(SubstackArticle).filter(
                SubstackArticle.author_id == author.id,
                SubstackArticle.deleted == False
            ).count()
            print(f"  ID {author.id}: {author.name} ({article_count} articles)")
        return
    
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
        print("   Use --list to see all authors")
        return
    
    if not author:
        print(f"❌ Author not found")
        return
    
    # Get article count
    articles = db.query(SubstackArticle).filter(
        SubstackArticle.author_id == author.id
    ).all()
    
    active_articles = [a for a in articles if not a.deleted]
    deleted_articles = [a for a in articles if a.deleted]
    
    print(f"\n📚 Author: {author.name} (ID: {author.id})")
    print(f"   Subdomain: {author.subdomain}")
    print(f"   Total articles: {len(articles)}")
    print(f"   Active articles: {len(active_articles)}")
    print(f"   Already deleted: {len(deleted_articles)}")
    
    if not args.force:
        print("\n⚠️ This will permanently delete:")
        print(f"   • {len(articles)} articles (including snippets and tags)")
        if not args.keep_author:
            print(f"   • The author entry '{author.name}'")
        
        confirmation = input("\nType 'DELETE' to confirm: ")
        if confirmation != 'DELETE':
            print("❌ Cancelled")
            return
    
    # Delete all articles and related data
    deleted_count = 0
    snippet_count = 0
    tag_count = 0
    
    for article in articles:
        # Delete snippets
        snippets = db.query(ArticleSnippet).filter(
            ArticleSnippet.article_id == article.id
        ).all()
        for snippet in snippets:
            db.delete(snippet)
            snippet_count += 1
        
        # Delete tags
        tags = db.query(ArticleTag).filter(
            ArticleTag.article_id == article.id
        ).all()
        for tag in tags:
            db.delete(tag)
            tag_count += 1
        
        # Delete article
        db.delete(article)
        deleted_count += 1
    
    # Delete author if requested
    if not args.keep_author:
        db.delete(author)
        print(f"\n✅ Deleted author '{author.name}'")
    
    # Commit changes
    db.commit()
    
    print(f"\n✅ Deletion complete!")
    print(f"   • Articles deleted: {deleted_count}")
    print(f"   • Snippets deleted: {snippet_count}")
    print(f"   • Tags deleted: {tag_count}")
    
    db.close()

if __name__ == "__main__":
    main()