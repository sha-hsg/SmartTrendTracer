"""
MongoDB-based Media Gallery API for Twitter media
"""

import re

from fastapi import APIRouter, Query
from app.database.mongodb import get_database
from typing import Optional
import logging
from app.repositories import media_gallery as repo
from app.repositories.media_gallery import GALLERY_SORT_OPTIONS, _empty_gallery_response  # noqa: F401 (moved)

logger = logging.getLogger(__name__)
router = APIRouter()

# MongoDB connection
db = get_database()

# Server-side sort options (tweet schema uses metrics.like_count / metrics.retweet_count)




@router.get("/gallery")
async def get_media_gallery(
    page: int = Query(1, ge=1, le=10000),
    page_size: int = Query(20, ge=1, le=100),
    days: int = Query(7, ge=1, le=365),
    media_type: Optional[str] = Query(None, description="Filter by media type: photo, video, animated_gif"),
    author: Optional[str] = Query(None, description="Filter by author username"),
    search: Optional[str] = Query(None, description="Filter by tweet text (case-insensitive substring)"),
    tag: Optional[str] = Query(None, description="Filter by concept tag (name, display name or slug)"),
    sort_by: str = Query("date_desc", description="Sort order: date_desc, date_asc, likes_desc, retweets_desc, engagement")
):
    """Get media items from tweets with pagination and filters"""
    return repo.get_media_gallery(page=page, page_size=page_size, days=days, media_type=media_type, author=author, search=search, tag=tag, sort_by=sort_by)

@router.get("/stats")
async def get_media_stats(
    days: int = Query(7, ge=1, le=365)
):
    """Get statistics about media in tweets"""
    return repo.get_media_stats(days=days)

@router.get("/authors")
async def get_media_authors(
    days: int = Query(7, ge=1, le=365)
):
    """Get list of authors who have posted media"""
    return repo.get_media_authors(days=days)

@router.get("/types")
async def get_media_types():
    """Get available media types"""
    return repo.get_media_types()
