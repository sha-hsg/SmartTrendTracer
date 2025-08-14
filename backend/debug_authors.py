#!/usr/bin/env python3
"""Debug what authors are in the database and why"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import SessionLocal, SubstackAuthor, SubstackArticle

def main():
    db = SessionLocal()
    
    print("🔍 CURRENT AUTHORS IN DATABASE:")
    print("=" * 60)
    
    authors = db.query(SubstackAuthor).all()
    for author in authors:
        article_count = db.query(SubstackArticle).filter_by(author_id=author.id).count()
        print(f"\n👤 Author: {author.name}")
        print(f"   Email: {author.email}")
        print(f"   Subdomain: {author.subdomain}")
        print(f"   URL: {author.url}")
        print(f"   Articles: {article_count}")
        
        # Show sample article titles
        if article_count > 0:
            sample_articles = db.query(SubstackArticle).filter_by(author_id=author.id).limit(3).all()
            for article in sample_articles:
                print(f"     - {article.title[:60]}...")
    
    print(f"\n📊 SUMMARY:")
    print(f"Total authors: {len(authors)}")
    
    # Expected vs actual authors
    print(f"\n🎯 EXPECTED AUTHORS (from forwarded_authors.json + Ethan Mollick):")
    expected = [
        "Nathan Lambert (robotic@substack.com)",
        "Gary Marcus (garymarcus@substack.com)", 
        "Sebastian Raschka (sebastianraschka@substack.com)",
        "Ethan Mollick (emollick@substack.com)"
    ]
    for exp in expected:
        print(f"   ✓ {exp}")
    
    print(f"\n❌ UNEXPECTED AUTHORS:")
    unexpected = []
    for author in authors:
        if author.email not in ['robotic@substack.com', 'garymarcus@substack.com', 'sebastianraschka@substack.com', 'emollick@substack.com']:
            unexpected.append(f"{author.name} ({author.email})")
    
    for unexp in unexpected:
        print(f"   ⚠️  {unexp}")
    
    if not unexpected:
        print("   None - all authors are expected!")
    
    db.close()

if __name__ == "__main__":
    main()