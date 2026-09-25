"""Paper lookups shared by the papers API package."""
import logging
from typing import Any, Dict, Optional

from bson import ObjectId
from bson.errors import InvalidId

from app.database.mongodb import get_database

logger = logging.getLogger(__name__)
db = get_database()


def get_paper_by_id(paper_id: str) -> Optional[Dict[str, Any]]:
    """Get paper by MongoDB ObjectId only - pure MongoDB standard.

    Returns the paper document with ``_id`` converted to a string so that
    it can be safely serialised to JSON.
    """
    try:
        if len(paper_id) == 24:
            # Try as MongoDB ObjectId
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
            if paper:
                # Convert ObjectId to string to prevent serialization errors
                paper['_id'] = str(paper['_id'])
                return paper
            return None
        else:
            # Invalid ID format
            return None
    except (InvalidId, TypeError, ValueError) as e:
        logger.debug(f"Failed to get paper by ID '{paper_id}': {e}")
        return None


def find_paper_by_any_id(paper_id: str) -> Optional[Dict[str, Any]]:
    """Paper by 24-hex ObjectId, or by legacy integer old_sqlite_id.

    Returns the raw document (ObjectId _id) or None; never raises.
    """
    try:
        if len(paper_id) == 24:
            return db.papers.find_one({'_id': ObjectId(paper_id)})
        return db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except Exception:
        return None


def save_extracted_sections(paper_id: str, sections, abstract: str):
    """Persist LLM-extracted sections; returns the UpdateResult."""
    from datetime import datetime, timezone
    return db.papers.update_one(
        {'_id': ObjectId(paper_id)},
        {
            '$set': {
                'sections': sections,
                'sections_extracted': True,
                'sections_extracted_at': datetime.now(timezone.utc),
                'abstract': abstract,
            }
        }
    )
