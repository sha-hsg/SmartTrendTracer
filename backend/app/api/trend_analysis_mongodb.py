"""
Trend Analysis API using MongoDB
Provides comprehensive trend analysis across tweets, papers, and articles
"""

from fastapi import APIRouter, Query
from typing import List, Optional
from datetime import datetime, timedelta, timezone
import logging
from app.repositories import trend_analysis as repo
from app.repositories import trend_analysis_queries as queries

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/top-concepts")
async def get_top_concepts(
    days: int = Query(7, ge=1, le=365),
    limit: int = Query(20, ge=1, le=100),
    content_type: Optional[str] = Query(None, description="Filter by content type: tweet, paper, article")
):
    """Get top concepts by usage count over a time period"""
    return repo.get_top_concepts(days=days, limit=limit, content_type=content_type)

@router.get("/velocity-leaders")
async def get_velocity_leaders(
    days: int = Query(7, ge=1, le=365),
    limit: int = Query(20, ge=1, le=100)
):
    """Get concepts with highest velocity (growth rate) in recent period"""
    return repo.get_velocity_leaders(days=days, limit=limit)

@router.get("/rising")
async def get_rising_trends(
    days: int = Query(7, ge=1, le=365),
    min_growth: float = Query(20.0, description="Minimum growth percentage"),
    limit: int = Query(20, ge=1, le=100)
):
    """Get concepts that are rising in popularity"""
    return repo.get_rising_trends(days=days, min_growth=min_growth, limit=limit)

@router.get("/declining")
async def get_declining_trends(
    days: int = Query(7, ge=1, le=365),
    min_decline: float = Query(20.0, description="Minimum decline percentage"),
    limit: int = Query(20, ge=1, le=100)
):
    """Get concepts that are declining in popularity"""
    return repo.get_declining_trends(days=days, min_decline=min_decline, limit=limit)

@router.get("/timeline")
async def get_trend_timeline(
    concept_ids: List[str] = Query(None, description="Concept IDs to track"),
    days: int = Query(30, ge=1, le=365),
    granularity: str = Query("daily", description="daily, weekly, or monthly"),
    max_concepts: int = Query(10, ge=1, le=50, description="Maximum concepts to return when none specified")
):
    """Get timeline data for specific concepts or overall activity"""
    return repo.get_trend_timeline(concept_ids=concept_ids, days=days, granularity=granularity, max_concepts=max_concepts)

@router.get("/overview")
async def get_trend_overview(
    days: int = Query(7, ge=1, le=365)
):
    """Get comprehensive trend overview combining all metrics"""

    # Get top concepts
    top_concepts = await get_top_concepts(days=days, limit=10, content_type=None)

    # Get velocity leaders
    velocity_leaders = await get_velocity_leaders(days=days, limit=10)

    # Get rising trends
    rising = await get_rising_trends(days=days, limit=10, min_growth=20.0)

    # Get declining trends
    declining = await get_declining_trends(days=days, limit=10, min_decline=20.0)

    # Calculate activity summary
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

    # Content type distribution
    content_distribution = list(queries.tag_instances_aggregate__get_trend_overview(cutoff_date))

    # Daily activity — created_at is native datetime after migration
    daily_activity = list(queries.tag_instances_aggregate__get_trend_overview_2(cutoff_date))

    # Get unique concepts
    unique_concept_ids = queries.tag_instances_distinct__get_trend_overview(cutoff_date)
    unique_concepts_count = len(unique_concept_ids) if unique_concept_ids else 0

    return {
        'period_days': days,
        'summary': {
            'total_annotations': sum(d['count'] for d in content_distribution),
            'unique_concepts': unique_concepts_count,
            'content_distribution': {d['_id']: d['count'] for d in content_distribution},
            'daily_average': sum(d['count'] for d in daily_activity) / max(len(daily_activity), 1)
        },
        'top_concepts': top_concepts['concepts'][:5],
        'velocity_leaders': velocity_leaders['velocity_leaders'][:5],
        'rising': rising['rising_concepts'][:5],
        'declining': declining['declining_concepts'][:5],
        'recent_activity': daily_activity[-7:] if len(daily_activity) > 7 else daily_activity
    }
