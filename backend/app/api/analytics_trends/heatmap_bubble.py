"""
Heatmap and bubble chart endpoints for analytics trends (app.services.trend_core).
"""

from fastapi import APIRouter, Query

from app.services import trend_core

router = APIRouter()


@router.get("/heatmap")
def get_trends_heatmap(
    days: int = Query(14, ge=7, le=90, description="Number of days to analyze"),
    top_n: int = Query(20, ge=5, le=50, description="Number of top concepts")
):
    """Daily document counts of the window's most active concepts (hub
    concepts such as "AI" left out), up to the last tagged day."""
    return trend_core.heatmap(days=days, top_n=top_n)


@router.get("/bubble-chart")
def get_bubble_chart_data(
    days: int = Query(30, ge=7, le=365, description="Number of days to analyze"),
    limit: int = Query(50, ge=10, le=100, description="Maximum bubbles to return")
):
    """
    Concept age against growth:
    X = days since the concept first occurred
    Y = growth factor of the window against the concept's own baseline
    Size = documents in the window, colour = dominant channel
    """
    return trend_core.bubbles(days=days, limit=limit)
