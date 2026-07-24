"""
Asynchronous Tag Reorganization API with Server-Sent Events (SSE)
Provides real-time updates during long-running GPT-5 reorganization process

Split into sub-modules:
  - routes.py: Core reorganization endpoints (start, stream, cancel, result, history)
  - debug_and_recovery.py: Debug endpoints (current-concepts)
  - recovery_and_apply.py: Recovery and apply endpoints (recover, apply-recovered, apply)
  - utils.py: Shared state, classes, and imports
"""

from fastapi import APIRouter

from .routes import router as routes_router
from .debug_and_recovery import router as debug_router
from .recovery_and_apply import router as recovery_apply_router

router = APIRouter()
router.include_router(routes_router)
router.include_router(debug_router)
router.include_router(recovery_apply_router)
