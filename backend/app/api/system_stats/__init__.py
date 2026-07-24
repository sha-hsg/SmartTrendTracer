"""
System Statistics API package.
Comprehensive analytics across all data sources and system components.

Sub-modules:
- overview_and_content: System overview, content stats, author stats
- analytics: Tag statistics, trend analysis, cross-source correlations
- system_and_llm: System health, LLM usage, summary, circuit breaker
"""

from fastapi import APIRouter

from .overview_and_content import router as overview_content_router
from .analytics import router as analytics_router
from .system_and_llm import router as system_llm_router

router = APIRouter()

router.include_router(overview_content_router)
router.include_router(analytics_router)
router.include_router(system_llm_router)
