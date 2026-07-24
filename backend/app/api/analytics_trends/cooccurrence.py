"""
Co-occurrence analysis endpoint for analytics trends.
Split from analysis.py to keep file sizes under 600 LOC.
"""

from fastapi import APIRouter, Query

from .utils import (
    logger,
    db,
    get_date_range,
)

router = APIRouter()


@router.get("/cooccurrence")
def get_cooccurrence_data(
    days: int = Query(30, ge=7, le=90, description="Number of days to analyze"),
    top_n: int = Query(25, ge=10, le=50, description="Number of top concepts"),
    min_cooccurrence: int = Query(2, ge=1, le=10, description="Minimum co-occurrence count")
):
    """
    Get concept co-occurrence matrix and top pairs.
    Shows which concepts frequently appear together in the same content.
    """
    from app.services.anomaly_detection import get_concept_cooccurrence

    start_date, end_date = get_date_range(days)

    cooc_data = get_concept_cooccurrence(
        db,
        days=days,
        min_cooccurrence=min_cooccurrence,
        top_n=top_n
    )

    return {
        "period_days": days,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "concepts": cooc_data['concepts'],
        "concept_ids": cooc_data['concept_ids'],
        "matrix": cooc_data['matrix'],
        "pairs": cooc_data['pairs'],
        "total_documents": cooc_data['total_documents']
    }
