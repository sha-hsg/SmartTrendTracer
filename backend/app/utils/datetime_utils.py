"""Datetime parsing helpers."""
from datetime import datetime
from typing import Any, Optional


def normalize_datetime(dt_value: Any) -> Optional[datetime]:
    """
    Normalize various datetime representations to a datetime object.
    Handles: datetime objects, ISO strings, timestamps (int/float).
    Returns None if conversion fails.
    """
    if dt_value is None:
        return None
    if isinstance(dt_value, datetime):
        return dt_value
    if isinstance(dt_value, str):
        try:
            # Try ISO format first
            return datetime.fromisoformat(dt_value.replace('Z', '+00:00'))
        except ValueError:
            try:
                # Try common formats
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S']:
                    try:
                        return datetime.strptime(dt_value, fmt)
                    except ValueError:
                        continue
            except Exception:
                pass
        return None
    if isinstance(dt_value, (int, float)):
        try:
            return datetime.fromtimestamp(dt_value)
        except (ValueError, OSError):
            return None
    return None
