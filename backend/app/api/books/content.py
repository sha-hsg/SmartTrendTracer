"""
Book content retrieval endpoints.
"""

from fastapi import APIRouter

from .utils import (
    HTTPException,
    get_book_by_id,
)

router = APIRouter()


@router.get("/{book_id}/content")
def get_book_content(book_id: str):
    """Get book's markdown content"""
    book = get_book_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    if not book.get('markdown_content'):
        raise HTTPException(status_code=404, detail="Book content not available - processing may be pending")

    return {
        'book_id': book_id,
        'title': book['title'],
        'content': book['markdown_content'],
        'processing_status': book.get('processing_status', 'unknown')
    }
