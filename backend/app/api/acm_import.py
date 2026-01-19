"""
ACM Digital Library paper import API endpoints
Handles paper imports from dl.acm.org
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from pathlib import Path
from datetime import datetime
import logging
from bson import ObjectId
from app.database.mongodb import get_database
from app.services.acm_service import acm_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/acm", tags=["acm"])

class ACMImportRequest(BaseModel):
    url: HttpUrl
    add_tags: Optional[List[str]] = None
    process_pdf: bool = False

@router.post("/import")
async def import_acm_paper(request: ACMImportRequest):
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
        save_dir = Path("data/papers")
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Import paper using ACM service
        logger.info(f"Importing ACM paper from: {request.url}")
        paper_data = acm_service.import_paper(str(request.url), save_dir)
        
        # Create MongoDB document
        authors_string = paper_data.get('authors', '')
        authors_detailed = []
        if authors_string:
            # Convert comma-separated authors string to detailed array
            author_names = [name.strip() for name in authors_string.split(',') if name.strip()]
            authors_detailed = author_names  # ACM authors are simple strings
        
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
            'created_at': datetime.utcnow(),
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
        result = db.papers.insert_one(paper_doc)
        paper_id = str(result.inserted_id)
        
        logger.info(f"Successfully imported ACM paper with ID: {paper_id}")
        
        return {
            'success': True,
            'paper_id': paper_id,
            'title': paper_doc['title'],
            'authors': paper_doc['authors'],
            'doi': paper_doc.get('doi'),
            'year': paper_doc.get('year'),
            'venue': paper_doc.get('venue'),
            'pdf_path': paper_doc.get('pdf_path'),
            'message': f"Successfully imported paper from ACM"
        }
        
    except ValueError as e:
        logger.error(f"Invalid ACM URL: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error importing ACM paper: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to import paper: {str(e)}")

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