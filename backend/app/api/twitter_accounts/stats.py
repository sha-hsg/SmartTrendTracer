from fastapi import APIRouter, Depends, Query

from app.database.mongodb import get_database

router = APIRouter()

# Tier collection intervals (in minutes)

from app.repositories import twitter_account_stats as repo


@router.get("/stats")
def get_account_stats(db=Depends(get_database)):
    """Get collection statistics per account."""
    return repo.get_account_stats()


@router.get("/dashboard")
def get_collection_dashboard(db=Depends(get_database)):
    """Get comprehensive collection dashboard statistics."""
    return repo.get_collection_dashboard()


@router.get("/collection-history")
def get_collection_history(
    days: int = Query(7, ge=1, le=90, description="Number of days to look back"),
    db=Depends(get_database)
):
    """Get tweet collection history over time."""
    return repo.get_collection_history(days=days)


@router.get("/collector-status")
def get_collector_status(db=Depends(get_database)):
    """Get the current status of the tweet collector service."""
    return repo.get_collector_status()


@router.get("/live-progress")
def get_live_collection_progress(db=Depends(get_database)):
    """
    Get real-time collection progress from the collector service.
    Returns current status, which account is being processed, and progress metrics.
    """
    return repo.get_live_collection_progress()


@router.get("/usage")
def get_usage_stats(db=Depends(get_database)):
    """Get Twitter API usage statistics for the current month."""
    return repo.get_usage_stats()
