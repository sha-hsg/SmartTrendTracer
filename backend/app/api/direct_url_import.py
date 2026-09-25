"""
Direct URL import API endpoints for importing PDFs from any URL
"""
from app.paths import PAPERS_DIR_REL
import asyncio

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
from pathlib import Path
import logging
from datetime import datetime, timezone
from app.database.mongodb import get_database
import hashlib
import os
import requests
from urllib.parse import urlparse, unquote

# MongoDB connection
db = get_database()

logger = logging.getLogger(__name__)
router = APIRouter()

class DirectURLImportRequest(BaseModel):
    """Request model for Direct URL import"""
    url: HttpUrl
    title: str
    authors: Optional[str] = None
    add_tags: Optional[List[str]] = None

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to remove special characters"""
    # Remove or replace special characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    # Limit length
    if len(filename) > 200:
        filename = filename[:200]
    return filename

def generate_filename(url: str, title: str) -> str:
    """Generate a unique filename for the PDF"""
    # Get timestamp
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    
    # Generate hash from URL for uniqueness
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    
    # Try to get filename from URL
    parsed_url = urlparse(url)
    url_filename = unquote(os.path.basename(parsed_url.path))
    
    # If URL has a PDF filename, use it
    if url_filename and url_filename.lower().endswith('.pdf'):
        # Clean the filename
        clean_name = sanitize_filename(url_filename)
        return f"{timestamp}_{url_hash}_{clean_name}"
    else:
        # Use title to create filename
        clean_title = sanitize_filename(title)
        # Replace spaces with underscores
        clean_title = clean_title.replace(' ', '_')
        # Remove duplicate underscores
        clean_title = '_'.join(filter(None, clean_title.split('_')))
        return f"{timestamp}_{url_hash}_{clean_title}.pdf"

@router.post("/import-url")
async def import_paper_from_url(
    request: DirectURLImportRequest,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    Import a paper from a direct URL
    
    This will:
    1. Download the PDF from the URL
    2. Save it locally
    3. Create a database entry
    """
    try:
        url = str(request.url)
        
        # Check if paper already exists by URL
        existing = db.papers.find_one({'pdf_url': url})
        
        if existing:
            return {
                "success": False,
                "message": "Paper with this URL already exists in database",
                "paper_id": str(existing['_id']),
                "existing": True
            }
        
        # Set up save directory
        save_dir = PAPERS_DIR_REL
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        filename = generate_filename(url, request.title)
        pdf_path = save_dir / filename
        
        # Download the PDF without blocking the event loop
        logger.info(f"Downloading PDF from: {url}")

        def _download_pdf() -> None:
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()

            content_type = response.headers.get('Content-Type', '')
            if 'pdf' not in content_type.lower() and not url.lower().endswith('.pdf'):
                logger.warning(f"URL may not be a PDF. Content-Type: {content_type}")

            with open(pdf_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

        try:
            await asyncio.to_thread(_download_pdf)
            logger.info(f"PDF saved to: {pdf_path}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download PDF: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to download PDF from URL: {str(e)}"
            )
        
        # Create MongoDB document for paper
        paper_doc = {
            'title': request.title,
            'authors': request.authors or '',
            'pdf_path': str(pdf_path),
            'pdf_url': url,
            'created_at': datetime.now(timezone.utc),
            'processed': False,
            'source': 'direct_url',
            'import_source': 'direct',  # Track import source type
            'import_url': url,  # Store original import URL
            'paper_type': 'research',
        }
        
        # Parse authors into structured format if provided
        if request.authors:
            author_names = [name.strip() for name in request.authors.split(',')]
            paper_doc['authors_list'] = [
                {'name': name, 'position': i} 
                for i, name in enumerate(author_names) if name
            ]
        
        # Insert paper into MongoDB
        result = db.papers.insert_one(paper_doc)
        paper_id = str(result.inserted_id)
        
        logger.info(f"Paper saved with ID: {paper_id}")
        
        # Add tags if provided — via concept service so concept_id is set
        # (raw inserts into tag_instances create invisible orphans)
        if request.add_tags:
            from app.services.concept_only_tag_service import ConceptOnlyTagService
            concept_service = ConceptOnlyTagService()

            added_count = 0
            for tag_name in request.add_tags:
                if not tag_name or not tag_name.strip():
                    continue
                try:
                    success, concept_id = concept_service.add_tag(
                        content_type='paper',
                        content_id=paper_id,
                        text=tag_name.strip(),
                        preserve_display_name=True
                    )
                    if success:
                        added_count += 1
                        db.papers.update_one(
                            {'_id': result.inserted_id},
                            {'$addToSet': {'concept_ids': concept_id}}
                        )
                except Exception as tag_err:
                    logger.warning(f"Failed to add tag '{tag_name}' to paper {paper_id}: {tag_err}")

            logger.info(f"Added {added_count} concept tags to paper {paper_id}")
        
        return {
            "success": True,
            "message": f"Successfully imported paper: {request.title}",
            "paper_id": paper_id,
            "paper": {
                "id": paper_id,
                "title": request.title,
                "authors": request.authors or '',
                "pdf_path": str(pdf_path),
                "pdf_url": url,
                "source": "direct_url"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing paper from URL: {e}")
        # Clean up downloaded file if it exists
        if 'pdf_path' in locals() and pdf_path.exists():
            try:
                os.remove(pdf_path)
            except Exception:
                pass
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/validate-url")
async def validate_pdf_url(url: str) -> Dict[str, Any]:
    """
    Validate if a URL points to a PDF file
    """
    try:
        # Basic URL validation
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return {
                "valid": False,
                "message": "Invalid URL format"
            }
        
        # Check if URL ends with .pdf
        if url.lower().endswith('.pdf'):
            return {
                "valid": True,
                "message": "URL appears to be a PDF file",
                "confidence": "high"
            }
        
        # Try to HEAD request to check content type
        try:
            response = requests.head(url, timeout=5, allow_redirects=True)
            content_type = response.headers.get('Content-Type', '')
            
            if 'pdf' in content_type.lower():
                return {
                    "valid": True,
                    "message": "URL points to a PDF file",
                    "confidence": "high",
                    "content_type": content_type
                }
            else:
                return {
                    "valid": False,
                    "message": f"URL does not appear to be a PDF (Content-Type: {content_type})",
                    "content_type": content_type
                }
        except Exception:
            # Can't determine from HEAD, but URL might still be valid
            return {
                "valid": True,
                "message": "Cannot verify URL content type, but it may still be valid",
                "confidence": "low"
            }
            
    except Exception as e:
        return {
            "valid": False,
            "message": str(e)
        }
