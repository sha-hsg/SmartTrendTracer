"""Backwards-compatibility shim — the analytics query helpers are data access
and live in app.repositories.analytics."""
from app.repositories.analytics import *  # noqa: F401,F403
from app.repositories.analytics import __all__  # noqa: F401
