"""API endpoints for article preview management"""

from fastapi import APIRouter
from app.repositories import article_preview as repo
from app.database.mongodb import get_database
import re
from typing import Dict
import mdformat

router = APIRouter()

# MongoDB connection
db = get_database()




# Moved to the shared helper so collectors/importers use the same cleaning


@router.post("/regenerate/{article_id}")
async def regenerate_article_preview(article_id: str) -> Dict:
    """
    Regenerate preview for a specific article
    
    Args:
        article_id: MongoDB ObjectId as string
        
    Returns:
        Dict with success status and new preview
    """
    return repo.regenerate_article_preview(article_id=article_id)


@router.post("/beautify/{article_id}")
async def beautify_article_markdown(article_id: str) -> Dict:
    """
    Beautify the markdown content of an article
    
from app.repositories import article_preview as repo
from app.repositories.article_preview import beautify_markdown  # noqa: F401 (moved)
    Args:
        article_id: MongoDB ObjectId as string
        
    Returns:
        Dict with success status and beautified markdown
    """
    return repo.beautify_article_markdown(article_id=article_id)
