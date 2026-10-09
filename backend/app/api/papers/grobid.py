"""
GROBID processing and metadata route handlers.

Covers: process_with_grobid (run GROBID on a paper PDF),
get_grobid_metadata (retrieve stored GROBID results),
and update_paper_metadata_grobid (update paper metadata fields).
"""

from .utils import (
    # Standard library re-exports used by the handlers
    datetime,
    timezone,
    # typing
    Any,
    Dict,
    # Third-party
    ObjectId,
    APIRouter,
    HTTPException,
    # Shared application state
    db,
    logger,
)
from app.repositories import papers_grobid as repo
from app.repositories import papers as papers_repo

router = APIRouter()


@router.post("/{paper_id}/grobid/process")
async def process_with_grobid(paper_id: str) -> Dict[str, Any]:
    """Process paper with GROBID service"""
    paper = papers_repo.find_paper_by_any_id(paper_id)

    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Check if PDF exists
    pdf_path = paper.get('pdf_path')
    if not pdf_path:
        raise HTTPException(status_code=400, detail="Paper has no PDF file")

    # Import GROBID service
    from app.services.grobid_service import GROBIDService
    grobid_service = GROBIDService()

    try:
        # Process with GROBID (not async)
        result = grobid_service.process_pdf(pdf_path)

        repo.store_grobid_result(paper, result, overwrite_authors=True)   # explicit user action

        # Format response for frontend
        response = {
            "success": True,
            "metadata": result,
            "metadata_extracted": bool(result.get('metadata')),
            "references_extracted": len(result.get('references', [])),
            "sections_extracted": len(result.get('sections', [])),
            "citations_extracted": len(result.get('citation_contexts', []))
        }

        return response
    except Exception as e:
        logger.error(f"GROBID processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{paper_id}/grobid/metadata")
def get_grobid_metadata(paper_id: str) -> Dict[str, Any]:
    """Get GROBID metadata for a paper"""
    return repo.get_grobid_metadata(paper_id=paper_id)



# Note: PUT /{paper_id}/metadata is handled in crud.py (update_paper_metadata)
# The GROBID metadata panel in the frontend uses the same endpoint.
