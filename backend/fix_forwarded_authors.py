#!/usr/bin/env python3
"""
Fix forwarded author entries in the database
"""
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db
from app.models.substack import SubstackAuthor, SubstackArticle
from sqlalchemy import or_

def main():
    print("=" * 60)
    print("🔧 Fixing Forwarded Author Entries")
    print("=" * 60)
    
    # Load forwarded authors configuration
    with open('forwarded_authors.json', 'r') as f:
        config = json.load(f)
    
    forwarded_authors = config['forwarded_authors']
    
    db = next(get_db())
    
    print("\n📋 Configured forwarded authors:")
    for author in forwarded_authors:
        print(f"  • {author['name']} - {author['newsletter']}")
    
    print("\n🔍 Finding and fixing malformed author entries...")
    
    # Fix Nathan Lambert
    nathan = db.query(SubstackAuthor).filter(
        or_(
            SubstackAuthor.id == 3,
            SubstackAuthor.subdomain.contains("Nathan Lambert"),
            SubstackAuthor.subdomain.contains("robotic")
        )
    ).first()
    
    if nathan:
        print(f"\n✅ Found Nathan Lambert (ID: {nathan.id})")
        print(f"   Old subdomain: {nathan.subdomain}")
        nathan.name = "Nathan Lambert"
        nathan.subdomain = "robotic"
        nathan.url = "https://robotic.substack.com"
        nathan.description = "Interconnects Newsletter"
        print(f"   Fixed name: {nathan.name}")
        print(f"   Fixed subdomain: {nathan.subdomain}")
    
    # Fix Gary Marcus
    gary = db.query(SubstackAuthor).filter(
        or_(
            SubstackAuthor.id == 4,
            SubstackAuthor.subdomain.contains("Gary Marcus"),
            SubstackAuthor.subdomain.contains("garymarcus")
        )
    ).first()
    
    if gary:
        print(f"\n✅ Found Gary Marcus (ID: {gary.id})")
        print(f"   Old subdomain: {gary.subdomain}")
        gary.name = "Gary Marcus"
        gary.subdomain = "garymarcus"
        gary.url = "https://garymarcus.substack.com"
        gary.description = "Marcus on AI Newsletter"
        print(f"   Fixed name: {gary.name}")
        print(f"   Fixed subdomain: {gary.subdomain}")
    
    # Fix Sebastian Raschka
    sebastian = db.query(SubstackAuthor).filter(
        or_(
            SubstackAuthor.id == 5,
            SubstackAuthor.subdomain.contains("Sebastian Raschka"),
            SubstackAuthor.subdomain.contains("sebastianraschka")
        )
    ).first()
    
    if sebastian:
        print(f"\n✅ Found Sebastian Raschka (ID: {sebastian.id})")
        print(f"   Old subdomain: {sebastian.subdomain}")
        sebastian.name = "Sebastian Raschka"
        sebastian.subdomain = "sebastianraschka"
        sebastian.url = "https://sebastianraschka.substack.com"
        sebastian.description = "Ahead of AI Newsletter"
        print(f"   Fixed name: {sebastian.name}")
        print(f"   Fixed subdomain: {sebastian.subdomain}")
    
    # Also check for duplicate empty authors and clean them up
    empty_authors = db.query(SubstackAuthor).filter(
        or_(
            SubstackAuthor.name == "",
            SubstackAuthor.name == None,
            SubstackAuthor.name == " "
        )
    ).all()
    
    if empty_authors:
        print(f"\n🧹 Found {len(empty_authors)} empty author entries")
        for author in empty_authors:
            # Check if they have articles
            article_count = db.query(SubstackArticle).filter(
                SubstackArticle.author_id == author.id
            ).count()
            
            if article_count == 0:
                print(f"   Deleting empty author ID {author.id} (no articles)")
                db.delete(author)
            else:
                print(f"   Keeping author ID {author.id} ({article_count} articles)")
    
    # Commit all changes
    db.commit()
    print("\n✅ Database fixed!")
    
    # Show updated authors
    print("\n📊 Updated author list:")
    authors = db.query(SubstackAuthor).filter(
        SubstackAuthor.id.in_([3, 4, 5])
    ).all()
    
    for author in authors:
        article_count = db.query(SubstackArticle).filter(
            SubstackArticle.author_id == author.id,
            SubstackArticle.deleted == False
        ).count()
        print(f"  • {author.name} (ID: {author.id})")
        print(f"    Subdomain: {author.subdomain}")
        print(f"    URL: {author.url}")
        print(f"    Articles: {article_count}")
    
    db.close()
    
    print("\n💡 Next steps:")
    print("  1. Run the collector to fetch articles from these authors:")
    print("     python collect_configured_authors.py")

if __name__ == "__main__":
    main()