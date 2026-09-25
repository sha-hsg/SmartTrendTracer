"""Content CRUD, concept/tag management, and snippet routes for articles."""

from fastapi import APIRouter, Query, Body
from typing import Dict, Any
import re

from .utils import concept_service

router = APIRouter()

from app.repositories import article_content as repo


@router.post("/{article_id}/concepts")
def add_concept_to_article(
    article_id: str,
    text: str = Query(..., description="Text to create/find concept from")
):
    """Add a concept to an article"""
    return repo.add_concept_to_article(article_id=article_id, text=text, concept_service=concept_service)


@router.delete("/{article_id}/concepts/{concept_id}")
def remove_concept_from_article(article_id: str, concept_id: str):
    """Remove a concept from an article"""
    return repo.remove_concept_from_article(article_id=article_id, concept_id=concept_id, concept_service=concept_service)


@router.delete("/{article_id}/tags/{tag_name}")
def remove_tag_from_article(article_id: str, tag_name: str):
    """Remove a tag from an article by tag name (display_name)"""
    return repo.remove_tag_from_article(article_id=article_id, tag_name=tag_name, concept_service=concept_service)


@router.post("/{article_id}/snippets")
def add_snippet(article_id: str, snippet: Dict[str, Any] = Body(...)):
    """Add a snippet to an article"""
    return repo.add_snippet(article_id=article_id, snippet=snippet)


@router.delete("/{article_id}/snippets/{snippet_id}")
def remove_snippet(article_id: str, snippet_id: str):
    """Remove a snippet from an article"""
    return repo.remove_snippet(article_id=article_id, snippet_id=snippet_id)


@router.patch("/{article_id}")
def update_article(article_id: str, updates: Dict[str, Any] = Body(...)):
    """Update article fields (title, content, url, date, etc.)"""
    return repo.update_article(article_id=article_id, updates=updates)


@router.get("/without-author")
def get_articles_without_author(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200)
):
    """Get articles that don't have an author assigned"""
    return repo.get_articles_without_author(page=page, page_size=page_size)
