"""
Paper metadata route handlers.

Covers: metadata update, flag toggle, star rating, and generic field patching.
"""

from .utils import Any, Dict, APIRouter, Body, Query
from app.repositories import papers_metadata as repo

router = APIRouter()


@router.put("/{paper_id}/content")
async def update_paper_content(paper_id: str, data: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Update paper content/markdown content"""
    return repo.update_paper_content(paper_id=paper_id, data=data)


@router.put("/{paper_id}/metadata")
def update_paper_metadata(paper_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Update paper metadata"""
    return repo.update_paper_metadata(paper_id=paper_id, metadata=metadata)


@router.post("/{paper_id}/flag")
def toggle_paper_flag(paper_id: str, flag_data: Dict[str, Any]) -> Dict[str, Any]:
    """Toggle the flag status of a paper"""
    return repo.toggle_paper_flag(paper_id=paper_id, flag_data=flag_data)


@router.patch("/{paper_id}/rating")
def set_paper_rating(
    paper_id: str,
    rating: int = Query(..., ge=0, le=5, description="Rating 1-5, or 0 to clear")
) -> Dict[str, Any]:
    """Set user rating for a paper (1-5 stars, 0 to clear rating)"""
    return repo.set_paper_rating(paper_id=paper_id, rating=rating)


@router.patch("/{paper_id}")
def patch_paper_fields(paper_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Patch specific paper fields including import_url and import_source
    """
    return repo.patch_paper_fields(paper_id=paper_id, updates=updates)
