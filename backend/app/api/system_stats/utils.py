"""
Shared utilities for the system_stats package.
Database connection, logger, and caching mechanism.
"""
from typing import Dict, Any
from datetime import datetime, timezone, timedelta
import logging

from app.database.mongodb import get_database

logger = logging.getLogger(__name__)

# MongoDB connection
db = get_database()

CACHE_TTL = timedelta(seconds=60)
_cache: Dict[str, Dict[str, Any]] = {}


def _get_cached(key: str, builder):
    now = datetime.now(timezone.utc)
    entry = _cache.get(key)
    if entry and entry["expires_at"] > now:
        return entry["value"]

    value = builder()
    _cache[key] = {"value": value, "expires_at": now + CACHE_TTL}
    return value
