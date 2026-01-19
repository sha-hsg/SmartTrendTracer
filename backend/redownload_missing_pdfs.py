#!/usr/bin/env python3
"""Re-download missing PDFs from ArXiv"""

import os
import sys
import requests
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db, Paper

def download_arxiv_pdf(arxiv_id: str, output_path: Path) -> bool:
    """Download PDF from ArXiv"""
    # Clean up arxiv_id (remove 'arXiv:' prefix and version if present)
    clean_id = arxiv_id.replace('arXiv:', '').replace('arxiv:', '')
    
    # ArXiv PDF URL
    pdf_url = f"https://arxiv.org/pdf/{clean_id}.pdf"
    
    print(f"  Downloading from: {pdf_url}")
    
    try:
        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status()
        
        # Save PDF
        output_path.write_bytes(response.content)
        print(f"  Saved to: {output_path}")
        return True
        
    except Exception as e:
        print(f"  Error downloading: {e}")
        return False

def redownload_missing_pdfs():
    """Re-download missing PDFs from ArXiv"""
    
    # Get database session
    db = next(get_db())
    
    # Create papers directory if it doesn't exist
    papers_dir = Path("data/papers")
    papers_dir.mkdir(parents=True, exist_ok=True)
    
    # Get papers with missing PDFs that have arxiv_id
    papers = db.query(Paper).filter(
        Paper.pdf_path == None,
        Paper.arxiv_id != None
    ).all()
    
    if not papers:
        # Also check for papers with pdf_path that doesn't exist
        all_papers = db.query(Paper).filter(Paper.arxiv_id != None).all()
        papers = []
        for p in all_papers:
            if p.pdf_path:
                if not Path(p.pdf_path).exists():
                    papers.append(p)
    
    print(f"Found {len(papers)} papers with missing PDFs and ArXiv IDs\n")
    
    downloaded = 0
    failed = 0
    
    for paper in papers:
        print(f"Paper {paper.id}: {paper.title[:60]}...")
        print(f"  ArXiv ID: {paper.arxiv_id}")
        
        # Generate filename
        clean_id = paper.arxiv_id.replace('arXiv:', '').replace('arxiv:', '').replace('/', '_')
        filename = f"arxiv_{clean_id}.pdf"
        pdf_path = papers_dir / filename
        
        # Check if already exists
        if pdf_path.exists():
            print(f"  PDF already exists at: {pdf_path}")
            paper.pdf_path = str(pdf_path.absolute())
            downloaded += 1
        else:
            # Download PDF
            if download_arxiv_pdf(paper.arxiv_id, pdf_path):
                paper.pdf_path = str(pdf_path.absolute())
                downloaded += 1
            else:
                failed += 1
        
        print()
    
    # Commit changes
    db.commit()
    
    print(f"\nSummary:")
    print(f"  Downloaded/fixed: {downloaded}")
    print(f"  Failed: {failed}")
    print(f"  Total processed: {len(papers)}")

if __name__ == "__main__":
    redownload_missing_pdfs()