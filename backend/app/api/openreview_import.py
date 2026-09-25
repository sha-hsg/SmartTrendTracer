"""
OpenReview paper import API endpoints
"""
from app.paths import PAPERS_DIR_REL
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
import logging
from datetime import datetime, timezone
from pathlib import Path
from bson import ObjectId
from app.database.mongodb import get_database

from app.services.openreview_service import OpenReviewService
from app.services.pdf_processor_service import PDFProcessorService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/openreview")

# MongoDB connection
db = get_database()

# Initialize services
openreview_service = OpenReviewService()
pdf_processor = PDFProcessorService()

class OpenReviewImportRequest(BaseModel):
    """Request model for OpenReview import"""
    url: str
    add_tags: Optional[List[str]] = None
    process_pdf: Optional[bool] = True

class OpenReviewValidateRequest(BaseModel):
    """Request model for URL validation"""
    url: str

@router.post("/validate-url")
async def validate_openreview_url(request: OpenReviewValidateRequest):
    """
    Validate an OpenReview URL and extract forum ID
    """
    try:
        forum_id = openreview_service.extract_forum_id_from_url(request.url)
        
        if not forum_id:
            return {
                "valid": False,
                "error": "Invalid OpenReview URL format"
            }
        
        return {
            "valid": True,
            "forum_id": forum_id,
            "normalized_url": f"https://openreview.net/forum?id={forum_id}"
        }
        
    except Exception as e:
        logger.error(f"Error validating OpenReview URL: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/import")
async def import_openreview_paper(
    request: OpenReviewImportRequest,
    background_tasks: BackgroundTasks
):
    """
    Import a paper from OpenReview
    """
    try:
        logger.info(f"Importing OpenReview paper from: {request.url}")
        
        # Extract forum ID
        forum_id = openreview_service.extract_forum_id_from_url(request.url)
        if not forum_id:
            raise HTTPException(status_code=400, detail="Invalid OpenReview URL")
        
        # Check if paper already exists
        existing_paper = db.papers.find_one({"openreview_id": forum_id})
        if existing_paper:
            return {
                "success": False,
                "existing": True,
                "paper_id": str(existing_paper["_id"]),
                "message": "Paper already exists in database"
            }
        
        # Fetch metadata
        metadata = openreview_service.fetch_paper_metadata(forum_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="Failed to fetch paper metadata")
        
        # Prepare paper document
        # Process authors to match expected format
        author_list = metadata.get("authors", [])
        authors_detailed = []
        author_names = []
        
        for idx, author in enumerate(author_list):
            # Create detailed author entry
            author_detail = {
                "name": author,
                "position": idx,
                "affiliation": "",
                "email": "",
                "is_corresponding": False
            }
            authors_detailed.append(author_detail)
            author_names.append(author)
        
        paper_doc = {
            "title": metadata["title"],
            "authors": ", ".join(author_names),  # Comma-separated string for compatibility
            "authors_detailed": authors_detailed,  # Detailed array for structured data
            "abstract": metadata.get("abstract", ""),
            "year": metadata.get("year"),
            "venue": metadata.get("venue", ""),
            "openreview_id": forum_id,
            "openreview_url": metadata["openreview_url"],
            "keywords": metadata.get("keywords", []),
            "tldr": metadata.get("tldr", ""),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "source": "openreview",
            "import_source": "openreview",  # Track import source type
            "import_url": request.url,  # Store original import URL
            "paper_type": "research",
            "metadata": {
                "supplementary": metadata.get("supplementary", []),
                "import_date": datetime.now(timezone.utc).isoformat()
            }
        }
        
        # Add publication date if available
        if metadata.get("publication_date"):
            try:
                # Parse the ISO format date string
                pub_date = datetime.fromisoformat(metadata["publication_date"].replace('Z', '+00:00'))
                paper_doc["publication_date"] = pub_date
            except Exception:
                # If parsing fails, store as string
                paper_doc["publication_date"] = metadata["publication_date"]
        
        # Download and save PDF if available
        if metadata.get("pdf_url"):
            try:
                # Generate filename
                safe_title = ''.join(c for c in metadata["title"][:50] if c.isalnum() or c in ' -_')
                pdf_filename = f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{forum_id[:8]}_{safe_title}.pdf"
                pdf_path = PAPERS_DIR_REL / pdf_filename
                
                # Download PDF
                if openreview_service.download_pdf(metadata["pdf_url"], pdf_path):
                    paper_doc["pdf_path"] = str(pdf_path)
                    paper_doc["has_pdf"] = True
                    logger.info(f"PDF downloaded to: {pdf_path}")
                else:
                    logger.warning("Failed to download PDF")
                    
            except Exception as e:
                logger.error(f"Error downloading PDF: {e}")
        
        # Add BibTeX
        if "bibtex" not in metadata:
            metadata["bibtex"] = openreview_service.generate_bibtex(metadata)
        paper_doc["bibtex"] = metadata["bibtex"]
        
        # Insert paper into database
        result = db.papers.insert_one(paper_doc)
        paper_id = str(result.inserted_id)
        
        logger.info(f"Successfully imported OpenReview paper with ID: {paper_id}")
        
        # Add tags if provided
        if request.add_tags:
            for tag in request.add_tags:
                db.tag_instances.insert_one({
                    "tag": tag,
                    "content_type": "paper",
                    "content_id": paper_id,
                    "created_at": datetime.now(timezone.utc)
                })
        
        # Process PDF in background if requested and PDF exists
        if request.process_pdf and paper_doc.get("pdf_path"):
            background_tasks.add_task(
                process_pdf_background,
                paper_id,
                paper_doc["pdf_path"]
            )
        
        return {
            "success": True,
            "paper_id": paper_id,
            "title": metadata["title"],
            "authors": metadata.get("authors", []),
            "venue": metadata.get("venue", ""),
            "year": metadata.get("year"),
            "has_pdf": paper_doc.get("has_pdf", False),
            "keywords": metadata.get("keywords", []),
            "supplementary": len(metadata.get("supplementary", [])),
            "message": "Paper imported successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing OpenReview paper: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metadata/{forum_id}")
async def get_openreview_metadata(forum_id: str):
    """
    Get metadata for an OpenReview paper by forum ID
    """
    try:
        metadata = openreview_service.fetch_paper_metadata(forum_id)
        
        if not metadata:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        return metadata
        
    except Exception as e:
        logger.error(f"Error fetching OpenReview metadata: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def process_pdf_background(paper_id: str, pdf_path: str):
    """
    Background task to process PDF with Marker
    """
    try:
        logger.info(f"Processing PDF for paper {paper_id} in background")

        # Process with Marker preferred (falls back per PDFProcessorService order)
        result = pdf_processor.process_pdf(
            pdf_path,
            prefer_method="marker",
            mongo_paper_id=paper_id
        )

        if result and result.get("success"):
            # Update paper with processed content
            update_data = {
                "content": result.get("markdown", ""),
                "processed": True,
                "processor_used": result.get("method_used", "unknown"),
                "processed_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }

            db.papers.update_one(
                {"_id": ObjectId(paper_id)},
                {"$set": update_data}
            )

            logger.info(f"PDF processing completed for paper {paper_id}")
        else:
            logger.error(f"PDF processing failed for paper {paper_id}: {result.get('error') if result else 'no result'}")

    except Exception as e:
        logger.error(f"Error in background PDF processing: {e}")
