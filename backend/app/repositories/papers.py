"""Paper lookups shared by the papers API package."""
from app.database.mongodb import safe_object_id
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


def find_paper_by_id(paper_id: str) -> Optional[Dict[str, Any]]:
    """Find a paper by ObjectId or legacy SQLite ID.

    This helper consolidates the common pattern of:
    1. Try to find by ObjectId (if 24 chars)
    2. Fall back to old_sqlite_id (if numeric)

    Returns None if paper not found or ID is invalid.
    """
    if not paper_id:
        return None

    # Try ObjectId first if it looks like one
    oid = safe_object_id(paper_id)
    if oid:
        paper = db.papers.find_one({'_id': oid})
        if paper:
            return paper

    # Fall back to old SQLite ID
    try:
        sqlite_id = int(paper_id)
        return db.papers.find_one({'old_sqlite_id': sqlite_id})
    except (ValueError, TypeError):
        pass

    return None


def paper_filter(paper_id: str) -> Dict[str, Any]:
    """Build the MongoDB filter for a paper id (ObjectId or legacy string)."""
    return {'_id': ObjectId(paper_id) if len(paper_id) == 24 else paper_id}


def save_arxiv_import(result: Dict[str, Any]) -> str:
    """Persist an ArxivImportService.import_paper() result as a paper.

    Shared by POST /api/arxiv/import and POST /api/references/{id}/import so
    both write the same document. Returns the paper id; an existing paper
    with the same arxiv_id is reused instead of duplicated.
    """
    from datetime import datetime, timezone
    existing = db.papers.find_one({'arxiv_id': result['arxiv_id']})
    if existing:
        return str(existing['_id'])
    paper_data = {
        'title': result['metadata']['title'],
        'authors': ', '.join(result['metadata']['authors']),
        'authors_detailed': [{'name': author, 'affiliation': '', 'email': ''} for author in result['metadata']['authors']],
        'abstract': result['metadata']['abstract'],
        'arxiv_id': result['arxiv_id'],
        'pdf_url': result['metadata']['pdf_url'],
        'publication_date': result['metadata'].get('published'),
        'categories': result['metadata'].get('categories', []),
        'content': '',  # Will be filled after processing
        'pdf_path': result['pdf_path'],  # PDF is immediately available
        'processed': False,  # Not processed yet
        'processor_used': None,
        'created_at': datetime.now(timezone.utc),
        'source': 'arxiv',
        'url': f"https://arxiv.org/abs/{result['arxiv_id']}",
        'import_source': 'arxiv',  # Track import source type
        'import_url': f"https://arxiv.org/abs/{result['arxiv_id']}",  # Store original import URL
        'paper_type': 'research',
    }
    return str(db.papers.insert_one(paper_data).inserted_id)
