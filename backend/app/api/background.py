"""
API endpoints for background task management
"""
from fastapi import APIRouter, HTTPException
from app.background_tasks import (
    get_collection_status,
    start_background_collection,
    run_background_collection
)
from app.persistent_rate_limiter import get_persistent_rate_limiter
from concurrent.futures import ThreadPoolExecutor
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/status")
async def get_background_status():
    """Get status of background collection tasks"""
    status = get_collection_status()
    rate_limiter = get_persistent_rate_limiter()
    
    wait_time = 0
    if not rate_limiter.can_make_request():
        wait_time = rate_limiter.get_wait_time()
    
    return {
        "collection_in_progress": status["in_progress"],
        "rate_limited": status["rate_limited"],
        "wait_time_seconds": wait_time,
        "wait_time_minutes": round(wait_time / 60, 1) if wait_time > 0 else 0
    }

@router.post("/trigger")
async def trigger_collection():
    """Manually trigger tweet collection in background"""
    status = get_collection_status()
    
    if status["in_progress"]:
        return {
            "status": "already_running",
            "message": "Collection is already in progress"
        }
    
    if status["rate_limited"]:
        rate_limiter = get_persistent_rate_limiter()
        wait_time = rate_limiter.get_wait_time()
        return {
            "status": "rate_limited",
            "message": f"Rate limited. Please wait {wait_time} seconds ({wait_time/60:.1f} minutes)",
            "wait_time_seconds": wait_time
        }
    
    # Start collection in background
    executor = ThreadPoolExecutor(max_workers=1)
    executor.submit(run_background_collection)
    
    return {
        "status": "started",
        "message": "Collection triggered successfully in background"
    }

@router.post("/clear-rate-limit")
async def clear_rate_limit():
    """Clear rate limit state (use with caution)"""
    try:
        rate_limiter = get_persistent_rate_limiter()
        rate_limiter.reset()
        return {
            "status": "success",
            "message": "Rate limit state cleared"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))