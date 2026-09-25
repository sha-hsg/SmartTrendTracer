"""
ArXiv API endpoints
"""

from app.paths import ARXIV_PAPERS_DIR_REL
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List
import logging

from ..services.arxiv_import_service import get_arxiv_service
from ..services.pdf_processor_service import get_pdf_processor_service
from app.repositories import arxiv_queries as queries
from app.repositories import papers as papers_repo

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
        arxiv_dir = ARXIV_PAPERS_DIR_REL
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

            try:
                paper_id = papers_repo.save_arxiv_import(result)
                response.paper_id = paper_id
                logger.info(f"Paper stored in MongoDB: {paper_id}")

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
                    try:
                        # Update paper with processed content
                        update_result = queries.papers_update_one__import_arxiv_paper(paper_id, process_result)
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
