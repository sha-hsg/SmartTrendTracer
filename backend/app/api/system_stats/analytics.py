"""
Tag, trend, and cross-source analytics endpoints.
Tag statistics, trend analysis, cross-source correlations.
"""
from fastapi import APIRouter


router = APIRouter(
    prefix="/api/system",
    tags=["system-statistics"]
)

from app.repositories import system_analytics as repo
from app.repositories.system_analytics import get_tag_statistics  # noqa: F401 (re-export)


@router.get("/statistics/trends")
async def get_trend_statistics():
    """Get trend analysis and growth statistics"""
    return repo.get_trend_statistics()


@router.get("/statistics/cross-source")
async def get_cross_source_statistics():
    """Get cross-source analytics and correlations"""
    return repo.get_cross_source_statistics()
