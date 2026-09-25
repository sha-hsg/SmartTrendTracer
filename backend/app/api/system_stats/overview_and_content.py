"""
Overview, content, and author statistics endpoints.
High-level system overview, detailed content stats, author analytics.
"""
from fastapi import APIRouter


router = APIRouter(
    prefix="/api/system",
    tags=["system-statistics"]
)

from app.repositories import system_overview as repo
from app.repositories.system_overview import get_system_overview  # noqa: F401 (re-export)


@router.get("/statistics/content")
async def get_content_statistics():
    """Get detailed content statistics across all sources"""
    return repo.get_content_statistics()


@router.get("/statistics/authors")
async def get_author_statistics():
    """Get detailed author and contributor statistics"""
    return repo.get_author_statistics()
