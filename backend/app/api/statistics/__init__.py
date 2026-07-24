from fastapi import APIRouter

from app.api.statistics.content_stats import router as content_stats_router

router = APIRouter()
router.include_router(content_stats_router)
