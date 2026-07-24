#!/usr/bin/env python3
"""Fix PDF paths for papers - move from temp to permanent location"""

import os
import sys
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.models import get_db, Paper

def fix_pdf_paths():
    """Fix PDF paths by moving files to permanent location"""
    
    # Get database session
    db = next(get_db())
    
    # Create papers directory if it doesn't exist
    papers_dir = Path("data/papers")
    papers_dir.mkdir(parents=True, exist_ok=True)
    
    # Get all papers with pdf_path
    papers = db.query(Paper).filter(Paper.pdf_path != None).all()
    
    fixed_count = 0
    missing_count = 0
    already_correct = 0
    
    for paper in papers:
        if not paper.pdf_path:
            continue
            
        current_path = Path(paper.pdf_path)
        
        # Check if path is already in data/papers
        if str(current_path).startswith(str(papers_dir)):
            if current_path.exists():
                already_correct += 1
                continue
            else:
                print(f"Paper {paper.id}: PDF missing at correct path: {current_path}")
                missing_count += 1
                paper.pdf_path = None
                continue
        
        # Check if the current file exists
        if not current_path.exists():
            print(f"Paper {paper.id}: PDF not found at {current_path}")
            
            # Try to find it in data/papers with various naming patterns
            possible_names = [
                f"{paper.id}_{current_path.name}",
                f"paper_{paper.id}.pdf",
                current_path.name
            ]
            
            found = False
            for name in possible_names:
                possible_path = papers_dir / name
                if possible_path.exists():
                    print(f"  Found at: {possible_path}")
                    paper.pdf_path = str(possible_path.absolute())
                    fixed_count += 1
                    found = True
                    break
            
            if not found:
                paper.pdf_path = None
                missing_count += 1
        else:
            # File exists at temp location, move it to permanent location
            
            # Generate a proper filename
            if paper.arxiv_id:
                filename = f"arxiv_{paper.arxiv_id.replace('/', '_')}.pdf"
            else:
                # Use paper ID and sanitized title
                safe_title = "".join(c for c in paper.title[:50] if c.isalnum() or c in (' ', '-', '_')).strip()
                safe_title = safe_title.replace(' ', '_')
                filename = f"{paper.id}_{safe_title}.pdf"
            
            new_path = papers_dir / filename
            
            # Check if target already exists
            if new_path.exists():
                # Use a different name
                counter = 1
                while True:
                    alt_path = papers_dir / f"{paper.id}_{counter}_{filename}"
                    if not alt_path.exists():
                        new_path = alt_path
                        break
                    counter += 1
            
            try:
                # Copy the file (don't move in case it's being used elsewhere)
                shutil.copy2(current_path, new_path)
                paper.pdf_path = str(new_path.absolute())
                fixed_count += 1
                print(f"Paper {paper.id}: Moved PDF from {current_path} to {new_path}")
            except Exception as e:
                print(f"Paper {paper.id}: Error moving PDF: {e}")
                paper.pdf_path = None
                missing_count += 1
    
    # Commit changes
    db.commit()
    
    print(f"\nSummary:")
    print(f"  Already correct: {already_correct}")
    print(f"  Fixed: {fixed_count}")
    print(f"  Missing/removed: {missing_count}")
    print(f"  Total processed: {len(papers)}")

if __name__ == "__main__":
    fix_pdf_paths()