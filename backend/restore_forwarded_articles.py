#!/usr/bin/env python3
"""
Restore soft-deleted articles from forwarded authors
"""
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db
from app.models.substack import SubstackAuthor, SubstackArticle
from sqlalchemy import or_, and_

def main():
    print("=" * 60)
    print("♻️ Restoring Deleted Articles from Forwarded Authors")
    print("=" * 60)
    
    # Load forwarded authors configuration
    with open('forwarded_authors.json', 'r') as f:
        config = json.load(f)
    
    forwarded_authors = config['forwarded_authors']
    
    db = next(get_db())
    
    print("\n📋 Looking for deleted articles from:")
    for author in forwarded_authors:
        print(f"  • {author['name']} - {author['newsletter']}")
    
    # Get the author IDs
    nathan = db.query(SubstackAuthor).filter(SubstackAuthor.id == 3).first()
    gary = db.query(SubstackAuthor).filter(SubstackAuthor.id == 4).first()
    sebastian = db.query(SubstackAuthor).filter(SubstackAuthor.id == 5).first()
    
    author_ids = []
    if nathan:
        author_ids.append(nathan.id)
    if gary:
        author_ids.append(gary.id)
    if sebastian:
        author_ids.append(sebastian.id)
    
    # Find all deleted articles from these authors or with "Untitled" name
    deleted_articles = db.query(SubstackArticle).filter(
        and_(
            SubstackArticle.deleted == True,
            or_(
                SubstackArticle.author_id.in_(author_ids),
                SubstackArticle.title == "Untitled"
            )
        )
    ).all()
    
    if deleted_articles:
        print(f"\n🔍 Found {len(deleted_articles)} deleted articles")
        
        restored_count = 0
        for article in deleted_articles:
            # Check if this might be from one of our authors
            # (Untitled articles are likely from forwarded emails)
            if article.title == "Untitled" or article.author_id in author_ids:
                print(f"\n  📄 Article ID {article.id}: {article.title[:50]}...")
                print(f"     Author ID: {article.author_id}")
                print(f"     Preview: {article.preview[:100] if article.preview else 'No preview'}...")
                
                # Try to identify the correct author from content
                content_to_check = (article.preview or "") + " " + (article.content_markdown or "")[:500]
                content_lower = content_to_check.lower()
                
                # Assign to correct author based on content
                if 'nathan lambert' in content_lower or 'interconnects' in content_lower:
                    article.author_id = nathan.id
                    article.title = article.title if article.title != "Untitled" else "Article from Nathan Lambert"
                    print(f"     → Assigned to Nathan Lambert (ID: {nathan.id})")
                elif 'gary marcus' in content_lower or 'marcus on ai' in content_lower:
                    article.author_id = gary.id
                    article.title = article.title if article.title != "Untitled" else "Article from Gary Marcus"
                    print(f"     → Assigned to Gary Marcus (ID: {gary.id})")
                elif 'sebastian raschka' in content_lower or 'ahead of ai' in content_lower:
                    article.author_id = sebastian.id
                    article.title = article.title if article.title != "Untitled" else "Article from Sebastian Raschka"
                    print(f"     → Assigned to Sebastian Raschka (ID: {sebastian.id})")
                
                # Restore the article
                article.deleted = False
                restored_count += 1
                print(f"     ✅ Restored!")
        
        if restored_count > 0:
            db.commit()
            print(f"\n✅ Restored {restored_count} articles!")
    else:
        print("\n❌ No deleted articles found from these authors")
    
    # Show final counts
    print("\n📊 Final article counts:")
    
    for author, author_obj in [("Nathan Lambert", nathan), ("Gary Marcus", gary), ("Sebastian Raschka", sebastian)]:
        if author_obj:
            article_count = db.query(SubstackArticle).filter(
                SubstackArticle.author_id == author_obj.id,
                SubstackArticle.deleted == False
            ).count()
            
            print(f"  • {author}: {article_count} articles")
            
            if article_count > 0:
                # Show sample titles
                samples = db.query(SubstackArticle).filter(
                    SubstackArticle.author_id == author_obj.id,
                    SubstackArticle.deleted == False
                ).limit(3).all()
                for sample in samples:
                    print(f"    - {sample.title[:60]}...")
    
    db.close()

if __name__ == "__main__":
    main()