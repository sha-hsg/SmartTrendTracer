"""
Topic Explorer API
Provides topic frequency over time and correlation analysis
"""

from fastapi import APIRouter, Query
from typing import Optional
import logging
from app.repositories import topic_explorer as repo
from app.repositories.topic_explorer import TOPIC_COLORS, ensure_aware, get_date_from_content, group_by_granularity, parse_date  # noqa: F401 (moved)

logger = logging.getLogger(__name__)
router = APIRouter()


# Color palette for topics










@router.get("/frequency")
async def get_topic_frequency(
    concept_ids: str = Query(..., description="Comma-separated concept IDs"),
    source_types: str = Query("tweet,article,paper", description="Comma-separated content types"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format or YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format or YYYY-MM-DD)"),
    granularity: str = Query("week", description="Time granularity: day, week, month")
):
    """
    Get topic frequency over time for selected concepts.
    Returns time series data suitable for line charts.
    """
    return repo.get_topic_frequency(concept_ids=concept_ids, source_types=source_types, start_date=start_date, end_date=end_date, granularity=granularity)


@router.get("/correlation")
async def get_topic_correlation(
    source_types: str = Query("tweet,article,paper", description="Comma-separated content types"),
    min_count: int = Query(5, ge=1, le=100, description="Minimum occurrences to include topic"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format or YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format or YYYY-MM-DD)"),
    limit: int = Query(30, ge=5, le=100, description="Maximum number of topics to analyze")
):
    """
    Get topic co-occurrence correlation data.
    Returns data suitable for scatter plots showing topic relationships.
    """
    return repo.get_topic_correlation(source_types=source_types, min_count=min_count, start_date=start_date, end_date=end_date, limit=limit)


@router.get("/popular")
async def get_popular_topics(
    source_types: str = Query("tweet,article,paper", description="Comma-separated content types"),
    days: int = Query(90, ge=1, le=3650, description="Number of days to look back"),
    limit: int = Query(50, ge=5, le=200, description="Maximum number of topics")
):
    """
    Get most popular topics for the topic selector.
    """
    return repo.get_popular_topics(source_types=source_types, days=days, limit=limit)
