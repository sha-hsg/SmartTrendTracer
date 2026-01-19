#!/usr/bin/env python3
"""
Reprocess a paper to extract images
"""
import sys
from app.services.pdf_processor_service import get_pdf_processor_service
from app.models import get_db
from app.models.papers import Paper
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reprocess_paper(paper_id: int):
    """Reprocess a paper with image extraction"""
    db = next(get_db())
    try:
        # Get the paper
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            logger.error(f"Paper {paper_id} not found")
            return False
        
        if not paper.pdf_path:
            logger.error(f"Paper {paper_id} has no PDF path")
            return False
            
        logger.info(f"Reprocessing paper {paper_id}: {paper.title}")
        logger.info(f"PDF path: {paper.pdf_path}")
        
        # Process with image extraction
        pdf_processor = get_pdf_processor_service()
        result = pdf_processor.process_pdf(
            paper.pdf_path, 
            paper_id=paper_id,  # This enables image extraction
            prefer_method="marker_service"  # Use Marker for best quality
        )
        
        if result['success']:
            # Update paper with new content
            paper.content = result['markdown']
            paper.processor_used = result.get('method_used', 'unknown')
            
            db.commit()
            
            images_extracted = result.get('metadata', {}).get('images_extracted', 0)
            logger.info(f"✅ Successfully reprocessed paper {paper_id}")
            logger.info(f"   Method used: {result.get('method_used')}")
            logger.info(f"   Images extracted: {images_extracted}")
            logger.info(f"   Content length: {len(result['markdown'])} characters")
            
            return True
        else:
            logger.error(f"Failed to reprocess paper: {result.get('error')}")
            return False
            
    except Exception as e:
        logger.error(f"Error reprocessing paper: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python reprocess_paper_with_images.py <paper_id>")
        print("\nExample: python reprocess_paper_with_images.py 1")
        sys.exit(1)
    
    paper_id = int(sys.argv[1])
    success = reprocess_paper(paper_id)
    sys.exit(0 if success else 1)