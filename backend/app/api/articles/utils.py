"""Shared state for articles API package."""

from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import FileResponse
from app.database.mongodb import get_database
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import re
from bson import ObjectId
import json
from pathlib import Path

from app.services.concept_only_tag_service import ConceptOnlyTagService
from app.services.author_service import AuthorService

logger = logging.getLogger(__name__)

# MongoDB connection
db = get_database()

# Initialize services
concept_service = ConceptOnlyTagService()
author_service = AuthorService(db)
