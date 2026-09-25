"""
MongoDB-based User Trends API
Provides per-user trend analysis for tweets
"""

from fastapi import APIRouter, Query
from app.database.mongodb import get_database
import logging
from app.repositories import user_trends as repo

logger = logging.getLogger(__name__)
router = APIRouter()

# MongoDB connection
db = get_database()

@router.get("/per-user")
def get_per_user_trends(
    hours: int = Query(168, ge=1, le=720, description="Number of hours to analyze (default: 7 days)")
):
    """
    Get trend analysis broken down by user/author with real data
    Returns activity and concept usage per Twitter account
    """
    return repo.get_per_user_trends(hours=hours)

@router.get("/user/{username}")
def get_user_trends(
    username: str,
    days: int = Query(30, ge=1, le=90, description="Number of days to analyze")
):
    """
    Get detailed trend analysis for a specific user
    """
    return repo.get_user_trends(username=username, days=days)
