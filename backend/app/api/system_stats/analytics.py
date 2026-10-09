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
    """Get trend analysis and growth statistics. Hot topics and emerging tags
    come from the trend core (same numbers as the Trend Dashboard; the old
    tag-creation-date comparison counted tagging batches, not content)."""
    from app.services import trend_core
    stats = repo.get_trend_statistics()
    overview = trend_core.overview(hours=168, limit=10)
    hot = [{"topic": t["display_name"], "mentions": t["count"], "trend": "up"} for t in overview["hot_topics"]]
    steady = [{"topic": t["display_name"], "mentions": t["count"], "trend": "stable"} for t in overview["stable"]]
    stats["hot_topics"] = (hot + steady)[:5]
    stats["emerging_tags"] = [{"tag": t["display_name"], "growth_rate": t["velocity"]} for t in overview["hot_topics"]]
    stats["data_through"] = overview["time_range"]["data_through"]
    return stats


@router.get("/statistics/cross-source")
async def get_cross_source_statistics():
    """Get cross-source analytics and correlations"""
    return repo.get_cross_source_statistics()
