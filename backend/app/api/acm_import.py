"""
ACM Digital Library paper import API endpoints
Handles paper imports from dl.acm.org
"""

from app.paths import PAPERS_DIR_REL
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from pathlib import Path
from datetime import datetime, timezone
import logging
from bson import ObjectId
from app.database.mongodb import get_database
from app.services.acm_service import acm_service
from app.services.pdf_processor_service import get_pdf_processor_service
from app.repositories import acm_import_queries as queries

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/acm", tags=["acm"])

class ACMImportRequest(BaseModel):
    url: HttpUrl
    add_tags: Optional[List[str]] = None
    process_pdf: bool = False

@router.post("/import")
async def import_acm_paper(request: ACMImportRequest, background_tasks: BackgroundTasks):
    """
    Import a paper from ACM Digital Library
    
    Args:
        request: Import request with ACM URL and optional tags
        
    Returns:
        Import result with paper ID and metadata
    """
    try:
        db = get_database()
        
        # Set up save directory
        save_dir = PAPERS_DIR_REL
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Import paper using ACM service
        logger.info(f"Importing ACM paper from: {request.url}")
        paper_data = acm_service.import_paper(str(request.url), save_dir)
        
        # Create MongoDB document
        authors_string = paper_data.get('authors', '')
        authors_detailed = []
        if authors_string:
            # Convert comma-separated authors string to detailed array
            # (canonical schema: objects with name/affiliation/email, like arxiv.py)
            author_names = [name.strip() for name in authors_string.split(',') if name.strip()]
            authors_detailed = [
                {'name': name, 'affiliation': '', 'email': ''}
                for name in author_names
            ]
        
        paper_doc = {
            'title': paper_data.get('title', 'Untitled'),
            'authors': authors_string,
            'authors_detailed': authors_detailed,
            'abstract': paper_data.get('abstract', ''),
            'pdf_path': paper_data.get('pdf_path'),
            'pdf_url': paper_data.get('pdf_url'),
            'doi': paper_data.get('doi'),
            'year': paper_data.get('year'),
            'venue': paper_data.get('venue'),
            'conference': paper_data.get('conference'),
            'journal': paper_data.get('journal'),
            'publisher': paper_data.get('publisher', 'ACM'),
            'pages': paper_data.get('pages'),
            'volume': paper_data.get('volume'),
            'number': paper_data.get('number'),
            'keywords': paper_data.get('keywords'),
            'bibtex': paper_data.get('bibtex'),
            'source': 'acm',
            'source_url': str(request.url),
            'import_source': 'acm',  # Track import source type
            'import_url': str(request.url),  # Store original import URL
            'paper_type': 'research',
            'created_at': datetime.now(timezone.utc),
            'processed': False,
            'processor': None,
            'markdown_content': None,
            'sections': [],
            'references': [],
            'tags': request.add_tags or [],
            'snippets': [],
            'notes': '',
            'flagged': False
        }
        
        # Insert into MongoDB
        result = queries.papers_insert_one__import_acm_paper(paper_doc)
        paper_id = str(result.inserted_id)
        
        logger.info(f"Successfully imported ACM paper with ID: {paper_id}")

        # Process PDF in background if requested and PDF was downloaded
        if request.process_pdf and paper_doc.get('pdf_path'):
            background_tasks.add_task(
                process_pdf_background,
                paper_id,
                paper_doc['pdf_path']
            )

        return {
            'success': True,
            'paper_id': paper_id,
            'title': paper_doc['title'],
            'authors': paper_doc['authors'],
            'doi': paper_doc.get('doi'),
            'year': paper_doc.get('year'),
            'venue': paper_doc.get('venue'),
            'pdf_path': paper_doc.get('pdf_path'),
            'processing': bool(request.process_pdf and paper_doc.get('pdf_path')),
            'message': f"Successfully imported paper from ACM"
        }

    except ValueError as e:
        logger.error(f"Invalid ACM URL: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error importing ACM paper: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to import paper: {str(e)}")

def process_pdf_background(paper_id: str, pdf_path: str):
    """
    Background task to process an imported ACM PDF (Marker preferred).
    """
    try:
        logger.info(f"Processing PDF for ACM paper {paper_id} in background")
        db_bg = get_database()

        processor = get_pdf_processor_service()
        result = processor.process_pdf(
            pdf_path,
            prefer_method="marker",
            mongo_paper_id=paper_id
        )

        if result and result.get('success'):
            db_bg.papers.update_one(
                {'_id': ObjectId(paper_id)},
                {'$set': {
                    'content': result.get('markdown', ''),
                    'markdown_content': result.get('markdown', ''),
                    'processed': True,
                    'processor_used': result.get('method_used', 'unknown'),
                    'processed_at': datetime.now(timezone.utc)
                }}
            )
            logger.info(f"PDF processing completed for ACM paper {paper_id}")
        else:
            logger.error(f"PDF processing failed for ACM paper {paper_id}: {result.get('error') if result else 'no result'}")

    except Exception as e:
        logger.error(f"Error in background PDF processing for ACM paper {paper_id}: {e}")

@router.get("/validate-url")
async def validate_acm_url(url: str):
    """
    Validate if a URL is a valid ACM paper URL
    
    Args:
        url: URL to validate
        
    Returns:
        Validation result with extracted DOI if valid
    """
    try:
        doi = acm_service.extract_doi_from_url(url)
        if doi:
            return {
                'valid': True,
                'doi': doi,
                'message': 'Valid ACM URL'
            }
        else:
            return {
                'valid': False,
                'doi': None,
                'message': 'Could not extract DOI from URL'
            }
    except Exception as e:
        logger.error(f"Error validating ACM URL: {e}")
        return {
            'valid': False,
            'doi': None,
            'message': str(e)
        }