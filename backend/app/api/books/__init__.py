"""
Books API package - split from monolithic books_mongodb.py.

Sub-modules:
- crud: List, get, create, update, delete books
- facets: Filter options and statistics
- concepts: Concept tag management
- content: Markdown content retrieval
- processing: Queue-based and direct book processing
"""

from fastapi import APIRouter

from .crud import router as crud_router
from .facets import router as facets_router
from .concepts import router as concepts_router
from .content import router as content_router
from .processing import router as processing_router

router = APIRouter()

# NOTE: facets_router MUST be registered before crud_router — otherwise the
# static path GET /facets is shadowed by the dynamic GET /{book_id} route.
router.include_router(facets_router)
router.include_router(crud_router)
router.include_router(concepts_router)
router.include_router(content_router)
router.include_router(processing_router)
