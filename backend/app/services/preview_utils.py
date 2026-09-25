"""Backwards-compatibility shim — preview generation is a pure text utility
and lives in app.utils.preview_utils."""
from app.utils.preview_utils import generate_preview  # noqa: F401
