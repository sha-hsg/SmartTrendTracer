#!/usr/bin/env python3
"""Clean up non-Substack articles from the database"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import SessionLocal, SubstackAuthor, SubstackArticle

def main():
    db = SessionLocal()
    
    print("🧹 Cleaning up non-Substack articles...")
    
    # Find articles that are clearly not Substack newsletters
    junk_patterns = [
        'Bitte um Rechnung',
        'Arbeitsvertrag', 
        'Zweitvisum',
        'Nachfrage bezüglich',
        'Gedächtnisprotokoll',
        'Fragwürdiges Vorgehen',
        'Quittungen',
        'SVA Emilia',
        'Smart Life Registration',
        'Termin für Blutspiegel',
        'Formelle Anfrage',
        'Nachricht/Frage von',
        'Mein Gespräch mit'
    ]
    
    junk_articles = []
    all_articles = db.query(SubstackArticle).all()
    
    for article in all_articles:
        title = article.title or ''
        # Check if title contains junk patterns
        for pattern in junk_patterns:
            if pattern.lower() in title.lower():
                junk_articles.append(article)
                break
        
        # Also check for German administrative emails
        if any(word in title.lower() for word in ['rechnung', 'visum', 'termin', 'protokoll', 'gespräch']):
            if article not in junk_articles:
                junk_articles.append(article)
    
    print(f"🗑️  Found {len(junk_articles)} junk articles:")
    for article in junk_articles[:10]:  # Show first 10
        print(f"  - {article.title[:60]}...")
    
    if len(junk_articles) > 10:
        print(f"  ... and {len(junk_articles) - 10} more")
    
    # Delete junk articles
    if junk_articles:
        print(f"\n🗑️  Deleting {len(junk_articles)} junk articles...")
        for article in junk_articles:
            db.delete(article)
        db.commit()
        print(f"✅ Deleted {len(junk_articles)} junk articles")
    
    # Clean up authors with no articles
    print("\n🧹 Cleaning up orphaned authors...")
    authors = db.query(SubstackAuthor).all()
    orphaned = []
    
    for author in authors:
        article_count = db.query(SubstackArticle).filter_by(author_id=author.id).count()
        if article_count == 0:
            orphaned.append(author)
    
    if orphaned:
        print(f"🗑️  Deleting {len(orphaned)} orphaned authors...")
        for author in orphaned:
            db.delete(author)
        db.commit()
        print(f"✅ Deleted {len(orphaned)} orphaned authors")
    
    # Show final summary
    print(f"\n📊 Clean database summary:")
    remaining_authors = db.query(SubstackAuthor).all()
    print(f"  Total authors: {len(remaining_authors)}")
    
    for author in remaining_authors:
        article_count = db.query(SubstackArticle).filter_by(author_id=author.id).count()
        print(f"    {author.name}: {article_count} articles")
    
    db.close()

if __name__ == "__main__":
    main()