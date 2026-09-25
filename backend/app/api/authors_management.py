"""
Author Management API Endpoints

Provides comprehensive author management functionality including:
- List all authors with statistics
- Get author details
- Update author information
- Delete authors
- Find similar authors for merging
- Merge duplicate authors
- Author analytics
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any

from app.database.mongodb import get_database
from app.services.author_service import AuthorService

router = APIRouter()

# MongoDB connection
db = get_database()

# Initialize author service
author_service = AuthorService(db)


# Pydantic Models
class AuthorResponse(BaseModel):
    id: str
    name: str
    canonical_name: Optional[str] = None
    subdomain: Optional[str] = None
    email: Optional[str] = None
    article_count: int = 0
    last_article_date: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class AuthorUpdateRequest(BaseModel):
    name: Optional[str] = None
    canonical_name: Optional[str] = None
    subdomain: Optional[str] = None
    email: Optional[EmailStr] = None


class AuthorMergeRequest(BaseModel):
    source_id: str
    target_id: str


class FindSimilarRequest(BaseModel):
    name: str
    threshold: float = 0.85

from app.repositories import authors as repo


@router.get("/", response_model=Dict[str, Any])
def list_authors(
    page: int = Query(1, ge=1, le=10000),
    page_size: int = Query(50, ge=1, le=200),
    search: Optional[str] = None,
    sort_by: str = Query("article_count", regex="^(name|article_count|last_article_date|created_at)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$")
):
    """
    List all authors with pagination, search, and sorting
    """
    return repo.list_authors(page=page, page_size=page_size, search=search, sort_by=sort_by, sort_order=sort_order)


@router.get("/{author_id}", response_model=Dict[str, Any])
def get_author(author_id: str):
    """
    Get detailed author information including articles
    """
    return repo.get_author(author_id=author_id)


@router.put("/{author_id}")
def update_author(author_id: str, update_data: AuthorUpdateRequest):
    """
    Update author information
    """
    return repo.update_author(author_id=author_id, update_data=update_data)


@router.delete("/{author_id}")
def delete_author(author_id: str):
    """
    Delete author (only if article_count is 0)
    """
    return repo.delete_author(author_id=author_id)


@router.post("/find-similar")
def find_similar_authors(request: FindSimilarRequest):
    """
    Find authors with similar names (for merge detection)
    """
    return repo.find_similar_authors(request=request, author_service=author_service)


@router.post("/merge")
def merge_authors(request: AuthorMergeRequest):
    """
    Merge two author records (source → target)
    """
    return repo.merge_authors(request=request, author_service=author_service)


@router.get("/analytics/overview")
def get_author_analytics():
    """
    Get analytics data for author dashboard
    """
    return repo.get_author_analytics()
