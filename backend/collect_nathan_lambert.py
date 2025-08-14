#!/usr/bin/env python3
"""
Specifically collect Nathan Lambert / Interconnects articles from Gmail
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.collectors.gmail_substack_collector import GmailSubstackCollector
from app.models import SessionLocal

def main():
    print("🔍 Searching for Nathan Lambert / Interconnects articles...")
    
    collector = GmailSubstackCollector()
    db = SessionLocal()
    
    # Different search strategies
    searches = [
        # Try original subject lines
        'subject:"GPT-OSS: OpenAI validates the open ecosystem"',
        'subject:"GPT-5 and the arc of progress"',
        
        # Try forwarded versions
        'subject:(FW: OR Fwd:) "GPT-OSS"',
        'subject:(FW: OR Fwd:) "GPT-5 and the arc"',
        
        # Try by content
        '"Nathan Lambert" "Interconnects"',
        'from:"robotic@substack.com"',
        
        # Try the exact titles you mentioned
        '"GPT-OSS: OpenAI validates the open ecosystem (finally)"',
        '"GPT-5 and the arc of progress"',
        
        # Broader search
        'subject:Interconnects newer_than:90d',
        '"robotic" "substack" newer_than:90d'
    ]
    
    collected = []
    
    for query in searches:
        print(f"\n🔎 Trying: {query}")
        try:
            count = collector.collect_newsletters(query=query, max_results=5)
            if count > 0:
                collected.append((query, count))
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # Summary
    print("\n\n📊 Collection Summary:")
    if collected:
        for query, count in collected:
            print(f"  ✅ '{query[:50]}...': {count} articles")
    else:
        print("  ❌ No Nathan Lambert articles found")
    
    # Check what we have in the database
    from app.models import SubstackArticle, SubstackAuthor
    
    nathan = db.query(SubstackAuthor).filter(
        (SubstackAuthor.name.like('%Nathan%')) |
        (SubstackAuthor.subdomain == 'robotic')
    ).first()
    
    if nathan:
        articles = db.query(SubstackArticle).filter_by(author_id=nathan.id).all()
        print(f"\n📚 Nathan Lambert articles in database:")
        for article in articles:
            print(f"  - {article.title[:60]}... ({article.word_count} words)")
    
    db.close()

if __name__ == "__main__":
    main()