"""
API endpoints for managing references in the normalized references collection
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.database.mongodb import get_database
import logging
from app.repositories import references as repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/references", tags=["references"])

# MongoDB connection
db = get_database()

@router.get("/")
async def get_all_references(
    search: Optional[str] = Query(None, description="Search in title, authors, venue"),
    year: Optional[int] = Query(None, description="Filter by year"),
    has_doi: Optional[bool] = Query(None, description="Filter by DOI availability"),
    in_system: Optional[bool] = Query(None, description="Filter by whether paper exists in system"),
    min_citations: Optional[int] = Query(None, description="Minimum citation count"),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get all unique references across all papers with filtering and search"""
    return repo.get_all_references(search=search, year=year, has_doi=has_doi, in_system=in_system, min_citations=min_citations, limit=limit, offset=offset)

@router.get("/top-cited")
async def get_top_cited_references(limit: int = Query(20, le=100)):
    """Get the most cited references across all papers"""
    return repo.get_top_cited_references(limit=limit)

@router.get("/importable")
async def get_importable_references(limit: int = Query(50, le=200)):
    """Get references that can be imported as new papers (have DOI/ArXiv but not in system)"""
    return repo.get_importable_references(limit=limit)

@router.get("/statistics")
async def get_reference_statistics():
    """Get statistics about the references collection"""
    return repo.get_reference_statistics()

@router.post("/{reference_id}/import")
async def import_reference_as_paper(reference_id: str):
    """Import a reference as a new paper using its DOI or ArXiv ID"""
    
    ref = repo.find_reference(reference_id)
    
    if not ref:
        raise HTTPException(status_code=404, detail="Reference not found")
    
    if ref.get('is_in_system'):
        raise HTTPException(status_code=400, detail="Reference already exists as a paper")
    
    # Determine import method
    if ref.get('arxiv_id'):
        # Import from ArXiv
        from app.services.arxiv_import_service import ArxivImportService
        service = ArxivImportService()
        
        try:
            result = await service.import_paper(ref['arxiv_id'])
            
            if result.get('paper_id'):
                # Mark reference as in system + create citation links
                repo.mark_reference_imported(ref, result['paper_id'])
                
                return {
                    'success': True,
                    'paper_id': result['paper_id'],
                    'message': f"Successfully imported from ArXiv: {ref['arxiv_id']}"
                }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to import from ArXiv: {str(e)}")
    
    elif ref.get('doi'):
        # TODO: Implement DOI import (CrossRef, Unpaywall, etc.)
        raise HTTPException(status_code=501, detail="DOI import not yet implemented")
    
    else:
        raise HTTPException(status_code=400, detail="Reference has no DOI or ArXiv ID for import")

@router.post("/{reference_id}/generate-bibtex")
async def generate_bibtex(reference_id: str):
    """Generate BibTeX entry for a reference"""
    return repo.generate_bibtex(reference_id=reference_id)
