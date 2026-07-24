#!/usr/bin/env python3
"""
Fix missing PDF for paper ID 9
"""
import os
import requests
from datetime import datetime
from app.models import get_db
from app.models.papers import Paper

def download_arxiv_pdf(arxiv_id: str, save_path: str) -> bool:
    """Download PDF from ArXiv"""
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    
    try:
        print(f"Downloading PDF from {pdf_url}...")
        response = requests.get(pdf_url, stream=True)
        response.raise_for_status()
        
        # Save the PDF
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"PDF saved to {save_path}")
        return True
    except Exception as e:
        print(f"Error downloading PDF: {e}")
        return False

def fix_paper_pdf(paper_id: int = 9):
    """Fix the PDF path for a specific paper"""
    db = next(get_db())
    
    try:
        # Get the paper
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            print(f"Paper {paper_id} not found")
            return
        
        print(f"Found paper: {paper.title}")
        print(f"Current PDF path: {paper.pdf_path}")
        print(f"ArXiv ID: {paper.arxiv_id}")
        
        if not paper.arxiv_id:
            print("No ArXiv ID found, cannot re-download")
            return
        
        # Create proper path in data/papers directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_arxiv_{paper.arxiv_id.replace('/', '_')}.pdf"
        pdf_dir = os.path.join(os.path.dirname(__file__), "data", "papers")
        
        # Ensure directory exists
        os.makedirs(pdf_dir, exist_ok=True)
        
        new_pdf_path = os.path.join(pdf_dir, filename)
        
        # Download the PDF
        if download_arxiv_pdf(paper.arxiv_id, new_pdf_path):
            # Update the database
            paper.pdf_path = new_pdf_path
            db.commit()
            print(f"✅ Successfully updated paper {paper_id}")
            print(f"New PDF path: {new_pdf_path}")
        else:
            print(f"❌ Failed to download PDF for paper {paper_id}")
            
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_paper_pdf(9)