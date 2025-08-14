#!/usr/bin/env python3
"""Clean up the broken HTML authors in the database"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import SessionLocal, SubstackAuthor, SubstackArticle
import json
from pathlib import Path

def main():
    db = SessionLocal()
    
    print("🧹 Cleaning up broken author entries...")
    
    # Load the proper author config
    config_path = Path(__file__).parent / 'forwarded_authors.json'
    configured_authors = {}
    
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
            for author in config.get('forwarded_authors', []):
                configured_authors[author['email']] = author
                print(f"  Loaded config for: {author['name']} ({author['email']})")
    
    # Find broken authors (those with HTML garbage in names)
    broken_authors = db.query(SubstackAuthor).filter(
        (SubstackAuthor.name.like('%&lt;%')) |  # HTML entities
        (SubstackAuthor.name.like('%</%')) |    # HTML tags  
        (SubstackAuthor.name.like('%</span>%')) |
        (SubstackAuthor.name.like('%&gt;%')) |
        (SubstackAuthor.name == '')             # Empty names
    ).all()
    
    print(f"\n🔍 Found {len(broken_authors)} broken authors:")
    for author in broken_authors:
        print(f"  ID {author.id}: '{author.name[:50]}...'")
    
    # Delete broken authors and their articles
    if broken_authors:
        print(f"\n🗑️  Deleting {len(broken_authors)} broken authors and their articles...")
        if True:  # Auto-proceed
            for author in broken_authors:
                # Delete articles first
                articles = db.query(SubstackArticle).filter_by(author_id=author.id).all()
                for article in articles:
                    db.delete(article)
                # Delete author
                db.delete(author)
            
            db.commit()
            print(f"✅ Deleted {len(broken_authors)} broken authors")
    
    # Create proper authors from config
    print(f"\n📝 Creating proper authors from forwarded_authors.json...")
    
    for email, author_config in configured_authors.items():
        # Extract subdomain from email
        if '@substack.com' in email:
            subdomain = email.split('@')[0]
        else:
            subdomain = author_config['name'].lower().replace(' ', '-')
        
        # Check if author already exists
        existing = db.query(SubstackAuthor).filter_by(
            subdomain=subdomain
        ).first()
        
        if not existing:
            # Create new author
            author = SubstackAuthor(
                subdomain=subdomain,
                name=author_config['name'],
                email=email,
                url=f"https://{subdomain}.substack.com"
            )
            db.add(author)
            print(f"  ✅ Created: {author_config['name']} ({subdomain})")
        else:
            print(f"  👍 Already exists: {existing.name}")
    
    db.commit()
    
    # Show final summary
    print(f"\n📊 Final summary:")
    all_authors = db.query(SubstackAuthor).all()
    print(f"  Total authors: {len(all_authors)}")
    for author in all_authors:
        article_count = db.query(SubstackArticle).filter_by(author_id=author.id).count()
        print(f"    {author.name}: {article_count} articles")
    
    db.close()

if __name__ == "__main__":
    main()