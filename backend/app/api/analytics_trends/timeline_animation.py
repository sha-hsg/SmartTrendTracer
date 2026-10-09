"""
Animated timeline endpoint for analytics trends (app.services.trend_core).
"""

from fastapi import APIRouter, Query

from app.services import trend_core

router = APIRouter()


@router.get("/animated-timeline")
def get_animated_timeline_data(
    days: int = Query(30, ge=7, le=90, description="Number of days to analyze"),
    top_n: int = Query(15, ge=5, le=30, description="Concepts per frame")
):
    """
    Bar-chart race: each daily frame ranks concepts by their documents in the
    7 days up to that day, so topics enter and leave.
    """
    return trend_core.timeline(days=days, top_n=top_n)
