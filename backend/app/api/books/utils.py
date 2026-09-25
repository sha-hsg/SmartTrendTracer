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

def get_book_by_id(book_id: str):
    """Get book by MongoDB ObjectId - returns ObjectId converted to string"""
    try:
        if len(book_id) == 24:
            # Try as MongoDB ObjectId
            book = db.books.find_one({'_id': ObjectId(book_id)})
            if book:
                # Convert ObjectId to string to prevent serialization errors
                book['_id'] = str(book['_id'])
                if book.get('processing_job_id'):
                    try:
                        book['processing_job_id'] = str(book['processing_job_id'])
                    except Exception:
                        pass
                file_path_value = book.get('file_path')
                file_name_value = book.get('file_name') or (Path(file_path_value).name if file_path_value else None)
                if file_name_value:
                    book['file_name'] = file_name_value
                    book['file_url'] = f"/books/{book['_id']}/{file_name_value}"
                else:
                    book['file_url'] = None
                return book
            return None
        else:
            # Invalid ID format
            return None
    except Exception:
        return None
