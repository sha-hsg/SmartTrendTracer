#!/usr/bin/env python3
"""
Fix PDF paths to use absolute paths
"""

import os
from pathlib import Path
from sqlalchemy.orm import Session
from app.models import get_db
from app.models.papers import Paper

def fix_pdf_paths_to_absolute():
    """Convert relative PDF paths to absolute paths"""
    
    db = next(get_db())
    
    try:
        # Get current working directory (backend directory)
        backend_dir = Path.cwd()
        print(f"Backend directory: {backend_dir}")
        
        # Find all papers
        papers = db.query(Paper).filter(Paper.pdf_path.isnot(None)).all()
        
        fixed_count = 0
        for paper in papers:
            if paper.pdf_path:
                pdf_path = Path(paper.pdf_path)
                
                # Check if path is relative
                if not pdf_path.is_absolute():
                    # Make it absolute
                    absolute_path = backend_dir / pdf_path
                    
                    if absolute_path.exists():
                        print(f"Fixing paper {paper.id}: {paper.title[:50]}...")
                        print(f"  From: {paper.pdf_path}")
                        print(f"  To: {absolute_path}")
                        
                        paper.pdf_path = str(absolute_path)
                        fixed_count += 1
                    else:
                        print(f"WARNING: File not found for paper {paper.id}: {absolute_path}")
                elif not Path(paper.pdf_path).exists():
                    # Absolute path but file doesn't exist - might be wrong absolute path
                    # Try relative path from backend dir
                    relative_attempt = backend_dir / Path(paper.pdf_path).name
                    if relative_attempt.exists():
                        print(f"Fixing broken absolute path for paper {paper.id}: {paper.title[:50]}...")
                        print(f"  From: {paper.pdf_path}")
                        print(f"  To: {relative_attempt}")
                        paper.pdf_path = str(relative_attempt)
                        fixed_count += 1
        
        db.commit()
        print(f"\nFixed {fixed_count} PDF paths to absolute paths")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_pdf_paths_to_absolute()