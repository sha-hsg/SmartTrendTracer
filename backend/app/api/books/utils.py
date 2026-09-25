"""
Shared imports, global state, and utility functions for the books API sub-modules.

All books sub-modules should import from here rather than duplicating setup code.
"""

# --- Standard library ---
from app.paths import BOOK_REPOSITORY_REL
import hashlib
import json
import logging
import os
import re
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# --- Third-party ---
from bson import ObjectId
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
from pymongo import ASCENDING, DESCENDING

# --- Application services ---
from app.database.mongodb import get_database
from app.services.concept_only_tag_service import ConceptOnlyTagService
from app.repositories.books import get_book_by_id  # noqa: F401 (moved to data layer)

# ---------------------------------------------------------------------------
# Shared global state
# ---------------------------------------------------------------------------

logger = logging.getLogger("app.api.books")

# MongoDB connection
db = get_database()

# Initialize services
concept_service = ConceptOnlyTagService()

# Book storage directory
BOOKS_REPOSITORY = BOOK_REPOSITORY_REL
BOOKS_REPOSITORY.parent.mkdir(parents=True, exist_ok=True)
BOOKS_REPOSITORY.mkdir(exist_ok=True)

# Queue collection for background processing
BOOK_PROCESSING_QUEUE = db.book_processing_jobs


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

