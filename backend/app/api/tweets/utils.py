"""
Shared imports, database connection, logger, and helper functions for the tweets API package.
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pymongo import ASCENDING, DESCENDING
from app.database.mongodb import get_database
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel
import logging
import uuid
import json
from bson import ObjectId
from bson.errors import InvalidId

from app.services.concept_only_tag_service import ConceptOnlyTagService
from app.services.llm_manager import get_llm_manager

logger = logging.getLogger(__name__)

# MongoDB connection
db = get_database()

# Initialize services
concept_service = ConceptOnlyTagService()
llm_manager = get_llm_manager()

# In-memory batch annotation task tracking
batch_annotation_tasks: Dict[str, Dict] = {}

# Cache for profile images to avoid repeated DB lookups (OBS-006: with TTL)
_profile_image_cache: Dict[str, tuple[Optional[str], float]] = {}  # {username: (url, timestamp)}
_PROFILE_IMAGE_CACHE_TTL = 3600  # 1 hour TTL

def get_profile_images_for_usernames(usernames: List[str]) -> Dict[str, Optional[str]]:
    """
    Batch lookup profile images from twitter_accounts collection.
    Returns a dict mapping username -> profile_image_url (or None if not found).
    Uses caching with 1 hour TTL to avoid repeated lookups.
    """
    import time
    current_time = time.time()
    result = {}
    usernames_to_lookup = []

    # Check cache first (with TTL validation)
    for username in usernames:
        if username in _profile_image_cache:
            cached_url, cached_time = _profile_image_cache[username]
            if current_time - cached_time < _PROFILE_IMAGE_CACHE_TTL:
                result[username] = cached_url
            else:
                # Cache expired
                del _profile_image_cache[username]
                usernames_to_lookup.append(username)
        else:
            usernames_to_lookup.append(username)

    # Lookup remaining usernames from DB
    if usernames_to_lookup:
        accounts = list(db.twitter_accounts.find(
            {'username': {'$in': usernames_to_lookup}},
            {'username': 1, 'profile_image_url': 1}
        ))

        for account in accounts:
            username = account.get('username')
            profile_url = account.get('profile_image_url')
            result[username] = profile_url
            _profile_image_cache[username] = (profile_url, current_time)

        # Cache None for usernames not found
        for username in usernames_to_lookup:
            if username not in result:
                result[username] = None
                _profile_image_cache[username] = (None, current_time)

    return result


class BatchAnnotateRequest(BaseModel):
    """Request model for batch annotation"""
    tweet_ids: List[str]
    model: Optional[str] = None  # User-selected model (uses default if None)
