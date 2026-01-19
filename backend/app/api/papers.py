"""
API endpoints for research papers
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse
from typing import List, Optional, Union
from datetime import datetime, date
from pathlib import Path
import logging

from app.models.papers import Paper, PaperAuthor, PaperSection, PaperTag, PaperSnippet, PaperReference, PaperAnalysis
from app.services.paper_service import PaperService
from app.services.paper_rag_service import PaperRAGService
from app.services.paper_tag_service import PaperTagService
from app.services.unified_tag_service import UnifiedTagService
from app.services.tag_concept_v2_service import get_tag_concept_v2_service
from app.services.pdf_processor_service import get_pdf_processor_service
from app.services.paper_author_extraction_service import PaperAuthorExtractionService
from app.services.paper_analysis_service import PaperAnalysisService
from app.services.grobid_service import GROBIDService
from app.services.vector_store_openai import get_vector_store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/papers", tags=["papers"])

# Initialize services
paper_service = PaperService()
rag_service = PaperRAGService()
tag_service = PaperTagService()
author_extraction_service = PaperAuthorExtractionService()
analysis_service = PaperAnalysisService()
grobid_service = GROBIDService()

# Pydantic models
    id: int
    processor_used: Optional[str] = None
    title: str
    abstract: Optional[str]
    authors: List[dict]
    publication_date: Optional[date]
    conference: Optional[str]
    journal: Optional[str]
    arxiv_id: Optional[str]
    doi: Optional[str]
    page_count: Optional[int] = 0
    word_count: Optional[int] = 0  # Added for showing paper length
    tags: List[str]
    created_at: datetime
    processed: bool
    pdf_path: Optional[str] = None  # Added to enable PDF viewing
    processing_error: Optional[str] = None  # Added for error handling
    is_flagged: bool = False  # Added for flagging system
    flag_notes: Optional[str] = None  # Added for flag notes
    
    class Config:
        from_attributes = True

    id: int
    title: str
    message: str
    extracted_sections: int
    extracted_authors: int

    papers: List[PaperResponse]
    total: int
    page: int
    page_size: int

    tag: str
    tag_type: str = "manual"

    content: str
    page_number: Optional[int]
    annotation: Optional[str]
    category: Optional[str]

from fastapi import BackgroundTasks

@router.post("/upload", response_model=PaperUploadResponse)
async def upload_paper(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """Upload and process a PDF research paper (async)"""
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Check file size (limit to 50MB)
    contents = await file.read()
    if len(contents) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 50MB limit")
    
    try:
        # Save the PDF file
        pdf_path = paper_service.save_pdf_file(contents, file.filename)
        
        # Extract basic info from filename (no PDF processing)
        filename_metadata = paper_service.extract_metadata_from_filename(file.filename)
        
        # Create paper record immediately with basic info
        paper = Paper(
            title=filename_metadata.get('title', file.filename.replace('.pdf', '').replace('_', ' ')),
            authors='',  # Will be filled when processed
            abstract='PDF uploaded. Click "Process PDF" to extract content with Marker/MinerU.',
            content='',  # Will be filled by processing
            pdf_path=pdf_path,
            processed=False
        )
        db.add(paper)
        db.commit()
        db.refresh(paper)
        
        # NO LONGER AUTO-PROCESSING - User must click "Process PDF" button
        # background_tasks.add_task(process_pdf_complete, paper.id, pdf_path)
        
        return PaperUploadResponse(
            id=paper.id,
            title=paper.title,
            message="Paper uploaded successfully. Use 'Process PDF' button to extract content.",
            extracted_sections=0,
            extracted_authors=0
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error uploading paper: {e}")
        raise HTTPException(status_code=500, detail=f"Error uploading paper: {str(e)}")

def process_pdf_complete(paper_id: int, pdf_path: str, prefer_processor: str = None):
    """Complete PDF processing in background
    
    Args:
        paper_id: ID of the paper to process
        pdf_path: Path to the PDF file
        prefer_processor: Optional preferred processor ('marker' or 'mineru')
    """
    from ..services.pdf_processor_service import get_pdf_processor_service
    
    logger.info(f"Processing PDF for paper {paper_id} with preferred processor: {prefer_processor}")
    
    try:
        # Get the paper record
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            logger.error(f"Paper {paper_id} not found")
            return
        
        # Process the PDF with image extraction
        pdf_processor = get_pdf_processor_service()
        
        # Pass the preferred processor if specified
        if prefer_processor:
            process_result = pdf_processor.process_pdf(
                pdf_path, 
                prefer_method=prefer_processor,  # Use correct parameter name
                paper_id=paper_id
            )
        else:
            process_result = pdf_processor.process_pdf(pdf_path, paper_id=paper_id)
        
        if process_result["success"]:
            # Update paper with processed content
            paper.content = process_result["markdown"]
            paper.processed = True
            paper.processor_used = process_result.get("method_used", "unknown")
            
            # Update metadata if available
            if "metadata" in process_result:
                metadata = process_result["metadata"]
                if metadata.get("title") and len(metadata["title"]) > 3:
                    paper.title = metadata["title"]
                if metadata.get("abstract"):
                    paper.abstract = metadata["abstract"]
                if metadata.get("page_count"):
                    paper.page_count = metadata["page_count"]
            
            # Extract and save authors if not already present
            if not paper.author_details:
                authors = paper_service.extract_authors_from_content(process_result["markdown"])
                for i, author_data in enumerate(authors):
                    author = PaperAuthor(
                        paper_id=paper.id,
                        name=author_data["name"],
                        email=author_data.get("email"),
                        position=i
                    )
                    db.add(author)
            
            db.commit()
            logger.info(f"Successfully processed paper {paper_id} using {process_result.get('method_used')}")
            
            # Add to RAG index
            try:
                rag_service.add_paper_to_index(db, paper.id)
                logger.info(f"Added paper {paper.id} to RAG index")
            except Exception as e:
                logger.error(f"Failed to add paper to RAG index: {e}")
        else:
            # Mark as failed
            paper.processed = False
            paper.abstract = f"Processing failed: {process_result.get('error', 'Unknown error')}"
            db.commit()
            logger.error(f"Failed to process paper {paper_id}: {process_result.get('error')}")
            
    except Exception as e:
        logger.error(f"Error processing paper {paper_id}: {e}")
        try:
            paper = db.query(Paper).filter(Paper.id == paper_id).first()
            if paper:
                paper.processed = False
                paper.abstract = f"Processing error: {str(e)}"
                db.commit()
        except:
            pass
    finally:
        db.close()

@router.get("", response_model=PaperListResponse)
def get_papers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    author: Optional[str] = None,
    tag: Optional[str] = None,
    conference: Optional[str] = None,
    year: Optional[int] = None,
    affiliation: Optional[str] = None,
    processor: Optional[str] = None,
    is_flagged: Optional[bool] = None,
    # Negative filters (show papers WITHOUT these attributes)
    no_processor: bool = False,
    no_year: bool = False,
    no_conference: bool = False,
    no_affiliation: bool = False,
    use_ontology: bool = Query(True, description="Use tag ontology for hierarchical filtering"),
):
    """Get list of papers with filtering and pagination"""
    
    query = db.query(Paper)
    
    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Paper.title.ilike(search_term)) |
            (Paper.abstract.ilike(search_term))
        )
    
    if author:
        query = query.join(PaperAuthor).filter(
            PaperAuthor.name.ilike(f"%{author}%")
        )
    
    if affiliation:
        # Join with PaperAuthor if not already joined
        if not author:
            query = query.join(PaperAuthor)
        query = query.filter(
            PaperAuthor.affiliation.ilike(f"%{affiliation}%")
        )
    
    if tag:
        # Use unified tag service for consistent filtering
        unified_service = UnifiedTagService(db)
        query = unified_service.filter_papers_by_tag(query, tag, use_hierarchy=use_ontology)
        logger.info(f"Filtering papers by tag: '{tag}' (hierarchy={'enabled' if use_ontology else 'disabled'})")
    
    if conference:
        query = query.filter(Paper.conference.ilike(f"%{conference}%"))
    
    if year:
        query = query.filter(
            func.extract('year', Paper.publication_date) == year
        )
    
    if processor:
        query = query.filter(Paper.processor_used == processor)
    
    # Flag filter
    if is_flagged is not None:
        query = query.filter(Paper.is_flagged == is_flagged)
    
    # Negative filters (papers WITHOUT certain attributes)
    if no_processor:
        query = query.filter(
            (Paper.processor_used == None) | 
            (Paper.processor_used == '') |
            (Paper.processed == False)
        )
    
    if no_year:
        query = query.filter(
            Paper.publication_date == None
        )
    
    if no_conference:
        query = query.filter(
            (Paper.conference == None) | 
            (Paper.conference == '')
        )
    
    if no_affiliation:
        # Papers with no author affiliations
        query = query.outerjoin(PaperAuthor).filter(
            (PaperAuthor.affiliation == None) | 
            (PaperAuthor.affiliation == '')
        ).distinct()
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    papers = query.order_by(desc(Paper.created_at)).offset(offset).limit(page_size).all()
    
    # Format response
    paper_responses = []
    for paper in papers:
        paper_dict = {
            "id": paper.id,
            "title": paper.title,
            "abstract": paper.abstract,
            "authors": [
                {"name": a.name, "email": a.email, "affiliation": a.affiliation}
                for a in paper.author_details
            ],
            "publication_date": paper.publication_date,
            "conference": paper.conference,
            "journal": paper.journal,
            "arxiv_id": paper.arxiv_id,
            "doi": paper.doi,
            "page_count": paper.page_count,
            "word_count": paper.word_count if hasattr(paper, 'word_count') else 0,  # Include word count for display
            "tags": [t.tag for t in paper.tags],
            "created_at": paper.created_at,
            "processed": paper.processed,
            "processor_used": paper.processor_used,
            "is_flagged": paper.is_flagged if hasattr(paper, 'is_flagged') else False,
            "flag_notes": paper.flag_notes if hasattr(paper, 'flag_notes') else None
        }
        paper_responses.append(PaperResponse(**paper_dict))
    
    return PaperListResponse(
        papers=paper_responses,
        total=total,
        page=page,
        page_size=page_size
    )

@router.get("/facets")
def get_paper_facets(
    search: Optional[str] = Query(None, description="Search in title and abstract"),
    author: Optional[str] = Query(None, description="Filter by author name"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    conference: Optional[str] = Query(None, description="Filter by conference"),
    year: Optional[int] = Query(None, description="Filter by year"),
    affiliation: Optional[str] = Query(None, description="Filter by affiliation/institution"),
    processor: Optional[str] = Query(None, description="Filter by processor used"),
):
    """Get facet counts for paper filtering"""
    
    try:
        base_query = db.query(Paper)
        
        # Apply current filters to get accurate facet counts
        if search:
            search_term = f"%{search}%"
            base_query = base_query.filter(
                (Paper.title.ilike(search_term)) |
                (Paper.abstract.ilike(search_term))
            )
        
        # Get author facets
        author_facets = []
        # Always show author facets, but filter counts based on other active filters
        author_query = base_query.join(PaperAuthor)
        # Apply other filters (not author) to get correct counts
        if tag:
            unified_service = UnifiedTagService(db)
            author_query = unified_service.filter_papers_by_tag(author_query, tag, use_hierarchy=True)
        if conference:
            author_query = author_query.filter(Paper.conference.ilike(f"%{conference}%"))
        if year:
            author_query = author_query.filter(func.extract('year', Paper.publication_date) == year)
        if affiliation:
            author_query = author_query.filter(PaperAuthor.affiliation.ilike(f"%{affiliation}%"))
        if processor:
            author_query = author_query.filter(Paper.processor_used == processor)
        
        author_counts = author_query.with_entities(
            PaperAuthor.name,
            func.count(func.distinct(Paper.id)).label('count')
        ).group_by(PaperAuthor.name).order_by(desc('count')).limit(20).all()
        
        author_facets = [
            {"value": name, "count": count, "label": name}
            for name, count in author_counts
        ]
        
        # Get conference facets
        conference_facets = []
        # Always show conference facets, but filter counts based on other active filters
        conf_query = base_query
        # Apply other filters (not conference) to get correct counts
        if author:
            conf_query = conf_query.join(PaperAuthor).filter(PaperAuthor.name.ilike(f"%{author}%"))
        if affiliation:
            if author:  # Already joined
                conf_query = conf_query.filter(PaperAuthor.affiliation.ilike(f"%{affiliation}%"))
            else:
                conf_query = conf_query.join(PaperAuthor).filter(PaperAuthor.affiliation.ilike(f"%{affiliation}%"))
        if tag:
            unified_service = UnifiedTagService(db)
            conf_query = unified_service.filter_papers_by_tag(conf_query, tag, use_hierarchy=True)
        if year:
            conf_query = conf_query.filter(func.extract('year', Paper.publication_date) == year)
        if processor:
            conf_query = conf_query.filter(Paper.processor_used == processor)
        
        conf_counts = conf_query.with_entities(
            Paper.conference,
            func.count(Paper.id).label('count')
        ).filter(Paper.conference.isnot(None)).group_by(Paper.conference).order_by(desc('count')).limit(20).all()
        
        conference_facets = [
            {"value": conf, "count": count, "label": conf}
            for conf, count in conf_counts if conf
        ]
        
        # Get year facets
        year_facets = []
        # Always show year facets, but filter counts based on other active filters
        year_query = base_query
        # Apply other filters (not year) to get correct counts
        if author:
            # Join with PaperAuthor to filter by author
            year_query = year_query.join(PaperAuthor).filter(PaperAuthor.name.ilike(f"%{author}%"))
        if affiliation:
            if author:  # Already joined
                year_query = year_query.filter(PaperAuthor.affiliation.ilike(f"%{affiliation}%"))
            else:
                year_query = year_query.join(PaperAuthor).filter(PaperAuthor.affiliation.ilike(f"%{affiliation}%"))
        if tag:
            unified_service = UnifiedTagService(db)
            year_query = unified_service.filter_papers_by_tag(year_query, tag, use_hierarchy=True)
        if conference:
            year_query = year_query.filter(Paper.conference.ilike(f"%{conference}%"))
        if processor:
            year_query = year_query.filter(Paper.processor_used == processor)
        
        year_counts = year_query.with_entities(
            func.extract('year', Paper.publication_date).label('year'),
            func.count(func.distinct(Paper.id)).label('count')
        ).filter(Paper.publication_date.isnot(None)).group_by('year').order_by(desc('year')).all()
        
        year_facets = [
            {"value": int(year_val), "count": count, "label": str(int(year_val))}
            for year_val, count in year_counts if year_val
        ]
        
        # Get tag facets
        tag_facets = []
        # Always show tag facets, but filter counts based on other active filters
        tag_query = base_query.join(PaperTag)
        # Apply other filters (not tag) to get correct counts  
        if author:
            tag_query = tag_query.join(PaperAuthor).filter(PaperAuthor.name.ilike(f"%{author}%"))
        if affiliation:
            if author:  # Already joined
                tag_query = tag_query.filter(PaperAuthor.affiliation.ilike(f"%{affiliation}%"))
            else:
                tag_query = tag_query.join(PaperAuthor).filter(PaperAuthor.affiliation.ilike(f"%{affiliation}%"))
        if conference:
            tag_query = tag_query.filter(Paper.conference.ilike(f"%{conference}%"))
        if year:
            tag_query = tag_query.filter(func.extract('year', Paper.publication_date) == year)
        if processor:
            tag_query = tag_query.filter(Paper.processor_used == processor)
        
        tag_counts = tag_query.with_entities(
            PaperTag.tag,
            func.count(func.distinct(Paper.id)).label('count')
        ).group_by(PaperTag.tag).order_by(desc('count')).limit(30).all()
        
        tag_facets = [
            {"value": tag_name, "count": count, "label": tag_name}
            for tag_name, count in tag_counts
        ]
        
        # Get affiliation/institution facets
        affiliation_facets = []
        # Always show affiliation facets, but filter counts based on other active filters  
        affil_query = base_query.join(PaperAuthor)
        # Apply other filters (not affiliation) to get correct counts
        if author:
            affil_query = affil_query.filter(PaperAuthor.name.ilike(f"%{author}%"))
        if tag:
            unified_service = UnifiedTagService(db)
            affil_query = unified_service.filter_papers_by_tag(affil_query, tag, use_hierarchy=True)
        if conference:
            affil_query = affil_query.filter(Paper.conference.ilike(f"%{conference}%"))
        if year:
            affil_query = affil_query.filter(func.extract('year', Paper.publication_date) == year)
        if processor:
            affil_query = affil_query.filter(Paper.processor_used == processor)
        
        affil_counts = affil_query.with_entities(
            PaperAuthor.affiliation,
            func.count(func.distinct(Paper.id)).label('count')
        ).filter(
            PaperAuthor.affiliation.isnot(None),
            PaperAuthor.affiliation != ''
        ).group_by(PaperAuthor.affiliation).order_by(desc('count')).limit(20).all()
        
        affiliation_facets = [
            {"value": affil, "count": count, "label": affil}
            for affil, count in affil_counts if affil
        ]
        
        # Get processor facets (for filtering by PDF processor used)
        processor_query = base_query
        if author:
            processor_query = processor_query.join(PaperAuthor).filter(PaperAuthor.name.ilike(f"%{author}%"))
        if affiliation:
            if author:  # Already joined
                processor_query = processor_query.filter(PaperAuthor.affiliation.ilike(f"%{affiliation}%"))
            else:
                processor_query = processor_query.join(PaperAuthor).filter(PaperAuthor.affiliation.ilike(f"%{affiliation}%"))
        if tag:
            unified_service = UnifiedTagService(db)
            processor_query = unified_service.filter_papers_by_tag(processor_query, tag, use_hierarchy=True)
        if conference:
            processor_query = processor_query.filter(Paper.conference.ilike(f"%{conference}%"))
        if year:
            processor_query = processor_query.filter(func.extract('year', Paper.publication_date) == year)
        
        processor_counts = processor_query.with_entities(
            Paper.processor_used,
            func.count(Paper.id).label('count')
        ).filter(Paper.processor_used.isnot(None)).group_by(Paper.processor_used).order_by(desc('count')).all()
        
        processor_facets = [
            {"value": proc, "count": count, "label": proc.replace('_', ' ').title()}
            for proc, count in processor_counts if proc
        ]
        
        # Get total count for current filters
        total_query = base_query
        if author:
            total_query = total_query.join(PaperAuthor).filter(PaperAuthor.name.ilike(f"%{author}%"))
        if affiliation:
            if author:  # Already joined
                total_query = total_query.filter(PaperAuthor.affiliation.ilike(f"%{affiliation}%"))
            else:
                total_query = total_query.join(PaperAuthor).filter(PaperAuthor.affiliation.ilike(f"%{affiliation}%"))
        if tag:
            unified_service = UnifiedTagService(db)
            total_query = unified_service.filter_papers_by_tag(total_query, tag, use_hierarchy=True)
        if conference:
            total_query = total_query.filter(Paper.conference.ilike(f"%{conference}%"))
        if year:
            total_query = total_query.filter(func.extract('year', Paper.publication_date) == year)
        if processor:
            total_query = total_query.filter(Paper.processor_used == processor)
        
        total_count = total_query.count()
        
        return {
            "facets": {
                "authors": author_facets,
                "conferences": conference_facets,
                "years": year_facets,
                "tags": tag_facets,
                "affiliations": affiliation_facets,
                "processors": processor_facets
            },
            "total_results": total_count,
            "active_filters": {
                "search": search,
                "author": author,
                "tag": tag,
                "conference": conference,
                "year": year,
                "affiliation": affiliation,
                "processor": processor
            }
        }
    except Exception as e:
        logger.error(f"Error getting paper facets: {e}")
        # Return empty facets on error
        return {
            "facets": {
                "authors": [],
                "conferences": [],
                "years": [],
                "tags": [],
                "affiliations": [],
                "processors": []
            },
            "total_results": 0,
            "active_filters": {
                "search": search,
                "author": author,
                "tag": tag,
                "conference": conference,
                "year": year,
                "affiliation": affiliation
            }
        }

@router.post("/reindex")
    """Reindex all papers in the RAG system"""
    try:
        results = rag_service.update_all_papers(db)
        return {
            "message": "Papers reindexed successfully",
            "results": results
        }
    except Exception as e:
        logger.error(f"Error reindexing papers: {e}")
        raise HTTPException(status_code=500, detail=f"Error reindexing papers: {str(e)}")

@router.get("/search")
def search_papers_rag(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50),
):
    """Search papers using RAG (semantic search)"""
    try:
        results = rag_service.search_papers(q, k=limit)
        
        # Filter to only paper results
        paper_results = [r for r in results if r.get("type") == "paper"]
        
        return {
            "query": q,
            "results": paper_results,
            "total": len(paper_results)
        }
    except Exception as e:
        logger.error(f"Error searching papers: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching papers: {str(e)}")

@router.get("/{paper_id}/pdf")
    """Get the PDF file for a paper"""
    
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    if not paper.pdf_path:
        raise HTTPException(status_code=404, detail="PDF file not found")
    
    import os
    if not os.path.exists(paper.pdf_path):
        raise HTTPException(status_code=404, detail="PDF file not found on disk")
    
    return FileResponse(
        path=paper.pdf_path,
        media_type="application/pdf",
        filename=os.path.basename(paper.pdf_path)
    )

@router.delete("/{paper_id}")
    """Delete a paper and all its related data"""
    
    # Get the paper
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Delete related data in order (due to foreign key constraints)
    # Delete snippets
    db.query(PaperSnippet).filter(PaperSnippet.paper_id == paper_id).delete()
    
    # Delete tags
    db.query(PaperTag).filter(PaperTag.paper_id == paper_id).delete()
    
    # Delete sections
    db.query(PaperSection).filter(PaperSection.paper_id == paper_id).delete()
    
    # Delete the paper (authors will be handled by cascade if configured)
    db.delete(paper)
    db.commit()
    
    return {"message": f"Paper '{paper.title}' deleted successfully"}

@router.get("/{paper_id}", response_model=PaperResponse)
    """Get detailed information about a specific paper"""
    
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    return PaperResponse(
        id=paper.id,
        title=paper.title,
        abstract=paper.abstract,
        authors=[
            {
                "name": a.name, 
                "email": a.email,
                "affiliation": a.affiliation  # Include affiliation
            }
            for a in paper.author_details
        ],
        publication_date=paper.publication_date,
        conference=paper.conference,
        journal=paper.journal,
        arxiv_id=paper.arxiv_id,
        doi=paper.doi,
        page_count=paper.page_count,
        word_count=paper.word_count if hasattr(paper, 'word_count') else 0,  # Include word count for showing paper length
        tags=[t.tag for t in paper.tags],
        created_at=paper.created_at,
        processed=paper.processed,
        processor_used=paper.processor_used,
        pdf_path=paper.pdf_path,  # Include PDF path for frontend
        processing_error=paper.processing_error  # Include processing error if any
    )

@router.get("/{paper_id}/content")
    """Get the full text content of a paper"""
    
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    return {
        "id": paper.id,
        "title": paper.title,
        "content": paper.content,
        "sections": [
            {
                "id": s.id,
                "type": s.section_type,
                "title": s.title,
                "content": s.content,
                "position": s.position
            }
            for s in paper.sections
        ]
    }

    content: str

@router.put("/{paper_id}/content")
def update_paper_content(
    paper_id: int, 
    content_update: UpdatePaperContent,
):
    """Update the markdown content of a paper"""
    
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Update the content
    paper.content = content_update.content
    
    try:
        db.commit()
        db.refresh(paper)
        logger.info(f"Updated content for paper {paper_id}")
        
        return {
            "id": paper.id,
            "title": paper.title,
            "content": paper.content,
            "message": "Content updated successfully"
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating paper content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    use_full_content: bool = False

@router.post("/{paper_id}/extract-authors")
def extract_paper_authors(
    paper_id: int,
    request: ExtractAuthorsRequest = ExtractAuthorsRequest(),
):
    """Extract authors and affiliations from paper using LLM"""
    
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    if not paper.content:
        raise HTTPException(status_code=400, detail="Paper has no content to analyze")
    
    # Extract authors using the service (now synchronous)
    result = author_extraction_service.extract_authors(
        paper_content=paper.content,
        paper_title=paper.title
    )
    
    if result.get("success") and result.get("authors"):
        # Store authors in database
        try:
            # Remove existing authors
            db.query(PaperAuthor).filter(PaperAuthor.paper_id == paper_id).delete()
            
            # Add new authors
            for idx, author_data in enumerate(result["authors"]):
                author = PaperAuthor(
                    paper_id=paper_id,
                    name=author_data.get("name", "Unknown"),
                    affiliation=author_data.get("affiliation", ""),
                    email=author_data.get("email", ""),
                    position=idx
                )
                db.add(author)
            
            db.commit()
            logger.info(f"Extracted and saved {len(result['authors'])} authors for paper {paper_id}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving extracted authors: {e}")
            result["warning"] = "Authors extracted but not saved to database"
    
    return result

    title: Optional[str] = None
    abstract: Optional[str] = None
    publication_date: Optional[Union[date, str]] = None  # Accept both date and string
    conference: Optional[str] = None
    journal: Optional[str] = None
    arxiv_id: Optional[str] = None
    doi: Optional[str] = None
    authors: Optional[List[dict]] = None  # List of author dicts with name, affiliation, email

@router.put("/{paper_id}/metadata")
def update_paper_metadata(
    paper_id: int,
    metadata_update: UpdatePaperMetadata,
):
    """Update paper metadata including authors"""
    
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    try:
        logger.info(f"Updating metadata for paper {paper_id}")
        logger.info(f"Received metadata update: {metadata_update.dict()}")
        
        # Update basic metadata
        if metadata_update.title is not None:
            paper.title = metadata_update.title
        if metadata_update.abstract is not None:
            paper.abstract = metadata_update.abstract
        if metadata_update.publication_date is not None:
            # Handle both string and date types
            if isinstance(metadata_update.publication_date, str):
                try:
                    from datetime import datetime
                    paper.publication_date = datetime.fromisoformat(metadata_update.publication_date.replace('Z', '+00:00')).date()
                except:
                    logger.warning(f"Could not parse publication date: {metadata_update.publication_date}")
            else:
                paper.publication_date = metadata_update.publication_date
        if metadata_update.conference is not None:
            paper.conference = metadata_update.conference
        if metadata_update.journal is not None:
            paper.journal = metadata_update.journal
        if metadata_update.arxiv_id is not None:
            paper.arxiv_id = metadata_update.arxiv_id
        if metadata_update.doi is not None:
            paper.doi = metadata_update.doi
        
        # Update authors if provided
        if metadata_update.authors is not None:
            # Remove existing authors
            db.query(PaperAuthor).filter(PaperAuthor.paper_id == paper_id).delete()
            
            # Add new authors
            author_names = []
            for idx, author_data in enumerate(metadata_update.authors):
                author = PaperAuthor(
                    paper_id=paper_id,
                    name=author_data.get("name", "Unknown"),
                    affiliation=author_data.get("affiliation", ""),
                    email=author_data.get("email", ""),
                    position=idx
                )
                db.add(author)
                author_names.append(author_data.get("name", "Unknown"))
            
            # Update the authors string field as well
            paper.authors = ", ".join(author_names)
        
        db.commit()
        db.refresh(paper)
        
        # Return updated paper with authors
        return {
            "id": paper.id,
            "title": paper.title,
            "abstract": paper.abstract,
            "publication_date": paper.publication_date,
            "conference": paper.conference,
            "journal": paper.journal,
            "arxiv_id": paper.arxiv_id,
            "doi": paper.doi,
            "authors": [
                {
                    "name": author.name,
                    "affiliation": author.affiliation,
                    "email": author.email,
                    "position": author.position
                }
                for author in paper.author_details
            ],
            "message": "Metadata updated successfully"
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating paper metadata: {e}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{paper_id}/process-grobid")
async def process_paper_with_grobid(
    paper_id: int,
):
    """Process paper with GROBID to extract metadata and conclusion"""
    
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    if not paper.pdf_path:
        raise HTTPException(status_code=400, detail="Paper has no PDF file")
    
    try:
        logger.info(f"Processing paper {paper_id} with GROBID")
        
        # Process with GROBID
        result = grobid_service.process_pdf(paper.pdf_path)
        
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=f"GROBID processing failed: {result.get('error')}")
        
        # Extract and save conclusion if found
        conclusion_saved = False
        if result.get('full_document', {}).get('success'):
            tei_xml = result['full_document'].get('tei_xml', '')
            conclusion_data = grobid_service.extract_conclusion(tei_xml)
            
            if conclusion_data:
                logger.info(f"Found conclusion for paper {paper_id}")
                
                # Format conclusion text using LLM
                try:
                    from app.services.llm_service import LLMService
                    llm_service = LLMService()
                    
                    # Use academic text formatting prompt
                    formatted_content = llm_service.format_academic_text(
                        text=conclusion_data['content'],
                        section_type='conclusion'
                    )
                    
                    # Check if conclusion section already exists
                    existing_conclusion = db.query(PaperSection).filter(
                        PaperSection.paper_id == paper_id,
                        PaperSection.section_type == 'conclusion'
                    ).first()
                    
                    if existing_conclusion:
                        # Update existing conclusion
                        existing_conclusion.title = conclusion_data['title']
                        existing_conclusion.content = formatted_content
                    else:
                        # Create new conclusion section
                        conclusion_section = PaperSection(
                            paper_id=paper_id,
                            section_type='conclusion',
                            title=conclusion_data['title'],
                            content=formatted_content,
                            position=99  # Put conclusion at the end
                        )
                        db.add(conclusion_section)
                    
                    db.commit()
                    conclusion_saved = True
                    logger.info(f"Saved conclusion for paper {paper_id}")
                    
                except Exception as e:
                    logger.error(f"Error formatting conclusion: {e}")
                    # Save unformatted conclusion as fallback
                    existing_conclusion = db.query(PaperSection).filter(
                        PaperSection.paper_id == paper_id,
                        PaperSection.section_type == 'conclusion'
                    ).first()
                    
                    if existing_conclusion:
                        existing_conclusion.title = conclusion_data['title']
                        existing_conclusion.content = conclusion_data['content']
                    else:
                        conclusion_section = PaperSection(
                            paper_id=paper_id,
                            section_type='conclusion',
                            title=conclusion_data['title'],
                            content=conclusion_data['content'],
                            position=99
                        )
                        db.add(conclusion_section)
                    
                    db.commit()
                    conclusion_saved = True
        
        # Save TEI XML if available
        tei_saved = False
        if result.get('full_document', {}).get('tei_xml'):
            tei_path = Path(paper.pdf_path).parent.parent / 'tei_xml' / f"{paper_id}.xml"
            tei_path.parent.mkdir(parents=True, exist_ok=True)
            if grobid_service.save_tei_xml(result['full_document']['tei_xml'], str(tei_path)):
                tei_saved = True
        
        return {
            "success": True,
            "paper_id": paper_id,
            "metadata_extracted": bool(result.get('metadata')),
            "references_extracted": len(result.get('references', [])),
            "sections_extracted": len(result.get('sections', [])),
            "conclusion_saved": conclusion_saved,
            "tei_xml_saved": tei_saved,
            "metadata": result.get('metadata', {}),
            "message": "GROBID processing completed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing paper with GROBID: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{paper_id}/tags/suggestions")
def get_tag_suggestions(
    paper_id: int,
):
    """Get AI-powered tag suggestions for a paper"""
    
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    suggestions = tag_service.suggest_tags_from_paper(db, paper_id)
    
    # Get existing tags
    existing_tags = db.query(PaperTag.tag).filter(
        PaperTag.paper_id == paper_id
    ).all()
    
    return {
        "paper_id": paper_id,
        "suggestions": suggestions,
        "existing_tags": [tag[0] for tag in existing_tags]
    }

@router.post("/{paper_id}/tags/suggest")
def suggest_paper_tags(
    paper_id: int,
):
    """Generate tag suggestions for a paper using LLM and vector similarity"""
    
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Get already assigned tags
    existing_tags = db.query(PaperTag.tag).filter(
        PaperTag.paper_id == paper_id
    ).all()
    already_tagged = [tag[0] for tag in existing_tags]
    
    # Prepare content for similarity search - focus on title and abstract for better embedding quality
    content_for_similarity = f"""
    {paper.title}
    
    {paper.abstract or ''}
    """
    
    # Prepare fuller content for LLM analysis (if needed)
    content_for_llm = f"""
    Title: {paper.title}
    
    Abstract: {paper.abstract or 'No abstract available'}
    
    Authors: {paper.authors or 'Unknown'}
    
    Conference/Journal: {paper.conference or paper.journal or 'Not specified'}
    
    Full Paper Content (first 5000 chars):
    {(paper.content[:5000] if paper.content else 'No content available')}
    """
    
    # DEBUG: Log paper content stats
    logger.info(f"[DEBUG] ======== PAPER CONTENT ANALYSIS ========")
    logger.info(f"[DEBUG] Paper ID: {paper_id}")
    logger.info(f"[DEBUG] - Title: '{paper.title[:100]}...'")
    logger.info(f"[DEBUG] - Title length: {len(paper.title) if paper.title else 0} chars")
    logger.info(f"[DEBUG] - Abstract length: {len(paper.abstract) if paper.abstract else 0} chars")
    logger.info(f"[DEBUG] - Full content length: {len(paper.content) if paper.content else 0} chars")
    logger.info(f"[DEBUG] - Similarity content length: {len(content_for_similarity)} chars")
    logger.info(f"[DEBUG] - LLM content length: {len(content_for_llm)} chars")
    
    # Check if content is actually populated
    if paper.content:
        if len(paper.content) < 1000:
            logger.warning(f"[DEBUG] WARNING: Paper content is suspiciously short ({len(paper.content)} chars)")
        if "No content available" in paper.content:
            logger.warning(f"[DEBUG] WARNING: Paper content contains placeholder text!")
        logger.info(f"[DEBUG] - First 300 chars of paper.content: {paper.content[:300]}...")
    else:
        logger.warning(f"[DEBUG] WARNING: paper.content is None or empty!")
    
    # 1. Get similar existing tags using vector search
    similar_tags = []
    try:
        from app.services.vector_store_openai import get_vector_store
        vector_store = get_vector_store()
        
        # Search for similar tags using title and abstract for better embedding match
        logger.info(f"Searching for similar tags with content: {content_for_similarity[:200]}...")
        search_results = vector_store.search_similar_tags(
            query_text=content_for_similarity,
            k=20,  # Get more suggestions
            min_similarity=0.3  # Lower threshold to get more relevant tags
        )
        logger.info(f"Vector search returned {len(search_results)} results")
        
        # Filter out already tagged items
        already_tagged_lower = [t.lower() for t in already_tagged]
        for tag, score, usage_count in search_results:
            if tag.lower() not in already_tagged_lower:
                similar_tags.append({
                    'tag': tag,
                    'score': score,
                    'usage_count': usage_count,
                    'type': 'existing'
                })
                logger.debug(f"Added similar tag: {tag} (score: {score:.3f})")
                
        logger.info(f"Found {len(similar_tags)} similar existing tags after filtering")
    except Exception as e:
        logger.warning(f"Vector similarity search failed: {e}")
        similar_tags = []
    
    # 2. Generate new tag suggestions using LLM
    new_suggestions = []
    model_name = "unknown"
    
    try:
        from app.services.llm_service import LLMService
        import json
        import os
        
        # Load configurations
        llm_config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'llm.json')
        prompts_config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'prompts_config.json')
        
        with open(llm_config_path, 'r') as f:
            llm_config = json.load(f)
        with open(prompts_config_path, 'r') as f:
            prompts_config = json.load(f)
        
        # Get the paper_analysis_deep model config (Claude Opus 4.1 for comprehensive analysis)
        model_config = llm_config['models'].get('paper_analysis_deep', llm_config['models']['paper_analysis'])
        
        # DEBUG: Log the full model config
        logger.info(f"[DEBUG] Model config selected: {json.dumps(model_config, indent=2)}")
        
        llm_service = LLMService()
        
        # Log content size
        content_length = len(content_for_llm)
        logger.info(f"[DEBUG] Generating tags for paper {paper_id} with {content_length} chars of content")
        
        # Use prompts from config
        if 'paper_tag_suggestion' in prompts_config:
            tag_config = prompts_config['paper_tag_suggestion']
            logger.info(f"[DEBUG] Using paper_tag_suggestion prompt")
        else:
            tag_config = prompts_config['article_tag_suggestion']
            logger.info(f"[DEBUG] Falling back to article_tag_suggestion prompt")
        
        system_prompt = tag_config['system']
        max_tags = tag_config.get('max_tags', 15)  # Get from config, default to 15 if not specified
        user_prompt = tag_config['user_template'].format(
            author=paper.authors or 'Unknown',
            text=content_for_llm,  # Use the fuller content for LLM analysis
            max_tags=max_tags
        )
        logger.info(f"[DEBUG] Requesting {max_tags} tags from LLM")
        
        # DEBUG: Log prompt sizes and content breakdown
        logger.info(f"[DEBUG] System prompt length: {len(system_prompt)} chars")
        logger.info(f"[DEBUG] User prompt length: {len(user_prompt)} chars")
        
        # Extract and log the actual paper content being sent
        if "Full Paper Content:" in user_prompt:
            content_start = user_prompt.find("Full Paper Content:") + len("Full Paper Content:")
            actual_paper_content = user_prompt[content_start:].strip()
            logger.info(f"[DEBUG] === CONTENT BREAKDOWN ===")
            logger.info(f"[DEBUG] Paper content in prompt: {len(actual_paper_content)} chars")
            logger.info(f"[DEBUG] First 200 chars of paper content: {actual_paper_content[:200]}...")
            logger.info(f"[DEBUG] Last 200 chars of paper content: ...{actual_paper_content[-200:]}")
            
            # Count approximate tokens (rough estimate: 1 token ≈ 4 chars)
            approx_tokens = len(user_prompt) / 4
            logger.info(f"[DEBUG] Approximate input tokens: {approx_tokens:.0f}")
        
        logger.info(f"[DEBUG] First 500 chars of full prompt: {user_prompt[:500]}...")
        
        model_name = model_config.get('model', 'unknown')
        model_max_tokens = model_config.get('max_tokens', 8000)  # Use model's configured max_tokens
        model_temperature = model_config.get('temperature', 0.3)
        
        logger.info(f"[DEBUG] FINAL CONFIG - Model: {model_name}, Max tokens: {model_max_tokens}, Temperature: {model_temperature}")
        
        # Pass the specific model and its token limits
        llm_response = llm_service.generate_text(
            prompt=user_prompt,
            system_message=system_prompt,
            max_tokens=model_max_tokens,  # Use the model's configured limit (8000 for paper_analysis)
            temperature=model_temperature,
            model=model_name  # Pass the specific model to use
        )
        
        if llm_response:
            try:
                # Parse JSON response
                if isinstance(llm_response, str):
                    # Extract JSON from response if it's wrapped
                    import re
                    json_match = re.search(r'\[(.*?)\]', llm_response, re.DOTALL)
                    if json_match:
                        tags_data = json.loads('[' + json_match.group(1) + ']')
                    else:
                        tags_data = json.loads(llm_response)
                else:
                    tags_data = llm_response
                
                # Convert to list if needed
                if isinstance(tags_data, dict) and 'tags' in tags_data:
                    tags_data = tags_data['tags']
                
                # Filter and format
                already_tagged_lower = [t.lower() for t in already_tagged]
                similar_tag_names = [t['tag'].lower() for t in similar_tags]
                
                for tag in tags_data:
                    if isinstance(tag, str) and tag.strip():
                        tag_clean = tag.strip()
                        if (tag_clean.lower() not in already_tagged_lower and 
                            tag_clean.lower() not in similar_tag_names):
                            new_suggestions.append({
                                'tag': tag_clean,
                                'type': 'new',
                                'model': model_name
                            })
                
                logger.info(f"Generated {len(new_suggestions)} new tag suggestions")
                logger.info(f"[DEBUG] Raw LLM response: {llm_response[:1000]}...")  # Show first 1000 chars of response
                
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.error(f"Error parsing LLM response: {e}")
                logger.error(f"Raw response: {llm_response}")
                
    except Exception as e:
        logger.error(f"Error generating tag suggestions: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    
    return {
        "paper_id": paper_id,
        "existing_suggestions": similar_tags,
        "new_suggestions": new_suggestions,
        "already_tagged": already_tagged,
        "model_used": model_name,
        "total_suggestions": len(similar_tags) + len(new_suggestions)
    }

@router.post("/{paper_id}/tags")
def add_paper_tag(
    paper_id: int,
    tag_request: TagRequest,
):
    """Add a tag to a paper"""
    
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Normalize tag using unified service
    unified_service = UnifiedTagService(db)
    normalized_tag = unified_service.normalize_tag_for_storage(
        tag_request.tag, 
        preserve_case=(tag_request.tag_type == 'manual')
    )
    
    # Check if tag already exists (check both original and normalized)
    existing_tag = db.query(PaperTag).filter(
        PaperTag.paper_id == paper_id,
        func.lower(PaperTag.tag) == func.lower(normalized_tag)
    ).first()
    
    if existing_tag:
        return {"message": "Tag already exists", "tag": existing_tag.tag}
    
    # Add new tag with normalized form
    new_tag = PaperTag(
        paper_id=paper_id,
        tag=normalized_tag,
        tag_type=tag_request.tag_type
    )
    db.add(new_tag)
    db.commit()
    
    logger.info(f"Added tag '{normalized_tag}' to paper {paper_id} (original: '{tag_request.tag}')")
    
    # Update vector store with new tag
    try:
        vector_store = get_vector_store()
        # Get paper title for context
        context = f"{paper.title}: {paper.abstract[:200] if paper.abstract else ''}"
        vector_store.update_tag_incrementally(normalized_tag, 'paper', context)
        logger.info(f"Updated vector store with new paper tag: {normalized_tag}")
    except Exception as e:
        logger.error(f"Failed to update vector store for tag '{normalized_tag}': {e}")
        # Don't fail the request if vector store update fails
    
    return {"message": "Tag added successfully", "tag": normalized_tag}

@router.delete("/{paper_id}/tags/{tag}")
def remove_paper_tag(
    paper_id: int,
    tag: str,
):
    """Remove a tag from a paper"""
    
    tag_entry = db.query(PaperTag).filter(
        PaperTag.paper_id == paper_id,
        PaperTag.tag == tag
    ).first()
    
    if not tag_entry:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    db.delete(tag_entry)
    db.commit()
    
    return {"message": "Tag removed successfully"}

@router.post("/{paper_id}/snippets")
def create_paper_snippet(
    paper_id: int,
    snippet_request: SnippetRequest,
):
    """Create a snippet from a paper"""
    
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    snippet = PaperSnippet(
        paper_id=paper_id,
        content=snippet_request.content,
        page_number=snippet_request.page_number,
        annotation=snippet_request.annotation,
        category=snippet_request.category
    )
    
    db.add(snippet)
    db.commit()
    db.refresh(snippet)
    
    return {
        "id": snippet.id,
        "content": snippet.content,
        "annotation": snippet.annotation,
        "category": snippet.category,
        "created_at": snippet.created_at
    }

@router.get("/{paper_id}/snippets")
    """Get all snippets for a paper"""
    
    snippets = db.query(PaperSnippet).filter(
        PaperSnippet.paper_id == paper_id
    ).order_by(desc(PaperSnippet.created_at)).all()
    
    return [
        {
            "id": s.id,
            "content": s.content,
            "page_number": s.page_number,
            "annotation": s.annotation,
            "category": s.category,
            "created_at": s.created_at
        }
        for s in snippets
    ]

@router.get("/{paper_id}/sections")
    """Get all sections for a paper including abstract and conclusion"""
    
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    sections = []
    
    # Add abstract as the first section if available
    if paper.abstract:
        sections.append({
            "id": -1,  # Special ID for abstract
            "section_type": "abstract",
            "title": "Abstract",
            "content": paper.abstract,
            "position": 0
        })
    
    # Get all saved sections from database
    db_sections = db.query(PaperSection).filter(
        PaperSection.paper_id == paper_id
    ).order_by(PaperSection.position.asc()).all()
    
    for section in db_sections:
        sections.append({
            "id": section.id,
            "section_type": section.section_type,
            "title": section.title,
            "content": section.content,
            "position": section.position,
            "page_start": section.page_start,
            "page_end": section.page_end
        })
    
    return {
        "paper_id": paper_id,
        "sections": sections,
        "total_sections": len(sections)
    }

    content: str

@router.put("/{paper_id}/sections/{section_id}")
def update_paper_section(
    paper_id: int,
    section_id: int,
    request: UpdateSectionRequest,
):
    """Update a paper section content"""
    
    # Handle abstract special case (id = -1)
    if section_id == -1:
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        paper.abstract = request.content
        db.commit()
        
        return {
            "success": True,
            "message": "Abstract updated successfully",
            "section_type": "abstract"
        }
    
    # Handle regular sections
    section = db.query(PaperSection).filter(
        PaperSection.id == section_id,
        PaperSection.paper_id == paper_id
    ).first()
    
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    
    section.content = request.content
    db.commit()
    
    return {
        "success": True,
        "message": f"{section.section_type} updated successfully",
        "section_type": section.section_type
    }

@router.get("/{paper_id}/snippets/export")
def export_paper_snippets(
    paper_id: int,
    format: str = Query("markdown", enum=["markdown", "json", "text"]),
):
    """Export snippets in various formats"""
    
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    snippets = db.query(PaperSnippet).filter(
        PaperSnippet.paper_id == paper_id
    ).order_by(PaperSnippet.created_at).all()
    
    if format == "markdown":
        # Generate markdown format
        content = f"# Snippets from: {paper.title}\n\n"
        content += f"**Authors:** {', '.join([a.name for a in paper.author_details])}\n\n"
        
        # Group by category
        categories = {}
        uncategorized = []
        
        for snippet in snippets:
            if snippet.category:
                if snippet.category not in categories:
                    categories[snippet.category] = []
                categories[snippet.category].append(snippet)
            else:
                uncategorized.append(snippet)
        
        # Write categorized snippets
        for category, cat_snippets in categories.items():
            content += f"## {category.title()}\n\n"
            for s in cat_snippets:
                content += f"### Snippet {s.id}\n"
                if s.page_number:
                    content += f"*Page {s.page_number}*\n\n"
                content += f"> {s.content}\n\n"
                if s.annotation:
                    content += f"**Note:** {s.annotation}\n\n"
                content += "---\n\n"
        
        # Write uncategorized snippets
        if uncategorized:
            content += "## Uncategorized\n\n"
            for s in uncategorized:
                content += f"### Snippet {s.id}\n"
                if s.page_number:
                    content += f"*Page {s.page_number}*\n\n"
                content += f"> {s.content}\n\n"
                if s.annotation:
                    content += f"**Note:** {s.annotation}\n\n"
                content += "---\n\n"
        
        from fastapi.responses import Response
        return Response(
            content=content,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f"attachment; filename=snippets_{paper_id}.md"
            }
        )
    
    elif format == "json":
        # Return JSON format
        import json
        data = {
            "paper": {
                "id": paper.id,
                "title": paper.title,
                "authors": [a.name for a in paper.author_details]
            },
            "snippets": [
                {
                    "id": s.id,
                    "content": s.content,
                    "page_number": s.page_number,
                    "annotation": s.annotation,
                    "category": s.category,
                    "created_at": s.created_at.isoformat() if s.created_at else None
                }
                for s in snippets
            ]
        }
        
        from fastapi.responses import Response
        return Response(
            content=json.dumps(data, indent=2),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=snippets_{paper_id}.json"
            }
        )
    
    else:  # text format
        # Simple text format
        content = f"Snippets from: {paper.title}\n"
        content += "=" * 50 + "\n\n"
        
        for i, s in enumerate(snippets, 1):
            content += f"Snippet {i}"
            if s.page_number:
                content += f" (Page {s.page_number})"
            content += "\n" + "-" * 30 + "\n"
            content += s.content + "\n"
            if s.annotation:
                content += f"\nNote: {s.annotation}\n"
            content += "\n"
        
        from fastapi.responses import Response
        return Response(
            content=content,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename=snippets_{paper_id}.txt"
            }
        )

@router.get("/{paper_id}/related")
def get_related_content(
    paper_id: int,
):
    """Find tweets and articles related to this paper"""
    
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Use semantic search to find related content
    from app.services.rag_service import RAGService
    rag_service = RAGService(db)
    
    # Create a search query from paper title and abstract
    query = f"{paper.title}"
    if paper.abstract:
        query += f" {paper.abstract[:200]}"
    
    # Search for related content
    search_results = rag_service.search(query, k=20)
    
    related_tweets = []
    related_articles = []
    
    for result in search_results:
        if result.source_type == 'tweet':
            related_tweets.append({
                'tweet_id': result.source_id,
                'content': result.content[:280],
                'author': result.metadata.get('author'),
                'score': result.score
            })
        elif result.source_type == 'article':
            related_articles.append({
                'article_id': result.source_id,
                'title': result.metadata.get('title'),
                'author': result.metadata.get('author'),
                'content_preview': result.content[:200],
                'score': result.score
            })
    
    # Also check for direct keyword matches in tags
    paper_tags = [tag.tag for tag in paper.tags]
    
    if paper_tags:
        from app.models import Tag, Tweet, SubstackArticle
        
        # Find tweets with matching tags
        tag_matched_tweets = db.query(Tweet).join(Tag).filter(
            Tag.tag.in_(paper_tags)
        ).limit(10).all()
        
        for tweet in tag_matched_tweets:
            if not any(t['tweet_id'] == str(tweet.id) for t in related_tweets):
                related_tweets.append({
                    'tweet_id': str(tweet.id),
                    'content': tweet.text[:280],
                    'author': tweet.author_username,
                    'score': 0.5  # Lower score for tag matches
                })
    
    # Sort by score
    related_tweets.sort(key=lambda x: x['score'], reverse=True)
    related_articles.sort(key=lambda x: x['score'], reverse=True)
    
    return {
        'paper_id': paper_id,
        'paper_title': paper.title,
        'related_tweets': related_tweets[:10],
        'related_articles': related_articles[:10]
    }

@router.get("/stats/overview")
    """Get overview statistics for papers"""
    
    total_papers = db.query(func.count(Paper.id)).scalar()
    total_authors = db.query(func.count(func.distinct(PaperAuthor.name))).scalar()
    total_tags = db.query(func.count(func.distinct(PaperTag.tag))).scalar()
    total_snippets = db.query(func.count(PaperSnippet.id)).scalar()
    
    # Get recent papers
    recent_papers = db.query(Paper).order_by(
        desc(Paper.created_at)
    ).limit(5).all()
    
    # Get top tags
    top_tags = db.query(
        PaperTag.tag,
        func.count(PaperTag.id).label('count')
    ).group_by(PaperTag.tag).order_by(
        desc('count')
    ).limit(10).all()
    
    return {
        "total_papers": total_papers,
        "total_authors": total_authors,
        "total_tags": total_tags,
        "total_snippets": total_snippets,
        "recent_papers": [
            {"id": p.id, "title": p.title, "created_at": p.created_at}
            for p in recent_papers
        ],
        "top_tags": [
            {"tag": tag, "count": count}
            for tag, count in top_tags
        ]
    }

# Paper Analysis Endpoints

@router.get("/{paper_id}/analyses/available")
def get_available_analyses():
    """Get list of available analysis types"""
    return {
        "analyses": analysis_service.get_available_analyses(),
        "by_category": analysis_service.get_analyses_by_category()
    }

    analysis_type: str

@router.post("/{paper_id}/analyses/generate")
def generate_paper_analysis(
    paper_id: int,
    request: GenerateAnalysisRequest,
):
    """Generate a specific analysis for a paper"""
    
    result = analysis_service.generate_analysis(
        paper_id=paper_id,
        analysis_type=request.analysis_type,
        db=db
    )
    
    return result

    analysis_types: List[str]

@router.post("/{paper_id}/analyses/generate-multiple")
def generate_multiple_analyses(
    paper_id: int,
    request: GenerateMultipleAnalysesRequest,
):
    """Generate multiple analyses for a paper"""
    
    result = analysis_service.generate_multiple_analyses(
        paper_id=paper_id,
        analysis_types=request.analysis_types,
        db=db
    )
    
    return result

@router.get("/{paper_id}/analyses/saved")
def get_saved_analyses(
    paper_id: int,
):
    """Get all saved analyses for a paper"""
    
    # Check if paper exists
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Get saved analyses
    analyses = analysis_service.get_saved_analyses(db, paper_id)
    
    return {
        "paper_id": paper_id,
        "paper_title": paper.title,
        "analyses": analyses
    }

# GROBID Processing Endpoints

@router.post("/{paper_id}/grobid/process")
def process_paper_with_grobid(
    paper_id: int,
):
    """Process a paper with GROBID to extract structured metadata, TEI XML, and references"""
    
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    if not paper.pdf_path:
        raise HTTPException(status_code=400, detail="Paper has no PDF file")
    
    import os
    if not os.path.exists(paper.pdf_path):
        raise HTTPException(status_code=404, detail="PDF file not found on disk")
    
    try:
        # Process with GROBID
        result = grobid_service.process_pdf(paper.pdf_path)
        
        if not result.get('success'):
            raise HTTPException(
                status_code=500,
                detail=f"GROBID processing failed: {result.get('error', 'Unknown error')}"
            )
        
        # Store TEI XML if available
        if result.get('full_document', {}).get('tei_xml'):
            # Create TEI storage directory if it doesn't exist
            tei_dir = os.path.join('data', 'tei_xml')
            os.makedirs(tei_dir, exist_ok=True)
            
            # Save TEI XML
            tei_path = os.path.join(tei_dir, f"paper_{paper_id}_tei.xml")
            grobid_service.save_tei_xml(
                result['full_document']['tei_xml'],
                tei_path
            )
            
            # Store TEI path in paper record (you may need to add this field to the model)
            # paper.tei_xml_path = tei_path
        
        # Update paper metadata if extracted
        if result.get('metadata'):
            metadata = result['metadata']
            
            # Update title if available
            if metadata.get('title') and len(metadata['title']) > 3:
                paper.title = metadata['title']
            
            # Update abstract if available
            if metadata.get('abstract'):
                paper.abstract = metadata['abstract']
            
            # Update publication date if available
            if metadata.get('publication_date'):
                try:
                    from datetime import datetime
                    paper.publication_date = datetime.fromisoformat(metadata['publication_date']).date()
                except:
                    pass
            
            # Update DOI if available
            if metadata.get('doi'):
                paper.doi = metadata['doi']
            
            # Update ArXiv ID if available
            if metadata.get('arxiv_id'):
                paper.arxiv_id = metadata['arxiv_id']
            
            # Update authors if extracted
            if metadata.get('authors'):
                # Remove existing authors
                db.query(PaperAuthor).filter(PaperAuthor.paper_id == paper_id).delete()
                
                # Add GROBID-extracted authors
                author_names = []
                for idx, author_data in enumerate(metadata['authors']):
                    author = PaperAuthor(
                        paper_id=paper_id,
                        name=author_data.get('name', 'Unknown'),
                        affiliation=author_data.get('affiliation', ''),
                        email=author_data.get('email', ''),
                        position=idx
                    )
                    if author_data.get('department'):
                        # Could store department in affiliation or a separate field
                        author.affiliation = f"{author_data.get('department', '')}, {author.affiliation}".strip(', ')
                    db.add(author)
                    author_names.append(author_data.get('name', 'Unknown'))
                
                # Update the authors string field as well
                paper.authors = ", ".join(author_names)
        
        # Store references if extracted
        if result.get('references'):
            # Remove existing references
            db.query(PaperReference).filter(PaperReference.paper_id == paper_id).delete()
            
            # Add GROBID-extracted references
            for ref_data in result['references']:
                reference = PaperReference(
                    paper_id=paper_id,
                    title=ref_data.get('title', ''),
                    authors=', '.join(ref_data.get('authors', [])) if ref_data.get('authors') else None,
                    year=int(ref_data['year']) if ref_data.get('year') and ref_data['year'].isdigit() else None,
                    venue=ref_data.get('venue', ''),
                    doi=ref_data.get('doi', ''),
                    raw_citation=f"{', '.join(ref_data.get('authors', []))}. {ref_data.get('title', '')}. {ref_data.get('venue', '')}. {ref_data.get('year', '')}".strip()
                )
                db.add(reference)
        
        db.commit()
        
        # Format response
        response = {
            'success': True,
            'paper_id': paper_id,
            'processed_at': result.get('processed_at'),
            'metadata_extracted': bool(result.get('metadata')),
            'references_extracted': len(result.get('references', [])),
            'sections_extracted': len(result.get('sections', [])),
            'citations_extracted': len(result.get('citation_contexts', []))
        }
        
        # Include extracted data
        if result.get('metadata'):
            response['metadata'] = result['metadata']
        if result.get('references'):
            response['references'] = result['references']
        if result.get('sections'):
            response['sections'] = result['sections']
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing paper with GROBID: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{paper_id}/tei")
    """Get the TEI XML for a paper (if processed with GROBID)"""
    
    import os
    
    # Check if TEI XML exists
    tei_path = os.path.join('data', 'tei_xml', f"paper_{paper_id}_tei.xml")
    
    if not os.path.exists(tei_path):
        # Try to process the paper with GROBID if not already done
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        if not paper.pdf_path or not os.path.exists(paper.pdf_path):
            raise HTTPException(status_code=404, detail="PDF file not found")
        
        # Process with GROBID
        result = grobid_service.process_pdf(paper.pdf_path)
        
        if result.get('success') and result.get('full_document', {}).get('tei_xml'):
            os.makedirs(os.path.dirname(tei_path), exist_ok=True)
            grobid_service.save_tei_xml(
                result['full_document']['tei_xml'],
                tei_path
            )
        else:
            raise HTTPException(status_code=404, detail="TEI XML not available for this paper")
    
    # Read and return TEI XML
    with open(tei_path, 'r', encoding='utf-8') as f:
        tei_xml = f.read()
    
    from fastapi.responses import Response
    return Response(
        content=tei_xml,
        media_type="application/xml",
        headers={
            "Content-Disposition": f"inline; filename=paper_{paper_id}.tei.xml"
        }
    )

@router.get("/{paper_id}/references")
    """Get extracted references for a paper"""
    
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    if not paper.pdf_path:
        raise HTTPException(status_code=400, detail="Paper has no PDF file")
    
    import os
    
    # Check if we have cached TEI XML
    tei_path = os.path.join('data', 'tei_xml', f"paper_{paper_id}_tei.xml")
    
    if os.path.exists(tei_path):
        # Extract references from cached TEI
        with open(tei_path, 'r', encoding='utf-8') as f:
            tei_xml = f.read()
        references = grobid_service._extract_references(tei_xml)
    else:
        # Process with GROBID to get references
        if not os.path.exists(paper.pdf_path):
            raise HTTPException(status_code=404, detail="PDF file not found on disk")
        
        result = grobid_service.process_pdf(paper.pdf_path)
        
        if not result.get('success'):
            raise HTTPException(
                status_code=500,
                detail=f"GROBID processing failed: {result.get('error', 'Unknown error')}"
            )
        
        references = result.get('references', [])
        
        # Cache TEI XML for future use
        if result.get('full_document', {}).get('tei_xml'):
            os.makedirs(os.path.dirname(tei_path), exist_ok=True)
            grobid_service.save_tei_xml(
                result['full_document']['tei_xml'],
                tei_path
            )
    
    return {
        'paper_id': paper_id,
        'paper_title': paper.title,
        'total_references': len(references),
        'references': references
    }

@router.post("/{paper_id}/automatic-annotation")
def generate_automatic_annotations(
    paper_id: int,
):
    """Generate automatic annotations for a paper using multiple analysis prompts"""
    
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    if not paper.content:
        raise HTTPException(status_code=400, detail="Paper has no content to analyze")
    
    try:
        from app.services.llm_service import LLMService
        import json
        import os
        from datetime import datetime
        
        # Load configurations
        llm_config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'llm.json')
        prompts_config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'prompts_config.json')
        
        with open(llm_config_path, 'r') as f:
            llm_config = json.load(f)
        with open(prompts_config_path, 'r') as f:
            prompts_config = json.load(f)
        
        # Get the paper_analysis_deep model config (Claude Opus 4.1)
        model_config = llm_config['models'].get('paper_analysis_deep', llm_config['models']['tag_suggestion'])
        
        llm_service = LLMService()
        
        # Get available paper analysis prompts
        paper_analyses = prompts_config.get('paper_analyses', {})
        
        results = []
        
        # Run each analysis type
        for analysis_key, analysis_config in paper_analyses.items():
            try:
                logger.info(f"Running {analysis_config['name']} analysis for paper {paper_id}")
                
                # Prepare prompt
                system_prompt = analysis_config['system']
                user_prompt = analysis_config['user_template'].format(
                    paper_content=paper.content
                )
                
                # Generate analysis using the generate_text method
                analysis_result = llm_service.generate_text(
                    prompt=user_prompt,
                    system_message=system_prompt,
                    max_tokens=2000,
                    temperature=0.3
                )
                
                if analysis_result:
                    # Store as PaperAnalysis
                    analysis = PaperAnalysis(
                        paper_id=paper_id,
                        analysis_type=analysis_key,
                        content=analysis_result,
                        model_used=model_config.get('model', 'unknown'),
                        generated_at=datetime.utcnow()
                    )
                    
                    db.add(analysis)
                    
                    results.append({
                        'type': analysis_key,
                        'name': analysis_config['name'],
                        'description': analysis_config['description'],
                        'content': analysis_result,
                        'category': analysis_config.get('category', 'general'),
                        'status': 'success'
                    })
                    
                    logger.info(f"Completed {analysis_config['name']} analysis")
                else:
                    results.append({
                        'type': analysis_key,
                        'name': analysis_config['name'],
                        'description': analysis_config['description'],
                        'error': 'No response from LLM',
                        'status': 'failed'
                    })
                    
            except Exception as e:
                logger.error(f"Error in {analysis_config['name']} analysis: {e}")
                results.append({
                    'type': analysis_key,
                    'name': analysis_config['name'],
                    'description': analysis_config['description'],
                    'error': str(e),
                    'status': 'failed'
                })
        
        # Commit all successful analyses
        db.commit()
        
        return {
            'paper_id': paper_id,
            'paper_title': paper.title,
            'total_analyses': len(paper_analyses),
            'successful': len([r for r in results if r['status'] == 'success']),
            'failed': len([r for r in results if r['status'] == 'failed']),
            'results': results,
            'model_used': model_config.get('model', 'unknown')
        }
        
    except Exception as e:
        logger.error(f"Error generating automatic annotations: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{paper_id}/grobid/metadata")
    """Get GROBID-extracted metadata for a paper"""
    
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    import os
    
    # First, check if we have cached TEI XML from previous full processing
    tei_path = os.path.join('data', 'tei_xml', f"paper_{paper_id}_tei.xml")
    
    metadata = {}
    
    # Try to extract from cached TEI first
    if os.path.exists(tei_path):
        logger.info(f"Extracting metadata from cached TEI XML for paper {paper_id}")
        try:
            with open(tei_path, 'r', encoding='utf-8') as f:
                tei_xml = f.read()
            # The full TEI contains the header, so we can parse it the same way
            metadata = grobid_service._parse_header_xml(tei_xml)
            logger.info(f"Successfully extracted metadata from cached TEI: {len(metadata)} fields")
        except Exception as e:
            logger.error(f"Error reading cached TEI: {e}")
    
    # If no cached TEI or extraction failed, try processing the PDF
    if not metadata and paper.pdf_path and os.path.exists(paper.pdf_path):
        logger.info(f"Processing PDF header for metadata extraction for paper {paper_id}")
        try:
            # Process just the header for quick metadata extraction
            result = grobid_service._process_header(paper.pdf_path)
            
            if result.get('success'):
                metadata = grobid_service._parse_header_xml(result.get('tei_xml', ''))
                logger.info(f"Successfully extracted metadata from PDF header: {len(metadata)} fields")
            else:
                logger.error(f"GROBID header processing failed: {result.get('error')}")
        except Exception as e:
            logger.error(f"Error processing PDF header: {e}")
    
    # If still no metadata, try full processing
    if not metadata and paper.pdf_path and os.path.exists(paper.pdf_path):
        logger.info(f"Attempting full GROBID processing for paper {paper_id}")
        try:
            result = grobid_service.process_pdf(paper.pdf_path)
            if result.get('success'):
                metadata = result.get('metadata', {})
                
                # Cache the TEI for future use
                if result.get('full_document', {}).get('tei_xml'):
                    os.makedirs(os.path.dirname(tei_path), exist_ok=True)
                    grobid_service.save_tei_xml(
                        result['full_document']['tei_xml'],
                        tei_path
                    )
                    logger.info(f"Cached TEI XML for future use")
        except Exception as e:
            logger.error(f"Error in full GROBID processing: {e}")
    
    if not metadata:
        logger.warning(f"No metadata could be extracted for paper {paper_id}")
    
    return {
        'paper_id': paper_id,
        'current_title': paper.title,
        'grobid_metadata': metadata,
        'differences': {
            'title': metadata.get('title') != paper.title if metadata.get('title') else None,
            'has_new_authors': bool(metadata.get('authors')),
            'has_abstract': bool(metadata.get('abstract')),
            'has_keywords': bool(metadata.get('keywords'))
        }
    }

# Paper Entity Extraction Endpoints

@router.post("/{paper_id}/entities/extract")
def extract_paper_entities(
    paper_id: int,
    use_fast_model: bool = Query(False, description="Use fast model for extraction"),
):
    """Extract entities from a paper using the entity extraction service"""
    
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    if not paper.content:
        raise HTTPException(status_code=400, detail="Paper has no content to analyze")
    
    try:
        from app.services.entity_extraction_service import EntityExtractionService
        
        # Initialize service
        service = EntityExtractionService(use_fast_model=use_fast_model)
        
        # Prepare full paper content for analysis
        paper_text = f"""
