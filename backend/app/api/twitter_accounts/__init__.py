from fastapi import APIRouter

from .crud import router as crud_router
from .stats import router as stats_router
from .collection import router as collection_router

router = APIRouter()

# Static-path routers first, parametric catch-all last
router.include_router(stats_router)
router.include_router(collection_router)
router.include_router(crud_router)
