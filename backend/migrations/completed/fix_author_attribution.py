#!/usr/bin/env python3
"""Fix author attribution issues"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import SessionLocal, SubstackAuthor, SubstackArticle

def main():
    db = SessionLocal()
    
    print("🔧 FIXING AUTHOR ATTRIBUTION ISSUES")
    print("=" * 80)
    
    # Step 1: Fix Ethan Mollick's subdomain
    print("1. Fixing Ethan Mollick's subdomain...")
    ethan = db.query(SubstackAuthor).filter_by(email='oneusefulthing@substack.com').first()
    if ethan:
        print(f"   Current subdomain: {ethan.subdomain}")
        if ethan.subdomain != 'oneusefulthing':
            ethan.subdomain = 'oneusefulthing'
            ethan.url = 'https://oneusefulthing.substack.com'
            db.commit()
            print(f"   ✅ Updated to: {ethan.subdomain}")
        else:
            print(f"   ✅ Already correct")
    else:
        print("   ❌ Ethan Mollick not found!")
    
    # Step 2: Create David Szabo-Stuban author if doesn't exist
    print("\n2. Creating David Szabo-Stuban author...")
    david = db.query(SubstackAuthor).filter_by(subdomain='lumberjackai').first()
    if not david:
        david = SubstackAuthor(
            subdomain='lumberjackai',
            name='David Szabo-Stuban from Lumberjack',
            email='lumberjackai@substack.com',
            url='https://lumberjackai.substack.com'
        )
        db.add(david)
        db.flush()
        print(f"   ✅ Created new author: {david.name} (ID: {david.id})")
    else:
        print(f"   ✅ Already exists: {david.name} (ID: {david.id})")
    
    # Step 3: Find misattributed LumberjackAI articles
    print("\n3. Finding misattributed LumberjackAI articles...")
    
    # Find articles with "lumberjack" in title that are not attributed to David
    lumberjack_articles = []
    all_articles = db.query(SubstackArticle).all()
    
    for article in all_articles:
        title_lower = article.title.lower()
        if any(keyword in title_lower for keyword in ['lumberjack', 'david szabo']):
            current_author = db.query(SubstackAuthor).filter_by(id=article.author_id).first()
            if current_author.subdomain != 'lumberjackai':
                lumberjack_articles.append((article, current_author))
    
    print(f"   Found {len(lumberjack_articles)} misattributed LumberjackAI articles")
    
    # Step 4: Re-attribute articles to correct author
    if lumberjack_articles:
        print("\n4. Re-attributing articles to David Szabo-Stuban...")
        
        for article, wrong_author in lumberjack_articles:
            print(f"   Moving: {article.title[:50]}...")
            print(f"     From: {wrong_author.name} ({wrong_author.email})")
            print(f"     To: {david.name} ({david.email})")
            
            # Update the article's author
            article.author_id = david.id
        
        db.commit()
        print(f"   ✅ Re-attributed {len(lumberjack_articles)} articles")
    
    # Step 5: Verify the fix
    print(f"\n5. Verification:")
    
    authors = db.query(SubstackAuthor).all()
    for author in authors:
        article_count = db.query(SubstackArticle).filter_by(author_id=author.id).count()
        print(f"   {author.name}:")
        print(f"     Email: {author.email}")
        print(f"     Subdomain: {author.subdomain}")
        print(f"     Articles: {article_count}")
        
        # Show sample titles to verify correct attribution
        if article_count > 0:
            sample_articles = db.query(SubstackArticle).filter_by(author_id=author.id).limit(3).all()
            for sample in sample_articles:
                print(f"       - {sample.title[:40]}...")
        print()
    
    db.close()
    
    print("✅ Author attribution fix complete!")

if __name__ == "__main__":
    main()