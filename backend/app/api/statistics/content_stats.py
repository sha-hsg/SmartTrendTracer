"""
Per-content-type statistics (concepts).
"""

from fastapi import APIRouter, Query
from typing import Optional
import logging
from app.repositories import statistics_content_stats as repo

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/concepts/detailed")
def get_detailed_concept_statistics(
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    days: Optional[int] = Query(None, ge=1, le=365, description="Limit to recent days"),
    include_hierarchy: bool = Query(True, description="Include hierarchy information")
):
    """Get detailed concept statistics with usage patterns"""
    return repo.get_detailed_concept_statistics(content_type=content_type, days=days, include_hierarchy=include_hierarchy)
