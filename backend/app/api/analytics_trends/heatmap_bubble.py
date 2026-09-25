"""
Heatmap and bubble chart endpoints for analytics trends.
Split from visualizations.py.
"""

from fastapi import APIRouter, Query


from app.repositories import analytics_trends_heatmap_bubble as repo

router = APIRouter()


@router.get("/heatmap")
def get_trends_heatmap(
    days: int = Query(14, ge=7, le=90, description="Number of days to analyze"),
    top_n: int = Query(20, ge=5, le=50, description="Number of top concepts")
):
    """
    Get heatmap data for concept activity over time.
    Returns a matrix of concepts x dates with activity counts.
    """
    return repo.get_trends_heatmap(days=days, top_n=top_n)


@router.get("/bubble-chart")
def get_bubble_chart_data(
    days: int = Query(30, ge=7, le=365, description="Number of days to analyze"),
    limit: int = Query(50, ge=10, le=100, description="Maximum bubbles to return")
):
    """
    Get bubble chart data for concept importance and growth.
    X = Days since first occurrence
    Y = Velocity (% change)
    Size = Total count
    Color = Entity type
    """
    return repo.get_bubble_chart_data(days=days, limit=limit)
