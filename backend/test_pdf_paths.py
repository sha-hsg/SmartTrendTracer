#!/usr/bin/env python3
"""
Test PDF paths for debugging
"""

import os
from pathlib import Path
from sqlalchemy.orm import Session
from app.models import get_db
from app.models.papers import Paper
from app.paths import PAPERS_DIR

def test_pdf_paths():
    """Test PDF paths and file existence"""
    
    db = next(get_db())
    
    try:
        # Get papers 1, 2, 3
        papers = db.query(Paper).filter(Paper.id.in_([1, 2, 3])).all()
        
        print("=" * 80)
        print("PDF PATH DEBUG INFORMATION")
        print("=" * 80)
        print(f"Current working directory: {os.getcwd()}")
        print()
        
        for paper in papers:
            print(f"Paper ID {paper.id}: {paper.title[:50]}...")
            print(f"  PDF path in DB: {paper.pdf_path}")
            
            if paper.pdf_path:
                print(f"  Is absolute path: {os.path.isabs(paper.pdf_path)}")
                print(f"  File exists: {os.path.exists(paper.pdf_path)}")
                
                if os.path.exists(paper.pdf_path):
                    file_size = os.path.getsize(paper.pdf_path)
                    print(f"  File size: {file_size:,} bytes")
                else:
                    # Try to find the file
                    basename = os.path.basename(paper.pdf_path)
                    
                    # Check various locations
                    possible_paths = [
                        Path("data/papers/arxiv") / basename,
                        PAPERS_DIR / "arxiv" / basename,
                        Path.cwd() / "data/papers/arxiv" / basename,
                    ]
                    
                    print(f"  File NOT found. Checking alternative locations:")
                    for path in possible_paths:
                        exists = path.exists()
                        print(f"    {path}: {'EXISTS' if exists else 'not found'}")
                        if exists:
                            print(f"      Size: {path.stat().st_size:,} bytes")
            else:
                print(f"  ERROR: No PDF path in database!")
            
            print()
        
        # List files in arxiv directory
        arxiv_dir = Path("data/papers/arxiv")
        if arxiv_dir.exists():
            print("Files in data/papers/arxiv/:")
            for file in sorted(arxiv_dir.glob("*.pdf"))[:10]:
                print(f"  {file.name} ({file.stat().st_size:,} bytes)")
        else:
            print(f"ERROR: Directory does not exist: {arxiv_dir.absolute()}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_pdf_paths()