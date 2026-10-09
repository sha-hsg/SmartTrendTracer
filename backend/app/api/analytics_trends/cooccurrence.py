"""
Concept association endpoint for analytics trends (app.services.trend_core).
"""

from fastapi import APIRouter, Query

from app.services import trend_core

router = APIRouter()


@router.get("/cooccurrence")
def get_cooccurrence_data(
    days: int = Query(30, ge=7, le=90, description="Number of days to analyze"),
    top_n: int = Query(25, ge=10, le=50, description="Number of concepts in the matrix"),
    min_cooccurrence: int = Query(3, ge=1, le=10, description="Minimum documents per pair (at least 3)")
):
    """
    Concept pairs that appear together more often than chance (NPMI), with
    at least `min_cooccurrence` documents from two sources; flags pairs that
    are new against the previous window.
    """
    return {"period_days": days,
            **trend_core.associations(days=days, top_n=top_n, min_cooccurrence=min_cooccurrence)}
