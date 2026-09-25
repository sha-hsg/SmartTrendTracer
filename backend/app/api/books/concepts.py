"""
Books concept tag endpoints: add and remove concept tags from books.
"""

from fastapi import APIRouter

from .utils import Any, Dict, Body, logging
from app.repositories import books_concepts as repo

router = APIRouter()

logger = logging.getLogger("app.api.books.concepts")


@router.post("/{book_id}/concepts")
def add_concept_to_book(book_id: str, concept_data: Dict[str, Any] = Body(...)):
    """Add a concept tag to a book"""
    return repo.add_concept_to_book(book_id=book_id, concept_data=concept_data)


@router.delete("/{book_id}/concepts/{concept_id}")
def remove_concept_from_book(book_id: str, concept_id: str):
    """Remove a concept tag from a book"""
    return repo.remove_concept_from_book(book_id=book_id, concept_id=concept_id)
