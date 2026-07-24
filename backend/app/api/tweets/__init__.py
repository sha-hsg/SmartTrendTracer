"""
Complete MongoDB-based tweets API.
All data operations use MongoDB - no SQLite dependencies.

Split into sub-modules by responsibility:
  - browse: Listing, search, facets, single-tweet retrieval, stats
  - concepts: Add/remove concept tags on tweets
  - annotation: Batch annotation via LLM
"""

from fastapi import APIRouter
from typing import List, Dict

from .browse import router as browse_router
from .browse import get_tweets
from .concepts import router as concepts_router
from .annotation import router as annotation_router

router = APIRouter()
router.include_router(browse_router)
router.include_router(concepts_router)
router.include_router(annotation_router)

# Re-register the root listing endpoint on the empty-string path
# (the original monolithic file had both @router.get("/") and @router.get(""))
router.add_api_route("", get_tweets, methods=["GET"], response_model=List[Dict])
