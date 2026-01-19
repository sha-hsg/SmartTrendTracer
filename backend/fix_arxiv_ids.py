#!/usr/bin/env python3
"""
Fix ArXiv IDs by removing category suffixes like [cs.CL]
"""

import re
from sqlalchemy.orm import Session
from app.models import get_db
from app.models.papers import Paper

def fix_arxiv_ids():
    """Remove category suffixes from ArXiv IDs"""
    
    db = next(get_db())
    
    try:
        # Find all papers with ArXiv IDs
        papers = db.query(Paper).filter(Paper.arxiv_id.isnot(None)).all()
        
        fixed_count = 0
        print(f"Checking {len(papers)} papers with ArXiv IDs...")
        print()
        
        for paper in papers:
            if paper.arxiv_id:
                original_id = paper.arxiv_id
                
                # Remove various forms of category suffixes
                # Examples: [cs.CL], [cs.AI], [math.NA], etc.
                cleaned_id = re.sub(r'\[.*?\]$', '', original_id)
                cleaned_id = cleaned_id.strip()
                
                # Also remove "arXiv:" prefix if present (for consistency)
                cleaned_id = cleaned_id.replace('arXiv:', '').strip()
                
                if cleaned_id != original_id:
                    print(f"Paper ID {paper.id}: {paper.title[:50]}...")
                    print(f"  Original: {original_id}")
                    print(f"  Cleaned:  {cleaned_id}")
                    print()
                    
                    paper.arxiv_id = cleaned_id
                    fixed_count += 1
        
        if fixed_count > 0:
            db.commit()
            print(f"✅ Fixed {fixed_count} ArXiv IDs")
        else:
            print("✅ All ArXiv IDs are already clean")
        
        # Show sample of current ArXiv IDs
        print("\nSample of current ArXiv IDs:")
        sample_papers = db.query(Paper).filter(Paper.arxiv_id.isnot(None)).limit(5).all()
        for paper in sample_papers:
            print(f"  {paper.arxiv_id} - {paper.title[:50]}...")
            
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_arxiv_ids()