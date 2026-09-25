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
from app.repositories.tweets import get_profile_images_for_usernames, _profile_image_cache, _PROFILE_IMAGE_CACHE_TTL  # noqa: F401 (moved to data layer)

logger = logging.getLogger(__name__)

# MongoDB connection
db = get_database()

# Initialize services
concept_service = ConceptOnlyTagService()
llm_manager = get_llm_manager()

# In-memory batch annotation task tracking
batch_annotation_tasks: Dict[str, Dict] = {}

# Cache for profile images to avoid repeated DB lookups (OBS-006: with TTL)



class BatchAnnotateRequest(BaseModel):
    """Request model for batch annotation"""
    tweet_ids: List[str]
    model: Optional[str] = None  # User-selected model (uses default if None)
