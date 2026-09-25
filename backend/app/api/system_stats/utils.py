"""
Shared utilities for the system_stats package.
Database connection, logger, and caching mechanism.
"""
from typing import Dict, Any
from datetime import datetime, timezone, timedelta
import logging


logger = logging.getLogger(__name__)


# Cache lives in the data-access layer; kept under the old name for callers
from app.repositories.cache import get_cached as _get_cached  # noqa: E402,F401
