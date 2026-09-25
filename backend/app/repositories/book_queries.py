"""
Query builder helpers for the books list endpoint.

Extracts complex MongoDB query construction from crud.py to keep
each file under the 600 LOC limit.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from bson import ObjectId

logger = logging.getLogger("app.api.books")


def build_search_filter(query: Dict, search: Optional[str]) -> None:
    """Add full-text search to *query* in-place."""
    if search:
        query['$text'] = {'$search': search}


def build_concept_filter(
    query: Dict,
    concept_id: Optional[str],
    concept_ids: Optional[List[str]],
) -> None:
    """Add concept/tag filters to *query* in-place."""
    ids_to_use = concept_ids if concept_ids else ([concept_id] if concept_id else None)
    if not ids_to_use:
        return

    for cid in ids_to_use:
        if not cid:
            continue
        normalized_cid = str(cid)
        concept_options = [{'concept_ids': normalized_cid}]
        if len(normalized_cid) == 24:
            try:
                concept_options.append({'concept_ids': ObjectId(normalized_cid)})
            except Exception:
                pass
        if concept_options:
            query.setdefault('$and', [])
            query['$and'].append({'$or': concept_options})


def build_multi_value_filter(
    query: Dict,
    *,
    field: str,
    values: Optional[List],
    single_value: Optional[str],
    use_regex: bool = False,
) -> None:
    """Generic multi-value filter. Adds $in or regex as needed."""
    effective = values if values and len(values) > 0 else ([single_value] if single_value else None)
    if not effective:
        return

    if len(effective) == 1 and use_regex:
        query[field] = {'$regex': effective[0], '$options': 'i'}
    elif len(effective) == 1:
        query[field] = effective[0]
    else:
        query[field] = {'$in': effective}


def build_year_filter(query: Dict, year: Optional[int], years: Optional[List[int]]) -> None:
    """Add publication year filter."""
    effective = years if years and len(years) > 0 else ([year] if year else None)
    if not effective:
        return
    if len(effective) == 1:
        query['publication_year'] = effective[0]
    else:
        query['publication_year'] = {'$in': effective}


def build_special_filters(
    query: Dict,
    *,
    special_filter: Optional[str],
    is_processed: Optional[bool],
    no_processor: Optional[bool],
    no_year: Optional[bool],
    no_publisher: Optional[bool],
    no_isbn: Optional[bool],
    no_annotations: Optional[bool],
) -> None:
    """Apply all boolean / special-case filters in-place."""
    if is_processed is not None:
        if is_processed:
            query['processing_status'] = 'completed'
        else:
            query['processing_status'] = {'$ne': 'completed'}

    if no_processor:
        query['processor'] = {'$exists': False}
    if no_year:
        query['publication_year'] = {'$exists': False}
    if no_publisher:
        query['publisher'] = {'$exists': False}
    if no_isbn:
        query['isbn'] = {'$exists': False}
    if no_annotations:
        query['$or'] = [
            {'concept_ids': {'$exists': False}},
            {'concept_ids': {'$size': 0}}
        ]

    if special_filter == 'recently_uploaded':
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        query['uploaded_at'] = {'$gte': cutoff}
    elif special_filter == 'processing_failed':
        query['processing_status'] = 'failed'
    elif special_filter == 'large_books':
        query['page_count'] = {'$gte': 500}
    elif special_filter == 'epub_only':
        query['file_type'] = 'epub'
    elif special_filter == 'pdf_only':
        query['file_type'] = 'pdf'
