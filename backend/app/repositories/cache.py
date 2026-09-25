"""Tiny in-process TTL cache for expensive aggregate queries."""
from datetime import datetime, timezone
from typing import Any, Dict

_cache: Dict[str, Dict[str, Any]] = {}
CACHE_TTL_SECONDS = 60


def get_cached(key: str, builder, ttl_seconds: int = CACHE_TTL_SECONDS):
    """Return the cached value for key, rebuilding it after ttl_seconds."""
    now = datetime.now(timezone.utc)
    entry = _cache.get(key)
    if entry and (now - entry['at']).total_seconds() < ttl_seconds:
        return entry['value']
    value = builder()
    _cache[key] = {'value': value, 'at': now}
    return value
