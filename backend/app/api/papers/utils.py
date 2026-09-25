"""
Shared imports, global state, and utility functions for the papers API sub-modules.

All papers sub-modules should import from here rather than duplicating setup code.
"""

# --- Standard library ---
import asyncio
import hashlib
import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# --- Third-party ---
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    File,
    HTTPException,
    Query,
    Request,
    UploadFile,
)
from fastapi.responses import FileResponse, Response

# --- Application services ---
from app.database.mongodb import get_database
from app.services.concept_only_tag_service import ConceptOnlyTagService
from app.services.readability_service import ReadabilityService

# ---------------------------------------------------------------------------
# Shared global state
# ---------------------------------------------------------------------------

logger = logging.getLogger("app.api.papers")

# MongoDB connection
db = get_database()

# Initialize concept service
concept_service = ConceptOnlyTagService()

# Marker processing semaphore (limit to 1 concurrent Marker process)
marker_semaphore = asyncio.Semaphore(1)

# Initialize readability service
readability_service = ReadabilityService()


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def safe_object_id(value: Any) -> Optional[ObjectId]:
    """Safely convert a value to ObjectId, returning None if invalid.

    Handles various input formats:
    - None -> None
    - Already an ObjectId -> returns as-is
    - 24-character hex string -> converts to ObjectId
    - Any other value -> None
    """
    if value is None:
        return None
    if isinstance(value, ObjectId):
        return value
    try:
        str_val = str(value)
        if len(str_val) == 24:
            return ObjectId(str_val)
    except (InvalidId, TypeError, ValueError):
        pass
    return None




# Moved to the data-access layer; re-exported for the papers package
from app.repositories.papers import get_paper_by_id  # noqa: E402,F401
from app.repositories.papers import find_paper_by_id  # noqa: F401 (moved to data layer)


def parse_marker_error(error_text: str) -> str:
    """Parse Marker service error and return a user-friendly message."""
    try:
        # Try to parse as JSON
        error_data = json.loads(error_text)
        if isinstance(error_data, dict):
            # Extract the main error message
            error_msg = error_data.get('error', '')

            # Check for common error patterns in cli_logs
            cli_logs = error_data.get('cli_logs', '')

            # Surya/PyTorch memory error
            if 'AcceleratorError' in cli_logs or 'out of bounds' in cli_logs:
                return "PDF processing failed: Document too large or complex for available memory. Try using MinerU instead."

            # CUDA/MPS memory error
            if 'OutOfMemoryError' in cli_logs or 'out of memory' in cli_logs.lower():
                return "PDF processing failed: Out of memory. Try using MinerU instead or process on a machine with more RAM."

            # Invalid PDF
            if 'Invalid PDF' in cli_logs or 'PDFSyntaxError' in cli_logs:
                return "PDF processing failed: Invalid or corrupted PDF file."

            # Password protected
            if 'password' in cli_logs.lower() and 'protect' in cli_logs.lower():
                return "PDF processing failed: PDF is password protected."

            # Generic marker_single failed
            if 'marker_single failed' in error_msg:
                return "PDF processing failed: Marker could not extract content. Try using MinerU instead."

            # Return cleaned error message
            if error_msg:
                return f"PDF processing failed: {error_msg}"
    except (json.JSONDecodeError, TypeError):
        pass

    # Check for common patterns in raw text
    if 'AcceleratorError' in error_text or 'out of bounds' in error_text:
        return "PDF processing failed: Document too large or complex for available memory. Try using MinerU instead."

    if 'timeout' in error_text.lower():
        return "PDF processing failed: Processing timed out. The document may be too large."

    if 'connection' in error_text.lower() and ('refused' in error_text.lower() or 'error' in error_text.lower()):
        return "PDF processing failed: Could not connect to Marker service. Please ensure the service is running."

    # Truncate very long error messages
    if len(error_text) > 200:
        return f"PDF processing failed: {error_text[:150]}..."

    return f"PDF processing failed: {error_text}"
