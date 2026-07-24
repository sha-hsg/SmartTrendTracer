"""Articles API package - split from articles_mongodb.py."""
from fastapi import APIRouter
from .browse import router as browse_router
from .content import router as content_router
from .content_processing import router as content_processing_router
from .authors import router as authors_router

router = APIRouter()
# NOTE: browse_router MUST be registered last — it contains the dynamic route
# GET /{article_id}, which would otherwise shadow the static paths
# GET /authors, GET /authors/all (authors_router) and GET /without-author
# (content_router).
router.include_router(content_router)
router.include_router(content_processing_router)
router.include_router(authors_router)
router.include_router(browse_router)
