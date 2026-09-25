"""
MongoDB-based Trends Analysis API with Full Implementation
Provides comprehensive trend analysis for tweets, articles, and papers
"""

from fastapi import APIRouter, Query
from typing import Optional
import logging
from app.repositories import trends as repo
from app.repositories.trends import _batch_fetch_concept_counts, _batch_fetch_concept_counts_by_date, _batch_lookup_concepts  # noqa: F401 (moved)

logger = logging.getLogger(__name__)
router = APIRouter()









@router.get("/analysis")
def get_trend_analysis(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    content_type: Optional[str] = Query(None, description="Filter by content type (tweet/article/paper)")
):
    """
    Get comprehensive trend analysis across all content types with real data.
    Uses batch queries for performance.
    """
    return repo.get_trend_analysis(days=days, content_type=content_type)

