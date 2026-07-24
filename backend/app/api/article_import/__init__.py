from fastapi import APIRouter

from .url_import import router as url_import_router
from .conversion import router as conversion_router

router = APIRouter()
router.include_router(url_import_router)
router.include_router(conversion_router)
