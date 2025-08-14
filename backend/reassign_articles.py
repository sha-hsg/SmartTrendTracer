#!/usr/bin/env python3
"""
Reassign articles to the correct authors based on content
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
    print("🔄 Reassigning Articles to Correct Authors")
    print("=" * 60)
    
    db = next(get_db())
    
    # Get the fixed authors
    nathan = db.query(SubstackAuthor).filter(SubstackAuthor.id == 3).first()
    gary = db.query(SubstackAuthor).filter(SubstackAuthor.id == 4).first()
    sebastian = db.query(SubstackAuthor).filter(SubstackAuthor.id == 5).first()
    
    print("\n📋 Target authors:")
    print(f"  • Nathan Lambert (ID: {nathan.id})")
    print(f"  • Gary Marcus (ID: {gary.id})")
    print(f"  • Sebastian Raschka (ID: {sebastian.id})")
    
    # Find articles that might belong to these authors
    # Check all articles and look for patterns in their content
    
    print("\n🔍 Searching for misassigned articles...")
    
    articles = db.query(SubstackArticle).filter(
        SubstackArticle.deleted == False
    ).all()
    
    reassigned_count = 0
    
    for article in articles:
        # Check title and content for author patterns
        content_to_check = (article.title or "") + " " + (article.preview or "")
        content_lower = content_to_check.lower()
        
        # Check for Nathan Lambert / Interconnects
        if any(pattern in content_lower for pattern in ['nathan lambert', 'interconnects', 'robotic.substack']):
            if article.author_id != nathan.id:
                print(f"\n  📝 Article: {article.title[:50]}...")
                print(f"     Old author ID: {article.author_id} → New: {nathan.id} (Nathan Lambert)")
                article.author_id = nathan.id
                reassigned_count += 1
        
        # Check for Gary Marcus / Marcus on AI
        elif any(pattern in content_lower for pattern in ['gary marcus', 'marcus on ai', 'garymarcus.substack']):
            if article.author_id != gary.id:
                print(f"\n  📝 Article: {article.title[:50]}...")
                print(f"     Old author ID: {article.author_id} → New: {gary.id} (Gary Marcus)")
                article.author_id = gary.id
                reassigned_count += 1
        
        # Check for Sebastian Raschka / Ahead of AI
        elif any(pattern in content_lower for pattern in ['sebastian raschka', 'ahead of ai', 'sebastianraschka.substack']):
            if article.author_id != sebastian.id:
                print(f"\n  📝 Article: {article.title[:50]}...")
                print(f"     Old author ID: {article.author_id} → New: {sebastian.id} (Sebastian Raschka)")
                article.author_id = sebastian.id
                reassigned_count += 1
        
        # Also check if the URL contains patterns
        if article.url:
            url_lower = article.url.lower()
            if 'robotic.substack' in url_lower and article.author_id != nathan.id:
                print(f"\n  📝 Article: {article.title[:50]}...")
                print(f"     URL indicates Nathan Lambert")
                print(f"     Old author ID: {article.author_id} → New: {nathan.id}")
                article.author_id = nathan.id
                reassigned_count += 1
            elif 'garymarcus.substack' in url_lower and article.author_id != gary.id:
                print(f"\n  📝 Article: {article.title[:50]}...")
                print(f"     URL indicates Gary Marcus")
                print(f"     Old author ID: {article.author_id} → New: {gary.id}")
                article.author_id = gary.id
                reassigned_count += 1
            elif 'sebastianraschka.substack' in url_lower and article.author_id != sebastian.id:
                print(f"\n  📝 Article: {article.title[:50]}...")
                print(f"     URL indicates Sebastian Raschka")
                print(f"     Old author ID: {article.author_id} → New: {sebastian.id}")
                article.author_id = sebastian.id
                reassigned_count += 1
    
    if reassigned_count > 0:
        db.commit()
        print(f"\n✅ Reassigned {reassigned_count} articles!")
    else:
        print("\n✅ No articles needed reassignment")
    
    # Show final counts
    print("\n📊 Final article counts:")
    
    for author in [nathan, gary, sebastian]:
        article_count = db.query(SubstackArticle).filter(
            SubstackArticle.author_id == author.id,
            SubstackArticle.deleted == False
        ).count()
        
        if article_count > 0:
            print(f"\n  • {author.name}: {article_count} articles")
            # Show sample titles
            samples = db.query(SubstackArticle).filter(
                SubstackArticle.author_id == author.id,
                SubstackArticle.deleted == False
            ).limit(3).all()
            for sample in samples:
                print(f"    - {sample.title[:60]}...")
        else:
            print(f"  • {author.name}: {article_count} articles")
    
    db.close()

if __name__ == "__main__":
    main()