#!/usr/bin/env python3
"""
Fix papers with temporary PDF paths by re-downloading to permanent location
"""

import os
import shutil
from pathlib import Path
from sqlalchemy.orm import Session
from app.models import get_db
from app.models.papers import Paper
from app.services.arxiv_import_service import get_arxiv_service

def fix_temporary_pdfs():
    """Re-download PDFs from ArXiv to permanent location"""
    
    # Create permanent directory for ArXiv PDFs
    arxiv_dir = Path("data/papers/arxiv")
    arxiv_dir.mkdir(parents=True, exist_ok=True)
    
    db = next(get_db())
    
    try:
        # Find papers with temporary paths
        papers_with_temp_paths = db.query(Paper).filter(
            (Paper.pdf_path.like('/var/folders%')) | 
            (Paper.pdf_path.like('/tmp%')) |
            (Paper.pdf_path.like('/var/tmp%'))
        ).all()
        
        print(f"Found {len(papers_with_temp_paths)} papers with temporary PDF paths")
        
        for paper in papers_with_temp_paths:
            print(f"\nProcessing: {paper.title}")
            print(f"  Current path: {paper.pdf_path}")
            
            # Check if current file still exists
            if paper.pdf_path and os.path.exists(paper.pdf_path):
                # File exists, just move it to permanent location
                print(f"  File exists, moving to permanent location...")
                
                # Generate new permanent path
                if paper.arxiv_id:
                    # Clean arxiv_id (remove version)
                    arxiv_id_clean = paper.arxiv_id.replace('arXiv:', '').split('v')[0]
                    new_filename = f"{arxiv_id_clean.replace('/', '_')}.pdf"
                else:
                    # Use paper ID as fallback
                    new_filename = f"paper_{paper.id}.pdf"
                
                new_path = arxiv_dir / new_filename
                
                # Copy file to new location (don't move in case something goes wrong)
                shutil.copy2(paper.pdf_path, new_path)
                print(f"  Copied to: {new_path}")
                
                # Update database
                paper.pdf_path = str(new_path)
                db.commit()
                print(f"  Database updated successfully")
                
            elif paper.arxiv_id:
                # File doesn't exist but we have ArXiv ID, re-download
                print(f"  File missing, re-downloading from ArXiv...")
                
                arxiv_service = get_arxiv_service()
                
                # Extract ArXiv ID (remove version)
                arxiv_id = paper.arxiv_id.replace('arXiv:', '').split('v')[0]
                
                # Re-import just the PDF
                result = arxiv_service.import_paper(arxiv_id, download_dir=str(arxiv_dir))
                
                if result['success'] and result['pdf_path']:
                    paper.pdf_path = result['pdf_path']
                    db.commit()
                    print(f"  Re-downloaded to: {result['pdf_path']}")
                else:
                    print(f"  ERROR: Failed to re-download from ArXiv")
            else:
                print(f"  ERROR: No ArXiv ID and file doesn't exist - cannot recover PDF")
        
        print(f"\nFixed {len(papers_with_temp_paths)} papers")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_temporary_pdfs()