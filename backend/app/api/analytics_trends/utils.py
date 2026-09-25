"""
Shared utilities, imports, and state for the analytics_trends package.
Split from analytics_trends_mongodb.py.
"""

from fastapi import APIRouter, Query, HTTPException
from app.database.mongodb import get_database
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from bson import ObjectId
import logging



# Import helper functions
from app.services.analytics import (
    parse_period_to_days,
    get_date_range,
    get_previous_period_range,
    get_concept_ids_from_tags,
    get_tagged_content_ids,
    get_concept_by_id,
    get_concepts_by_ids,
    count_tags_for_content,
    calculate_tag_velocity,
    determine_trend,
    fetch_tweets_in_range,
    fetch_articles_in_range,
    fetch_papers_in_range,
    fetch_all_content_in_range,
    initialize_timeline_dict,
    initialize_hourly_dict,
    populate_timeline_from_content,
    calculate_content_statistics,
    find_peak_and_lowest,
    aggregate_concept_usage,
    collect_key_topics,
    prepare_content_sample,
    build_summarization_prompt,
    build_fallback_summary,
)
from app.utils.datetime_utils import normalize_datetime  # noqa: F401 (moved to data layer)

logger = logging.getLogger(__name__)

# MongoDB connection
db = get_database()
