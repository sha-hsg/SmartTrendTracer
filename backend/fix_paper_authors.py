#!/usr/bin/env python3
"""
Fix papers that have authors in the text field but no PaperAuthor records.
This script creates PaperAuthor records from the authors text field.
"""

from app.models import SessionLocal, Paper, PaperAuthor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_paper_authors():
    db = SessionLocal()
    
    try:
        # Find all papers with authors but no PaperAuthor records
        papers = db.query(Paper).filter(
            Paper.authors != None,
            Paper.authors != '',
            Paper.authors != 'None'
        ).all()
        
        fixed_count = 0
        for paper in papers:
            # Check if PaperAuthor records already exist
            existing_authors = db.query(PaperAuthor).filter(
                PaperAuthor.paper_id == paper.id
            ).count()
            
            if existing_authors == 0 and paper.authors:
                # Create PaperAuthor records
                author_names = [name.strip() for name in paper.authors.split(',')]
                
                logger.info(f"Creating {len(author_names)} PaperAuthor records for paper {paper.id}: {paper.title[:50]}...")
                
                for i, author_name in enumerate(author_names):
                    if author_name and author_name.strip():
                        author = PaperAuthor(
                            paper_id=paper.id,
                            name=author_name.strip(),
                            position=i
                        )
                        db.add(author)
                
                fixed_count += 1
        
        db.commit()
        logger.info(f"Fixed {fixed_count} papers with missing PaperAuthor records")
        
        # Verify the fix
        papers_with_authors = db.query(Paper).filter(
            Paper.authors != None,
            Paper.authors != '',
            Paper.authors != 'None'
        ).count()
        
        papers_with_records = db.query(Paper).join(
            PaperAuthor, Paper.id == PaperAuthor.paper_id
        ).distinct().count()
        
        logger.info(f"Papers with authors text: {papers_with_authors}")
        logger.info(f"Papers with PaperAuthor records: {papers_with_records}")
        
    except Exception as e:
        logger.error(f"Error fixing paper authors: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    fix_paper_authors()