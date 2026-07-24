#!/usr/bin/env python3
"""
Collect forwarded Substack emails from UniSG account
Specifically handles emails forwarded from siegfried.handschuh@unisg.ch
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.collectors.gmail_substack_collector import GmailSubstackCollector

def main():
    """Collect forwarded Substack emails"""
    
    # Custom query for forwarded emails
    queries = [
        # Emails from your UniSG account
        'from:siegfried.handschuh@unisg.ch @substack.com',
        'from:me to:me @substack.com',
        # Specific newsletter patterns in subject
        'subject:"Marcus on AI"',
        'subject:"Interconnects"',
        'subject:"AI Agents"',
        'subject:"GPT-OSS"',
        # General pattern for forwarded Substack emails
        '(from:unisg.ch OR from:handschuh) @substack.com',
    ]
    
    collector = GmailSubstackCollector()
    total_collected = 0
    
    for query in queries:
        print(f"\n🔍 Searching with query: {query}")
        try:
            articles = collector.collect_newsletters(query=query, max_results=50)
            total_collected += articles
            print(f"   Collected {articles} articles")
        except Exception as e:
            print(f"   Error: {e}")
    
    print(f"\n✅ Total collected: {total_collected} articles")
    
    # Also show what we have
    from app.models import get_db, SubstackArticle, SubstackAuthor
    db = next(get_db())
    
    print("\n📊 Database Summary:")
    total_articles = db.query(SubstackArticle).filter(SubstackArticle.deleted == False).count()
    authors = db.query(SubstackAuthor.name).distinct().all()
    
    print(f"Total articles: {total_articles}")
    print(f"Authors collected:")
    for author in authors:
        author_name = author[0]
        count = db.query(SubstackArticle).join(SubstackAuthor).filter(
            SubstackAuthor.name == author_name,
            SubstackArticle.deleted == False
        ).count()
        print(f"  - {author_name}: {count} articles")

if __name__ == "__main__":
    main()