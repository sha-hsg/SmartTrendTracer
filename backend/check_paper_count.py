#!/usr/bin/env python3
"""Quick check of papers in database"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db, Paper

def check_papers():
    """Check papers in database"""
    try:
        db = next(get_db())
        
        # Count papers
        total_papers = db.query(Paper).count()
        print(f"Total papers in database: {total_papers}")
        
        # Get some sample papers
        papers = db.query(Paper).limit(5).all()
        
        if papers:
            print("\nSample papers:")
            for p in papers:
                print(f"  - {p.title[:60]}...")
                if p.authors:
                    print(f"    Authors: {p.authors[:60]}...")
                if p.abstract:
                    print(f"    Abstract: {p.abstract[:100]}...")
                print()
        
        # Check if papers have content
        papers_with_content = db.query(Paper).filter(Paper.content != None).count()
        papers_with_abstract = db.query(Paper).filter(Paper.abstract != None).count()
        
        print(f"Papers with content: {papers_with_content}")
        print(f"Papers with abstract: {papers_with_abstract}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    check_papers()