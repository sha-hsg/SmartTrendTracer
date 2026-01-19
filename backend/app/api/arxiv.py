"""
ArXiv API endpoints
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List
import logging
import os
import re
from pathlib import Path

from ..services.arxiv_import_service import get_arxiv_service

# ArXiv ID validation patterns
ARXIV_ID_PATTERNS = [
    r'^(\d{4}\.\d{4,5})(v\d+)?$',  # New format: 2301.12345 or 2301.12345v1
    r'^([a-z\-]+/\d{7})(v\d+)?$',  # Old format: quant-ph/0301023
    r'^([a-z\-]+\.\w+/\d{7})(v\d+)?$',  # Old format with subcategory: cond-mat.soft/0301023
]

def validate_arxiv_id(arxiv_id: str) -> tuple[bool, str]:
    """
    Validate ArXiv ID format and return (is_valid, cleaned_id or error_message).

    Valid formats:
    - 2301.12345 (new format, 5 digits)
    - 2301.1234 (new format, 4 digits for older papers)
    - 2301.12345v1 (with version)
    - quant-ph/0301023 (old format)
    - hep-th/9901001v2 (old format with version)
    """
    # Clean the ID
    cleaned = arxiv_id.strip()

    # Remove common URL prefixes
    url_prefixes = [
        'https://arxiv.org/abs/',
        'http://arxiv.org/abs/',
        'https://arxiv.org/pdf/',
        'http://arxiv.org/pdf/',
        'arxiv.org/abs/',
        'arxiv.org/pdf/',
        'arxiv:',
    ]
    for prefix in url_prefixes:
        if cleaned.lower().startswith(prefix.lower()):
            cleaned = cleaned[len(prefix):]
            break

    # Remove .pdf suffix if present
    if cleaned.endswith('.pdf'):
        cleaned = cleaned[:-4]

    # Validate against patterns
    for pattern in ARXIV_ID_PATTERNS:
        if re.match(pattern, cleaned, re.IGNORECASE):
            return True, cleaned

    return False, f"Invalid ArXiv ID format: '{arxiv_id}'. Expected formats: '2301.12345', '2301.12345v1', or 'quant-ph/0301023'"
from ..services.pdf_processor_service import get_pdf_processor_service
from app.database.mongodb import get_database
from bson import ObjectId
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(tags=["arxiv"])

class ArXivImportRequest(BaseModel):
    """Request model for importing ArXiv paper"""
    url_or_id: str = Field(..., description="ArXiv URL or paper ID (e.g., '2301.12345' or 'https://arxiv.org/abs/2301.12345')")
    process_pdf: bool = Field(False, description="Whether to process PDF to markdown immediately (default: False, use Process PDF button later)")
    add_to_database: bool = Field(True, description="Whether to add paper to database")

class ArXivSearchRequest(BaseModel):
    """Request model for searching ArXiv"""
    query: str = Field(..., description="Search query")
    max_results: int = Field(10, ge=1, le=50, description="Maximum number of results")

class ArXivImportResponse(BaseModel):
    """Response model for ArXiv import"""
    success: bool
    arxiv_id: Optional[str] = None
    title: Optional[str] = None
    authors: Optional[List[str]] = None
    abstract: Optional[str] = None
    pdf_path: Optional[str] = None
    markdown_content: Optional[str] = None
    paper_id: Optional[str] = None
    error: Optional[str] = None

@router.post("/import", response_model=ArXivImportResponse)
async def import_arxiv_paper(
    request: ArXivImportRequest,
    background_tasks: BackgroundTasks
):
    """
    Import a paper from ArXiv

    This endpoint:
    1. Validates the ArXiv URL/ID format
    2. Fetches metadata from ArXiv API
    3. Downloads the PDF
    4. Optionally processes it to markdown
    5. Optionally adds it to the database
    """
    try:
        # Get services first
        arxiv_service = get_arxiv_service()

        # Validate ArXiv ID format using service method
        validated_id = arxiv_service.extract_arxiv_id(request.url_or_id)
        if not validated_id:
            logger.warning(f"Invalid ArXiv ID format: {request.url_or_id}")
            return ArXivImportResponse(
                success=False,
                error="Invalid ArXiv ID format. Expected format: 2301.12345 or arxiv.org URL"
            )

        logger.info(f"Validated ArXiv ID: {validated_id}")
        
        # Create permanent directory for ArXiv PDFs
        import os
        from pathlib import Path
        arxiv_dir = Path("data/papers/arxiv")
        arxiv_dir.mkdir(parents=True, exist_ok=True)
        
        # Import from ArXiv with permanent directory (using validated ID)
        result = arxiv_service.import_paper(validated_id, download_dir=str(arxiv_dir))
        
        if not result['success']:
            return ArXivImportResponse(
                success=False,
                error=result.get('error', 'Failed to import from ArXiv')
            )
        
        response = ArXivImportResponse(
            success=True,
            arxiv_id=result['arxiv_id'],
            title=result['metadata']['title'],
            authors=result['metadata']['authors'],
            abstract=result['metadata']['abstract'],
            pdf_path=result['pdf_path']
        )
        
        # Add to database first if requested (so we have paper_id for image extraction)
        paper_id = None
        if request.add_to_database:
            db = get_database()

            try:
                # Check if paper already exists
                existing = db.papers.find_one({
                    'arxiv_id': result['arxiv_id']
                })
                
                if existing:
                    paper_id = str(existing['_id'])
                    response.paper_id = paper_id
                    logger.info(f"Paper already exists in database: {paper_id}")
                else:
                    # Create new paper entry with PDF path immediately
                    paper_data = {
                        'title': result['metadata']['title'],
                        'authors': ', '.join(result['metadata']['authors']),
                        'authors_detailed': [{'name': author, 'affiliation': '', 'email': ''} for author in result['metadata']['authors']],
                        'abstract': result['metadata']['abstract'],
                        'arxiv_id': result['arxiv_id'],
                        'pdf_url': result['metadata']['pdf_url'],
                        'published_date': result['metadata'].get('published'),
                        'categories': result['metadata'].get('categories', []),
                        'content': '',  # Will be filled after processing
                        'pdf_path': result['pdf_path'],  # PDF is immediately available
                        'processed': False,  # Not processed yet
                        'processor_used': None,
                        'created_at': datetime.utcnow(),
                        'source': 'arxiv',
                        'url': f"https://arxiv.org/abs/{result['arxiv_id']}",
                        'import_source': 'arxiv',  # Track import source type
                        'import_url': f"https://arxiv.org/abs/{result['arxiv_id']}"  # Store original import URL
                    }
                    
                    # Insert into MongoDB
                    insert_result = db.papers.insert_one(paper_data)
                    paper_id = str(insert_result.inserted_id)
                    response.paper_id = paper_id
                    logger.info(f"Added paper to MongoDB: {paper_id}")
                    
            except Exception as e:
                logger.error(f"Failed to add paper to database: {e}")
        
        # Process PDF if explicitly requested (defaults to False)
        if request.process_pdf and result['pdf_path']:
            logger.info(f"Processing PDF (explicitly requested): {result['pdf_path']}")
            pdf_service = get_pdf_processor_service()
            
            # Process with MinerU/Marker and extract images
            process_result = pdf_service.process_pdf(result['pdf_path'], paper_id=paper_id)
            
            if process_result['success']:
                response.markdown_content = process_result['markdown']
                logger.info(f"Successfully processed PDF with {process_result['method_used']}")
                
                # Update paper with processed content if we have paper_id
                if paper_id:
                    db = get_database()
                    try:
                        # Update paper with processed content
                        update_result = db.papers.update_one(
                            {'_id': ObjectId(paper_id)},
                            {'$set': {
                                'content': process_result['markdown'],
                                'processed': True,
                                'processor_used': process_result.get('method_used', 'unknown'),
                                'processed_at': datetime.utcnow()
                            }}
                        )
                        if update_result.modified_count > 0:
                            logger.info(f"Updated paper {paper_id} with processed content")
                        else:
                            logger.warning(f"No paper updated for id {paper_id}")
                    except Exception as e:
                        logger.error(f"Failed to update paper with content: {e}")
                    finally:
                        pass
            else:
                logger.warning(f"Failed to process PDF: {process_result.get('error')}")
        else:
            logger.info(f"PDF processing not requested (process_pdf={request.process_pdf}), PDF ready at: {result.get('pdf_path')}")
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to import ArXiv paper: {e}")
        return ArXivImportResponse(
            success=False,
            error=str(e)
        )

@router.post("/search")
async def search_arxiv(request: ArXivSearchRequest):
    """
    Search for papers on ArXiv
    
    Returns a list of papers matching the search query
    """
    try:
        arxiv_service = get_arxiv_service()
        
        papers = arxiv_service.search_papers(
            query=request.query,
            max_results=request.max_results
        )
        
        if papers is None:
            raise HTTPException(status_code=500, detail="Failed to search ArXiv")
        
        return {
            'success': True,
            'query': request.query,
            'results': papers,
            'count': len(papers)
        }
        
    except Exception as e:
        logger.error(f"Failed to search ArXiv: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/validate/{arxiv_id}")
async def validate_arxiv_id(arxiv_id: str):
    """
    Validate an ArXiv ID and fetch basic metadata
    
    Args:
        arxiv_id: ArXiv paper ID (e.g., '2301.12345')
    """
    try:
        arxiv_service = get_arxiv_service()
        
        # Validate ID format
        extracted_id = arxiv_service.extract_arxiv_id(arxiv_id)
        if not extracted_id:
            return {
                'valid': False,
                'error': 'Invalid ArXiv ID format'
            }
        
        # Fetch metadata to verify it exists
        metadata = arxiv_service.fetch_metadata(extracted_id)
        if not metadata:
            return {
                'valid': False,
                'error': 'Paper not found on ArXiv'
            }
        
        return {
            'valid': True,
            'arxiv_id': extracted_id,
            'title': metadata['title'],
            'authors': metadata['authors'],
            'published': metadata['published']
        }
        
    except Exception as e:
        logger.error(f"Failed to validate ArXiv ID: {e}")
        return {
            'valid': False,
            'error': str(e)
        }

@router.post("/batch-import")
async def batch_import_arxiv(
    arxiv_ids: List[str],
    background_tasks: BackgroundTasks
):
    """
    Import multiple papers from ArXiv
    
    Args:
        arxiv_ids: List of ArXiv IDs or URLs
    """
    results = []
    
    for arxiv_id in arxiv_ids:
        try:
            # Import each paper (without auto-processing)
            request = ArXivImportRequest(
                url_or_id=arxiv_id,
                process_pdf=False,  # Don't auto-process, user must click "Process PDF" button
                add_to_database=True
            )
            
            result = await import_arxiv_paper(request, background_tasks)
            results.append(result.dict())
            
        except Exception as e:
            logger.error(f"Failed to import {arxiv_id}: {e}")
            results.append({
                'success': False,
                'arxiv_id': arxiv_id,
                'error': str(e)
            })
    
    # Summary
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    return {
        'total': len(results),
        'successful': len(successful),
        'failed': len(failed),
        'results': results
    }
