"""Author management routes for articles."""

from fastapi import APIRouter, Query, Body
from typing import List, Dict, Any


router = APIRouter()

from app.repositories import article_authors as repo


@router.get("/authors/all")
def get_all_authors():
    """Get all Substack authors from MongoDB"""
    return repo.get_all_authors()


@router.post("/authors")
def create_author(author_data: Dict[str, str] = Body(...)):
    """Create a new author"""
    return repo.create_author(author_data=author_data)


@router.put("/authors/{author_id}")
def update_author(author_id: str, author_data: Dict[str, str] = Body(...)):
    """Update an author's details"""
    return repo.update_author(author_id=author_id, author_data=author_data)


@router.delete("/authors/{author_id}")
def delete_author(author_id: str, delete_articles: bool = Query(False)):
    """Delete an author and optionally their articles"""
    return repo.delete_author(author_id=author_id, delete_articles=delete_articles)


@router.put("/{article_id}/author")
def update_article_author(article_id: str, author_data: Dict[str, Any] = Body(...)):
    """Update an article's author - can be existing ID or new author name"""
    return repo.update_article_author(article_id=article_id, author_data=author_data)


@router.post("/authors/{author_id}/assign-articles")
def assign_articles_to_author(author_id: str, article_ids: List[str] = Body(...)):
    """Assign multiple articles to an author"""
    return repo.assign_articles_to_author(author_id=author_id, article_ids=article_ids)
