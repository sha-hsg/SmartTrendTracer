"""
ACL Anthology import API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any
from pathlib import Path
import logging
from datetime import datetime
from app.database.mongodb import get_database
from bson import ObjectId
import hashlib
import os

from app.services.acl_anthology_service import acl_anthology_service
from app.services.pdf_processor_service import PDFProcessorService
from app.services.paper_analysis_service import PaperAnalysisService

# MongoDB connection
db = get_database()

logger = logging.getLogger(__name__)
router = APIRouter()

class ACLAnthologyImportRequest(BaseModel):
    """Request model for ACL Anthology import"""
    url: HttpUrl
    process_pdf: bool = True  # Whether to process PDF after import
    add_tags: Optional[list[str]] = None  # Optional tags to add

class ACLAnthologyParseRequest(BaseModel):
    """Request model for parsing ACL Anthology URL"""
    url: HttpUrl

@router.post("/parse")
async def parse_acl_anthology_url(request: ACLAnthologyParseRequest) -> Dict[str, Any]:
    """
    Parse an ACL Anthology URL to extract metadata without importing
    
    This endpoint is useful for previewing what will be imported
    """
    try:
        url = str(request.url)
        
        # Validate it's an ACL Anthology URL
        if 'aclanthology.org' not in url:
            raise HTTPException(
                status_code=400,
                detail="URL must be from aclanthology.org"
            )
        
        # Parse the URL
        metadata = acl_anthology_service.parse_acl_url(url)
        
        if not metadata:
            raise HTTPException(
                status_code=404,
                detail="Could not extract metadata from ACL Anthology page"
            )
        
        return {
            "success": True,
            "metadata": metadata,
            "pdf_url": metadata.get('pdf_url'),
            "message": f"Successfully parsed paper: {metadata.get('title', 'Unknown')}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error parsing ACL Anthology URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import")
async def import_acl_anthology_paper(
    request: ACLAnthologyImportRequest,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    Import a paper from ACL Anthology URL
    
    This will:
    1. Parse the ACL Anthology page for metadata
    2. Download the PDF
    3. Create a database entry
    4. Optionally process the PDF for full text extraction
    """
    try:
        url = str(request.url)
        
        # Validate URL
        if 'aclanthology.org' not in url:
            raise HTTPException(
                status_code=400,
                detail="URL must be from aclanthology.org"
            )
        
        # Check if paper already exists by URL
        existing = db.papers.find_one({
            '$or': [
                {'pdf_url': url},
                {'pdf_url': url.replace('http://', 'https://')}
            ]
        })
        
        if existing:
            return {
                "success": False,
                "message": "Paper already exists in database",
                "paper_id": str(existing['_id']),
                "existing": True
            }
        
        # Set up save directory
        save_dir = Path("data/papers")
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Import the paper
        logger.info(f"Importing ACL Anthology paper from: {url}")
        paper_data = acl_anthology_service.import_paper(url, save_dir)
        
        # Debug logging
        logger.info(f"Paper data authors: {paper_data.get('authors', 'NOT FOUND')}")
        logger.info(f"Authors type: {type(paper_data.get('authors'))}")
        
        # Create MongoDB document for paper
        paper_doc = {
            'title': paper_data['title'],
            'authors': paper_data['authors'],
            'abstract': paper_data['abstract'],
            'pdf_path': paper_data['pdf_path'],
            'pdf_url': paper_data['pdf_url'],
            'doi': paper_data.get('doi'),
            'conference': paper_data.get('conference'),
            'journal': paper_data.get('proceedings'),  # Some ACL papers may be in journals
            'publication_date': paper_data.get('publication_date'),  # Canonical field name for papers
            'created_at': datetime.utcnow(),
            'processed': False,
            'source': 'acl_anthology',
            'import_source': 'acl',  # Track import source type
            'import_url': paper_data['pdf_url']  # Store original import URL
        }
        
        # Store additional metadata in appropriate fields
        if paper_data.get('pages'):
            # Extract page count if possible
            pages = paper_data['pages']
            if '-' in pages:
                try:
                    start, end = pages.split('-')
                    paper_doc['page_count'] = int(end) - int(start) + 1
                except:
                    pass
        
        # Store anthology ID in a searchable field
        if paper_data.get('source_id'):
            # Store ACL ID with prefix to distinguish
            paper_doc['acl_anthology_id'] = f"acl:{paper_data['source_id']}"
        
        # Parse authors into structured format if they're provided as a string
        if paper_doc['authors'] and isinstance(paper_doc['authors'], str):
            author_names = [name.strip() for name in paper_doc['authors'].split(',')]
            paper_doc['authors_list'] = [
                {'name': name, 'position': i} 
                for i, name in enumerate(author_names) if name
            ]
            logger.info(f"Created {len(author_names)} author entries for paper")
        
        # Debug logging before save
        logger.info(f"Paper authors before save: {paper_doc.get('authors', 'NOT FOUND')}")
        
        # Insert paper into MongoDB
        result = db.papers.insert_one(paper_doc)
        paper_id = str(result.inserted_id)
        
        # Debug logging after save
        logger.info(f"Paper saved with ID: {paper_id}")
        
        # Add tags if provided
        if request.add_tags:
            # Add tags to tag_instances collection
            tag_instances = []
            for tag_name in request.add_tags:
                tag_instances.append({
                    'content_type': 'paper',
                    'content_id': paper_id,
                    'tag': tag_name,
                    'created_at': datetime.utcnow()
                })
            if tag_instances:
                db.tag_instances.insert_many(tag_instances)
                logger.info(f"Added {len(tag_instances)} tags to paper {paper_id}")
        
        # Process PDF in background if requested
        if request.process_pdf:
            background_tasks.add_task(
                process_pdf_background,
                paper_id,
                paper_doc['pdf_path']
            )
        
        return {
            "success": True,
            "message": f"Successfully imported paper: {paper_doc['title']}",
            "paper_id": paper_id,
            "paper": {
                "id": paper_id,
                "title": paper_doc['title'],
                "authors": paper_doc['authors'],
                "abstract": paper_doc['abstract'],
                "conference": paper_doc.get('conference'),
                "doi": paper_doc.get('doi'),
                "pdf_path": paper_doc['pdf_path'],
                "source": "acl_anthology",
                "processing": request.process_pdf
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing ACL Anthology paper: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-import")
async def batch_import_acl_papers(
    urls: list[str],
    process_pdfs: bool = True,
    background_tasks: BackgroundTasks = None,
) -> Dict[str, Any]:
    """
    Import multiple ACL Anthology papers in batch
    """
    results = []
    successful = 0
    failed = 0
    skipped = 0
    
    for url in urls:
        try:
            # Check if already exists in MongoDB
            existing = db.papers.find_one({
                '$or': [
                    {'pdf_url': url},
                    {'pdf_url': url.replace('http://', 'https://')}
                ]
            })
            
            if existing:
                results.append({
                    "url": url,
                    "status": "skipped",
                    "message": "Already exists",
                    "paper_id": str(existing['_id'])
                })
                skipped += 1
                continue
            
            # Import the paper
            request = ACLAnthologyImportRequest(
                url=url,
                process_pdf=process_pdfs
            )
            
            result = await import_acl_anthology_paper(
                request,
                background_tasks
            )
            
            results.append({
                "url": url,
                "status": "success",
                "paper_id": result.get("paper_id")
            })
            successful += 1
            
        except Exception as e:
            logger.error(f"Failed to import {url}: {e}")
            results.append({
                "url": url,
                "status": "failed",
                "error": str(e)
            })
            failed += 1
    
    return {
        "total": len(urls),
        "successful": successful,
        "failed": failed,
        "skipped": skipped,
        "results": results
    }

def process_pdf_background(paper_id: str, pdf_path: str):
    """
    Background task to process PDF and extract content
    """
    try:
        # Get MongoDB connection for background task
        from bson import ObjectId
        db_bg = get_database()
        
        # Get the paper from MongoDB
        paper = db_bg.papers.find_one({'_id': ObjectId(paper_id)})
        if not paper:
            logger.error(f"Paper {paper_id} not found for processing")
            return
        
        # Process the PDF
        processor = PDFProcessorService()
        success = processor.process_paper(paper_id)
        
        if success:
            logger.info(f"Successfully processed PDF for paper {paper_id}")
            
            # Update paper as processed
            db_bg.papers.update_one(
                {'_id': ObjectId(paper_id)},
                {'$set': {'processed': True}}
            )
            
            # Run analysis if available
            try:
                analysis_service = PaperAnalysisService()
                # Pass MongoDB connection to analysis service
                analysis_service.analyze_paper(paper_id, db=db_bg)
                logger.info(f"Successfully analyzed paper {paper_id}")
            except Exception as e:
                logger.warning(f"Could not analyze paper {paper_id}: {e}")
        else:
            logger.error(f"Failed to process PDF for paper {paper_id}")
        
    except Exception as e:
        logger.error(f"Error in background PDF processing for paper {paper_id}: {e}")

@router.get("/validate-url")
async def validate_acl_url(url: str) -> Dict[str, Any]:
    """
    Validate if a URL is a valid ACL Anthology paper URL
    """
    try:
        # Check if it's an ACL Anthology URL
        if 'aclanthology.org' not in url:
            return {
                "valid": False,
                "message": "Not an ACL Anthology URL"
            }
        
        # Try to parse it
        try:
            metadata = acl_anthology_service.parse_acl_url(url)
            return {
                "valid": True,
                "message": "Valid ACL Anthology paper URL",
                "title": metadata.get('title', 'Unknown'),
                "authors": metadata.get('authors', [])
            }
        except:
            return {
                "valid": False,
                "message": "Could not parse ACL Anthology page"
            }
            
    except Exception as e:
        return {
            "valid": False,
            "message": str(e)
        }
