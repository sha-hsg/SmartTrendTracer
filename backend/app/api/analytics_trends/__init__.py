"""Analytics Trends API package - split from analytics_trends_mongodb.py."""
from fastapi import APIRouter
from .visualizations import router as viz_router
from .analysis import router as analysis_router
from .cooccurrence import router as cooccurrence_router
from .heatmap_bubble import router as heatmap_bubble_router
from .network_correlation import router as network_correlation_router
from .timeline_animation import router as timeline_animation_router

router = APIRouter()
router.include_router(viz_router)
router.include_router(analysis_router)
router.include_router(cooccurrence_router)
router.include_router(heatmap_bubble_router)
router.include_router(network_correlation_router)
router.include_router(timeline_animation_router)
