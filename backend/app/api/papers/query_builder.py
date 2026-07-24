"""
Query builder helpers for the papers list endpoint.

Extracts complex MongoDB query construction from crud.py to keep
each file under the 600 LOC limit.
"""

import re
import logging
from typing import Dict, List, Optional

from bson import ObjectId
from bson.errors import InvalidId

from .utils import db

logger = logging.getLogger("app.api.papers")


def build_paper_type_filter(query: Dict, paper_type: str) -> None:
    """Filter papers by type: 'research' (default) or 'review'."""
    query['paper_type'] = paper_type


def build_search_filter(query: Dict, search: str, search_mode: str) -> None:
    """Add text-search clauses to *query* in-place."""
    escaped = re.escape(search)
    if search_mode == "content":
        query['$or'] = [
            {'markdown_content': {'$regex': escaped, '$options': 'i'}},
            {'content': {'$regex': escaped, '$options': 'i'}}
        ]
    elif search_mode == "all":
        query['$or'] = [
            {'title': {'$regex': escaped, '$options': 'i'}},
            {'markdown_content': {'$regex': escaped, '$options': 'i'}},
            {'content': {'$regex': escaped, '$options': 'i'}}
        ]
    else:  # "title" (default)
        query['title'] = {'$regex': escaped, '$options': 'i'}


def build_concept_filter(query: Dict, concept_id: Optional[str], concept_ids: Optional[List[str]]) -> None:
    """Add concept/tag filters to *query* in-place."""
    if concept_ids and len(concept_ids) > 0:
        concept_object_ids = []
        for cid in concept_ids:
            try:
                concept_object_ids.append(ObjectId(cid))
            except (InvalidId, TypeError):
                logger.debug(f"Skipping invalid concept_id format: {cid}")
        if concept_object_ids:
            query['concept_ids'] = {'$all': concept_object_ids}
    elif concept_id:
        try:
            query['concept_ids'] = {'$all': [ObjectId(concept_id)]}
        except (InvalidId, TypeError):
            query['concept_ids'] = {'$all': [concept_id]}


def build_author_filter(query: Dict, author: Optional[str]) -> None:
    if author:
        query['authors_detailed.name'] = {'$regex': author, '$options': 'i'}


def build_multi_value_filter(
    query: Dict,
    *,
    field: str,
    values: Optional[List[str]],
    single_value: Optional[str],
    use_regex: bool = True,
) -> None:
    """Generic multi-value OR filter that adds to $and when needed."""
    effective = values if values and len(values) > 0 else ([single_value] if single_value else None)
    if not effective:
        return

    if len(effective) == 1:
        if use_regex:
            query[field] = {'$regex': effective[0], '$options': 'i'}
        else:
            query[field] = effective[0]
    else:
        if use_regex:
            conditions = [{field: {'$regex': v, '$options': 'i'}} for v in effective]
        else:
            query[field] = {'$in': effective}
            return
        query.setdefault('$and', []).append({'$or': conditions})


def build_year_filter(query: Dict, year: Optional[int], years: Optional[List[int]]) -> None:
    """Add publication-year filters using MongoDB $expr."""
    effective = years if years and len(years) > 0 else ([year] if year else None)
    if not effective:
        return

    year_cond = {
        '$cond': {
            'if': {
                '$and': [
                    {'$ne': ['$publication_date', None]},
                    {'$ne': ['$publication_date', '']},
                    {'$eq': [{'$type': '$publication_date'}, 'string']},
                    {'$gt': [{'$strLenCP': '$publication_date'}, 4]}
                ]
            },
            'then': {'$year': {'$dateFromString': {'dateString': '$publication_date', 'onError': None}}},
            'else': {'$year': '$created_at'}
        }
    }

    if len(effective) == 1:
        query['$expr'] = {'$eq': [year_cond, effective[0]]}
    else:
        query['$expr'] = {'$in': [year_cond, effective]}


def build_special_filters(
    query: Dict,
    *,
    special_filter: Optional[str],
    is_flagged: Optional[bool],
    no_processor: Optional[bool],
    no_year: Optional[bool],
    no_conference: Optional[bool],
    no_affiliation: Optional[bool],
    no_annotations: Optional[bool],
    no_mollick_summary: Optional[bool],
    min_rating: Optional[int],
    rating: Optional[int],
    unrated_only: bool,
) -> None:
    """Apply all boolean / special-case filters in-place."""
    if special_filter:
        _SPECIAL_MAP = {
            'processed': ('processed', True),
            'flagged': ('is_flagged', True),
            'arxiv': ('arxiv_id', {'$nin': [None, '']}),
            'has_doi': ('doi', {'$nin': [None, '']}),
            'has_repository': ('repository', {'$nin': [None, '']}),
        }
        if special_filter in _SPECIAL_MAP:
            key, val = _SPECIAL_MAP[special_filter]
            query[key] = val

    if is_flagged is not None:
        query['is_flagged'] = is_flagged

    if no_processor:
        query.setdefault('$and', []).append({'$or': [
            {'processor_used': None},
            {'processor_used': ''},
            {'processor_used': {'$exists': False}},
            {'processed': False},
            {'processed': {'$exists': False}}
        ]})

    _missing_field = lambda field: [
        {field: None}, {field: ''}, {field: {'$exists': False}}
    ]

    if no_year:
        query.setdefault('$and', []).append({'$or': _missing_field('publication_date')})

    if no_conference:
        query.setdefault('$and', []).append({'$or': _missing_field('conference')})

    if no_affiliation:
        query.setdefault('$and', []).append({'$or': [
            {'authors_detailed': {'$in': [None, []]}},
            {'authors_detailed': {'$exists': False}},
            {
                'authors_detailed': {
                    '$elemMatch': {
                        '$or': [
                            {'affiliation': None},
                            {'affiliation': ''},
                            {'affiliation': {'$exists': False}}
                        ]
                    }
                }
            }
        ]})

    if no_annotations:
        papers_with_tags = db.tag_instances.distinct('content_id', {'content_type': 'paper'})
        objectid_list = []
        int_list = []
        for pid in papers_with_tags:
            pid_str = str(pid)
            try:
                if len(pid_str) == 24:
                    objectid_list.append(ObjectId(pid_str))
            except (InvalidId, TypeError):
                pass
            try:
                int_list.append(int(pid_str))
            except (ValueError, TypeError):
                pass

        if objectid_list or int_list:
            conditions = []
            if objectid_list:
                conditions.append({'_id': {'$nin': objectid_list}})
            if int_list:
                conditions.append({'old_sqlite_id': {'$nin': int_list}})
            if len(conditions) == 1:
                for key, value in conditions[0].items():
                    query[key] = value
            else:
                query.setdefault('$and', []).extend(conditions)

    # Rating filters
    if min_rating:
        query['user_rating'] = {'$gte': min_rating}
    elif rating:
        query['user_rating'] = rating
    elif unrated_only:
        query.setdefault('$and', []).append(
            {'$or': [{'user_rating': {'$exists': False}}, {'user_rating': None}]}
        )

    if no_mollick_summary:
        query.setdefault('$and', []).append(
            {'analyses': {'$not': {'$elemMatch': {'analysis_type': 'mollick_summary'}}}}
        )
