#!/usr/bin/env python3
"""Debug author attribution issues"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import SessionLocal, SubstackAuthor, SubstackArticle

def main():
    db = SessionLocal()
    
    print("🔍 DEBUGGING AUTHOR ATTRIBUTION ISSUES")
    print("=" * 80)
    
    # Get all authors and their articles
    authors = db.query(SubstackAuthor).all()
    
    for author in authors:
        print(f"\n👤 Author: {author.name}")
        print(f"   Database Email: {author.email}")
        print(f"   Subdomain: {author.subdomain}")
        print(f"   URL: {author.url}")
        
        # Get all articles for this author
        articles = db.query(SubstackArticle).filter_by(author_id=author.id).all()
        print(f"   Total Articles: {len(articles)}")
        
        # Show sample articles with their source info
        print(f"   Sample articles:")
        for article in articles[:5]:  # Show first 5
            # Check if this is a Gmail-sourced article (forwarded)
            is_forwarded = article.substack_id and article.substack_id.startswith('gmail_')
            source_type = "Forwarded" if is_forwarded else "Direct"
            
            print(f"     - {article.title[:50]}... [{source_type}]")
            
            # For direct articles, the substack_id might contain author info
            if not is_forwarded and article.substack_id:
                print(f"       Substack ID: {article.substack_id}")
        
        # Look for inconsistencies - articles that might belong to different authors
        if len(articles) > 10:  # Only check authors with many articles
            print(f"\n   🔍 Checking for attribution issues...")
            
            # Sample some article titles to look for obvious misattributions
            sample_titles = [article.title for article in articles[:10]]
            
            # Look for patterns that suggest wrong attribution
            author_mentions = []
            for title in sample_titles:
                title_lower = title.lower()
                # Common patterns that might indicate the real author
                if 'david szabo' in title_lower or 'lumberjack' in title_lower:
                    author_mentions.append("David Szabo-Stuban/LumberjackAI")
                elif 'ethan mollick' in title_lower or 'one useful thing' in title_lower:
                    author_mentions.append("Ethan Mollick")
                elif 'gary marcus' in title_lower:
                    author_mentions.append("Gary Marcus")
                elif 'nathan lambert' in title_lower:
                    author_mentions.append("Nathan Lambert")
                elif 'sebastian raschka' in title_lower:
                    author_mentions.append("Sebastian Raschka")
            
            if author_mentions:
                print(f"     ⚠️  Title analysis suggests these authors: {set(author_mentions)}")
                if author.name not in str(set(author_mentions)):
                    print(f"     ❌ MISMATCH: Database author '{author.name}' doesn't match title patterns!")
    
    print(f"\n" + "=" * 80)
    print("🔍 CHECKING SPECIFIC ISSUE: lumberjackai@substack.com")
    
    # Look for any articles that might be from David Szabo-Stuban/LumberjackAI
    all_articles = db.query(SubstackArticle).all()
    lumberjack_articles = []
    
    for article in all_articles:
        title_lower = article.title.lower()
        if any(keyword in title_lower for keyword in ['lumberjack', 'david szabo', 'stuban']):
            lumberjack_articles.append(article)
    
    print(f"Found {len(lumberjack_articles)} articles that might be from LumberjackAI:")
    for article in lumberjack_articles:
        attributed_author = db.query(SubstackAuthor).filter_by(id=article.author_id).first()
        print(f"  - {article.title}")
        print(f"    Attributed to: {attributed_author.name} ({attributed_author.email})")
        print(f"    Substack ID: {article.substack_id}")
        print(f"    Should be: David Szabo-Stuban (lumberjackai@substack.com)")
        print()
    
    db.close()

if __name__ == "__main__":
    main()