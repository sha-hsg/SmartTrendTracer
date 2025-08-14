#!/usr/bin/env python3
"""
Check if there are articles from the configured forwarded authors
"""
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db
from app.models.substack import SubstackAuthor, SubstackArticle
from sqlalchemy import or_, func

def main():
    print("=" * 60)
    print("📚 Checking Forwarded Authors in Database")
    print("=" * 60)
    
    # Load forwarded authors configuration
    with open('forwarded_authors.json', 'r') as f:
        config = json.load(f)
    
    forwarded_authors = config['forwarded_authors']
    
    print(f"\n📋 Configured forwarded authors ({len(forwarded_authors)}):")
    for author in forwarded_authors:
        print(f"  • {author['name']} - {author['newsletter']} ({author['email']})")
    
    db = next(get_db())
    
    print("\n🔍 Searching database for these authors...")
    print("-" * 40)
    
    # Check each configured author
    found_any = False
    for configured_author in forwarded_authors:
        name = configured_author['name']
        newsletter = configured_author['newsletter']
        email = configured_author['email']
        
        # Search for author in database using various patterns
        authors = db.query(SubstackAuthor).filter(
            or_(
                SubstackAuthor.name.contains(name),
                SubstackAuthor.name.contains(newsletter),
                SubstackAuthor.subdomain.contains(email.split('@')[0]),
                SubstackAuthor.email == email if hasattr(SubstackAuthor, 'email') else False
            )
        ).all()
        
        if authors:
            found_any = True
            for author in authors:
                article_count = db.query(SubstackArticle).filter(
                    SubstackArticle.author_id == author.id,
                    SubstackArticle.deleted == False
                ).count()
                
                print(f"\n✅ FOUND: {author.name}")
                print(f"   ID: {author.id}")
                print(f"   Subdomain: {author.subdomain}")
                print(f"   Articles: {article_count}")
                
                # Show sample articles
                if article_count > 0:
                    sample_articles = db.query(SubstackArticle).filter(
                        SubstackArticle.author_id == author.id,
                        SubstackArticle.deleted == False
                    ).order_by(SubstackArticle.published_at.desc()).limit(3).all()
                    
                    print("   Recent articles:")
                    for article in sample_articles:
                        print(f"     - {article.title[:60]}...")
        else:
            print(f"\n❌ NOT FOUND: {name} ({newsletter})")
    
    if not found_any:
        print("\n⚠️ None of the configured forwarded authors were found in the database!")
        print("\n💡 Suggestions:")
        print("  1. Run the selective Gmail collector:")
        print("     python collect_configured_authors.py")
        print("  2. Check if emails are being forwarded correctly")
        print("  3. Verify the forward settings in forwarded_authors.json")
    
    # Also check for any authors with similar names
    print("\n📊 All authors in database:")
    all_authors = db.query(
        SubstackAuthor.name,
        func.count(SubstackArticle.id).label('article_count')
    ).outerjoin(
        SubstackArticle
    ).group_by(
        SubstackAuthor.id
    ).having(
        func.count(SubstackArticle.id) > 0
    ).all()
    
    for author_name, count in all_authors:
        # Check if any of the configured names partially match
        for configured in forwarded_authors:
            if (configured['name'].lower() in author_name.lower() or 
                author_name.lower() in configured['name'].lower()):
                print(f"  🔍 Possible match: {author_name} ({count} articles)")
                break
        else:
            print(f"  • {author_name}: {count} articles")
    
    db.close()

if __name__ == "__main__":
    main()