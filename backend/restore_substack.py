#!/usr/bin/env python3
"""
Restore lost Substack data by collecting newsletters from Gmail
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.collectors.gmail_substack_collector import GmailSubstackCollector
from app.models import get_db, SubstackArticle, SubstackAuthor
from sqlalchemy import func
import json

def restore_substack():
    """Collect Substack newsletters from Gmail"""
    
    # Check current state
    db = next(get_db())
    current_articles = db.query(func.count(SubstackArticle.id)).scalar()
    current_authors = db.query(func.count(SubstackAuthor.id)).scalar()
    print(f"Current state:")
    print(f"  - Articles: {current_articles}")
    print(f"  - Authors: {current_authors}")
    
    # Initialize collector
    print("\nInitializing Gmail collector...")
    collector = GmailSubstackCollector()
    
    # Collect both direct and forwarded newsletters
    print("\nCollecting newsletters...")
    print("-" * 50)
    
    try:
        # Collect all newsletters (both direct and forwarded)
        print("Collecting newsletters from Gmail...")
        total_count = collector.collect_newsletters(max_results=100)
        print(f"✅ Collected {total_count} newsletters")
        
    except Exception as e:
        print(f"❌ Error during collection: {e}")
        print("\nTrying to collect with smaller batch size...")
        
        try:
            # Try with smaller batch
            total_count = collector.collect_newsletters(max_results=50)
            print(f"✅ Collected {total_count} newsletters (smaller batch)")
        except Exception as e2:
            print(f"❌ Still failing: {e2}")
    
    # Check final state
    final_articles = db.query(func.count(SubstackArticle.id)).scalar()
    final_authors = db.query(func.count(SubstackAuthor.id)).scalar()
    
    print("-" * 50)
    print(f"\nFinal state:")
    print(f"  - Articles: {final_articles} (+{final_articles - current_articles})")
    print(f"  - Authors: {final_authors} (+{final_authors - current_authors})")
    
    # Show breakdown by author
    if final_authors > 0:
        author_counts = db.query(
            SubstackAuthor.name,
            func.count(SubstackArticle.id)
        ).join(
            SubstackArticle, SubstackAuthor.id == SubstackArticle.author_id
        ).group_by(SubstackAuthor.name).all()
        
        print("\nArticles by author:")
        for author, count in sorted(author_counts, key=lambda x: x[1], reverse=True):
            print(f"  {author}: {count} articles")

if __name__ == "__main__":
    restore_substack()