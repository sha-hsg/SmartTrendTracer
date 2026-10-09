"""
Concept network endpoint for analytics trends (app.services.trend_core).
"""

from fastapi import APIRouter, Query

from app.services import trend_core

router = APIRouter()


@router.get("/network")
def get_concept_network(
    days: int = Query(30, ge=1, le=90, description="Number of days to analyze"),
    top_n: int = Query(40, ge=10, le=100, description="Number of concepts")
):
    """
    Graph of the strongest concept associations (NPMI edges, node size =
    documents in the window, colour = cluster).
    """
    return trend_core.network(days=days, top_n=top_n)