Title: {paper.title}

Abstract: {paper.abstract or 'No abstract available'}

Authors: {paper.authors or 'Unknown'}

Full Paper Content:
{paper.content}
"""
        
        logger.info(f"Extracting entities from paper {paper_id} with {len(paper_text)} characters")
        
        # Extract entities using full paper content
        entities = service.extract_entities(text=paper_text, article_id=None)
        
        # Convert to response format
        entity_suggestions = [
            {
                "id": entity.id,
                "text": entity.text,
                "type": entity.entity_type,
                "confidence": entity.confidence,
                "context": entity.context,
                "normalized": entity.normalized,
                "metadata": entity.metadata
            }
            for entity in entities
        ]
        
        # Calculate statistics
        stats = {
            "total": len(entities),
            "by_type": {},
            "avg_confidence": sum(e.confidence for e in entities) / len(entities) if entities else 0
        }
        
        for entity in entities:
            if entity.entity_type not in stats["by_type"]:
                stats["by_type"][entity.entity_type] = 0
            stats["by_type"][entity.entity_type] += 1
        
        return {
            "entities": entity_suggestions,
            "stats": stats,
            "source": f"paper_{paper_id}",
            "model": service.model_name,
            "paper_id": paper_id,
            "paper_title": paper.title
        }
        
    except Exception as e:
        logger.error(f"Error extracting entities from paper {paper_id}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{paper_id}/entities/bulk-action")
def paper_bulk_entity_action(
    paper_id: int,
    request: dict,
):
    """Apply bulk actions to paper entity suggestions"""
    
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    try:
        entity_ids = request.get('entity_ids', [])
        action = request.get('action', '')
        entities_data = request.get('entities', [])
        
        results = {
            "total": len(entity_ids),
            "processed": 0,
            "failed": 0,
            "action": action
        }
        
        if action == "accept_all":
            from app.services.entity_extraction_service import EntityExtractionService, EntityExtraction
            
            service = EntityExtractionService()
            processed_count = 0
            failed_count = 0
            
            # Process each entity and save to ontology
            for entity_data in entities_data:
                try:
                    # Create entity object
                    entity = EntityExtraction(
                        text=entity_data.get('text', ''),
                        entity_type=entity_data.get('type', ''),
                        confidence=entity_data.get('confidence', 0.9),
                        context=entity_data.get('context', '')
                    )
                    
                    # Save entity to ontology as a tag concept
                    concept = service.save_entity_to_ontology(db, entity, entity_data.get('type', ''), "user")
                    
                    if concept:
                        # Add as tag to the paper
                        # Check if tag already exists for this paper (case-insensitive)
                        existing_tag = db.query(PaperTag).filter(
                            PaperTag.paper_id == paper_id,
                            func.lower(PaperTag.tag) == func.lower(concept.tag)
                        ).first()
                        
                        if not existing_tag:
                            # Add the tag to the paper
                            new_tag = PaperTag(
                                paper_id=paper_id,
                                tag=concept.tag,
                                tag_type="entity"  # Mark as entity-extracted tag
                            )
                            db.add(new_tag)
                            logger.info(f"Added tag '{concept.tag}' to paper {paper_id}")
                            
                            # Update vector store with new tag
                            try:
                                vector_store = get_vector_store()
                                # Get paper title for context
                                context = f"{paper.title}: {paper.abstract[:200] if paper.abstract else ''}"
                                vector_store.update_tag_incrementally(concept.tag, 'paper', context)
                                logger.info(f"Updated vector store with entity tag: {concept.tag}")
                            except Exception as e:
                                logger.error(f"Failed to update vector store for entity tag '{concept.tag}': {e}")
                                # Don't fail the request if vector store update fails
                        else:
                            logger.info(f"Tag '{concept.tag}' already exists on paper {paper_id}")
                        
                        processed_count += 1
                    else:
                        failed_count += 1
                        
                except Exception as e:
                    logger.error(f"Error processing entity: {str(e)}")
                    failed_count += 1
            
            # Commit all changes
            try:
                db.commit()
                results["processed"] = processed_count
                results["failed"] = failed_count
                results["message"] = f"Accepted {processed_count} entities, {failed_count} failed"
            except Exception as e:
                db.rollback()
                results["processed"] = 0
                results["failed"] = len(entity_ids)
                results["message"] = f"Failed to save entities: {str(e)}"
        
        elif action == "reject_all":
            results["processed"] = len(entity_ids)
            results["message"] = f"Rejected {len(entity_ids)} entities"
        
        else:
            raise HTTPException(status_code=400, detail=f"Invalid bulk action: {action}")
        
        return results
        
    except Exception as e:
        logger.error(f"Error in bulk entity action for paper {paper_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{paper_id}/cancel-processing")
def cancel_paper_processing(
    paper_id: int,
):
    """
    Cancel stuck PDF processing for a paper.
    Marks the paper as having a processing error so it can be retried later.
    """
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    try:
        # Mark paper as failed/cancelled
        paper.processed = False
        paper.processing_error = "Processing cancelled by user - Marker service timeout"
        
        # If there's a processor field, clear it
        if hasattr(paper, 'processor'):
            paper.processor = None
        if hasattr(paper, 'processor_used'):
            paper.processor_used = None
            
        db.commit()
        db.refresh(paper)  # Ensure the paper object is refreshed with the latest data
        
        logger.info(f"Cancelled processing for paper {paper_id}: processed={paper.processed}, error={paper.processing_error}")
        
        return {
            "success": True,
            "message": f"Processing cancelled for paper {paper_id}",
            "paper_id": paper_id
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error cancelling processing for paper {paper_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{paper_id}/process")
async def trigger_paper_processing(
    paper_id: int,
    background_tasks: BackgroundTasks,
):
    """
    Manually trigger PDF processing for a paper.
    This allows users to control when to use Marker/MinerU services.
    """
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Always allow reprocessing with Marker for testing/debugging purposes
    # This allows users to try different processors to see which works best
    if paper.processed:
        logger.info(f"Allowing reprocessing of paper {paper_id} with Marker (was processed with {paper.processor_used})")
        paper.processed = False  # Mark as not processed to trigger reprocessing
    
    # Check if PDF exists
    if not paper.pdf_path:
        raise HTTPException(status_code=400, detail="No PDF file found for this paper")
    
    # Check if file exists
    from pathlib import Path
    if not Path(paper.pdf_path).exists():
        raise HTTPException(status_code=400, detail=f"PDF file not found at: {paper.pdf_path}")
    
    try:
        # Clear any previous error
        paper.processing_error = None
        paper.processed = False
        db.commit()
        
        # Schedule async processing in background with Marker preference
        background_tasks.add_task(
            process_pdf_complete, 
            paper.id, 
            paper.pdf_path,
            'marker'  # Prefer Marker for regular process button
        )
        
        logger.info(f"Started manual processing for paper {paper_id}")
        
        return {
            "success": True,
            "message": f"Processing started for paper {paper_id}",
            "paper_id": paper_id
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error starting processing for paper {paper_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{paper_id}/process-mineru")
async def trigger_paper_processing_mineru(
    paper_id: int,
    background_tasks: BackgroundTasks,
):
    """
    Manually trigger PDF processing for a paper using MinerU service.
    MinerU is better for math-heavy and complex layout PDFs.
    """
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Always allow reprocessing with MinerU for testing/debugging purposes
    # This helps with testing image extraction improvements
    if paper.processed:
        logger.info(f"Allowing reprocessing of paper {paper_id} with MinerU (was processed with {paper.processor_used})")
        paper.processed = False  # Mark as not processed to trigger reprocessing
    
    # Check if PDF exists
    if not paper.pdf_path:
        raise HTTPException(status_code=400, detail="Paper has no PDF file")
    
    import os
    if not os.path.exists(paper.pdf_path):
        raise HTTPException(status_code=404, detail=f"PDF file not found: {paper.pdf_path}")
    
    try:
        # Start processing with MinerU in background
        background_tasks.add_task(
            process_pdf_complete,
            paper_id,
            paper.pdf_path,
            'mineru'  # Force MinerU processor
        )
        
        # Update paper status
        paper.processing_status = 'processing'
        paper.processing_started_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Started MinerU processing for paper {paper_id}")
        
        return {
            "success": True,
            "message": f"Started MinerU processing for paper {paper_id}",
            "paper_id": paper_id,
            "status": "processing"
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error starting MinerU processing for paper {paper_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    is_flagged: bool
    notes: Optional[str] = None

@router.post("/{paper_id}/flag")
def toggle_paper_flag(
    paper_id: int,
    flag_request: FlagRequest,
):
    """Toggle the flag status of a paper"""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail=f"Paper {paper_id} not found")
    
    paper.is_flagged = flag_request.is_flagged
    if flag_request.notes is not None:
        paper.flag_notes = flag_request.notes
    
    db.commit()
    
    return {
        "success": True,
        "paper_id": paper_id,
        "is_flagged": paper.is_flagged,
        "flag_notes": paper.flag_notes
    }