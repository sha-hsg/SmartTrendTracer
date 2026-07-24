"""
Helper functions for building MongoDB aggregation pipelines used by the
paper facets endpoint.

Extracted from facets.py to keep individual modules under 600 LOC.
"""

from typing import Any, Dict, List, Optional

from bson import ObjectId
from bson.errors import InvalidId


# ---------------------------------------------------------------------------
# Aggregation pipeline builders
# ---------------------------------------------------------------------------

def build_author_pipeline(base_match: Optional[dict]) -> list:
    """Build aggregation pipeline for author facets from authors_detailed."""
    pipeline: list = []
    if base_match:
        pipeline.append(base_match)
    pipeline.extend([
        {'$unwind': '$authors_detailed'},
        {'$group': {
            '_id': '$authors_detailed.name',
            'count': {'$sum': 1}
        }},
        {'$sort': {'count': -1}},
        {'$limit': 50}
    ])
    return pipeline


def build_author_fallback_pipeline(base_match: Optional[dict]) -> list:
    """Fallback author pipeline using the plain authors field."""
    pipeline: list = []
    if base_match:
        pipeline.append(base_match)
    pipeline.extend([
        {'$match': {'authors': {'$nin': [None, '']}}},
        {'$project': {
            'authors_list': {
                '$cond': {
                    'if': {'$eq': [{'$type': '$authors'}, 'array']},
                    'then': '$authors',
                    'else': {'$split': ['$authors', ', ']}
                }
            }
        }},
        {'$unwind': '$authors_list'},
        {'$group': {'_id': '$authors_list', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}},
        {'$limit': 50}
    ])
    return pipeline


def build_year_pipeline(base_match: Optional[dict]) -> list:
    """Build aggregation pipeline for year facets."""
    pipeline: list = []
    if base_match:
        pipeline.append(base_match)
    pipeline.extend([
        {
            '$addFields': {
                'year': {
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
            }
        },
        {'$match': {'year': {'$ne': None}}},
        {'$group': {
            '_id': '$year',
            'count': {'$sum': 1}
        }},
        {'$sort': {'_id': -1}},
        {'$limit': 20}
    ])
    return pipeline


def build_simple_field_pipeline(
    base_match: Optional[dict],
    field: str,
    limit: int = 30,
) -> list:
    """Build a generic group-by-field pipeline (conferences, journals, processors)."""
    pipeline: list = []
    if base_match:
        pipeline.append(base_match)
    pipeline.extend([
        {'$match': {field: {'$nin': [None, '']}}},
        {'$group': {
            '_id': f'${field}',
            'count': {'$sum': 1}
        }},
        {'$sort': {'count': -1}},
        {'$limit': limit}
    ])
    return pipeline


def build_institution_pipeline(base_match: Optional[dict]) -> list:
    """Build aggregation pipeline for institution facets (unique papers per institution)."""
    pipeline: list = []
    if base_match:
        pipeline.append(base_match)
    pipeline.extend([
        {'$unwind': '$authors_detailed'},
        {'$match': {'authors_detailed.affiliation': {'$nin': [None, '']}}},
        {'$group': {
            '_id': {
                'paper_id': '$_id',
                'affiliation': '$authors_detailed.affiliation'
            }
        }},
        {'$group': {
            '_id': '$_id.affiliation',
            'count': {'$sum': 1}
        }},
        {'$sort': {'count': -1}},
        {'$limit': 30}
    ])
    return pipeline


def build_processor_pipeline(base_match: Optional[dict]) -> list:
    """Build aggregation pipeline for processor facets (no limit)."""
    pipeline: list = []
    if base_match:
        pipeline.append(base_match)
    pipeline.extend([
        {'$match': {'processor_used': {'$ne': None}}},
        {'$group': {
            '_id': '$processor_used',
            'count': {'$sum': 1}
        }},
        {'$sort': {'count': -1}}
    ])
    return pipeline


def build_rating_pipeline(base_match: Optional[dict]) -> list:
    """Build aggregation pipeline for rating facets."""
    pipeline: list = []
    if base_match:
        pipeline.append(base_match)
    pipeline.extend([
        {'$group': {
            '_id': '$user_rating',
            'count': {'$sum': 1}
        }},
        {'$sort': {'_id': -1}}
    ])
    return pipeline


def build_combined_counts_pipeline(base_match: Optional[dict]) -> list:
    """Build a single $facet pipeline that computes all special-filter counts
    in one database round-trip (DB-007/PERF-004 optimisation)."""
    pipeline: list = []
    if base_match:
        pipeline.append(base_match)

    pipeline.append({
        '$facet': {
            'processed': [{'$match': {'processed': True}}, {'$count': 'n'}],
            'flagged': [{'$match': {'is_flagged': True}}, {'$count': 'n'}],
            'unflagged': [{'$match': {'$or': [{'is_flagged': False}, {'is_flagged': {'$exists': False}}]}}, {'$count': 'n'}],
            'arxiv': [{'$match': {'arxiv_id': {'$exists': True, '$nin': [None, '']}}}, {'$count': 'n'}],
            'has_doi': [{'$match': {'doi': {'$exists': True, '$nin': [None, '']}}}, {'$count': 'n'}],
            'has_repository': [{'$match': {'repository': {'$exists': True, '$nin': [None, '']}}}, {'$count': 'n'}],
            'no_processor': [{'$match': {'$or': [{'processor_used': None}, {'processor_used': ''}, {'processor_used': {'$exists': False}}]}}, {'$count': 'n'}],
            'no_year': [{'$match': {'$and': [
                {'$or': [{'publication_date': None}, {'publication_date': ''}, {'publication_date': {'$exists': False}}]},
                {'$or': [{'year': None}, {'year': ''}, {'year': {'$exists': False}}]}
            ]}}, {'$count': 'n'}],
            'no_conference': [{'$match': {'$and': [
                {'$or': [{'conference': None}, {'conference': ''}, {'conference': {'$exists': False}}]},
                {'$or': [{'venue': None}, {'venue': ''}, {'venue': {'$exists': False}}]}
            ]}}, {'$count': 'n'}]
        }
    })
    return pipeline


def build_no_affiliation_pipeline(base_match: Optional[dict]) -> list:
    """Build pipeline to count papers with no author affiliations."""
    pipeline: list = []
    if base_match:
        pipeline.append(base_match)
    pipeline.extend([
        {'$match': {
            '$or': [
                {'authors_detailed': {'$exists': False}},
                {'authors_detailed': {'$size': 0}},
                {'$expr': {
                    '$eq': [
                        {'$size': {
                            '$filter': {
                                'input': {'$ifNull': ['$authors_detailed', []]},
                                'cond': {
                                    '$and': [
                                        {'$ne': ['$$this.affiliation', None]},
                                        {'$ne': ['$$this.affiliation', '']}
                                    ]
                                }
                            }
                        }},
                        0
                    ]
                }}
            ]
        }},
        {'$count': 'total'}
    ])
    return pipeline


# ---------------------------------------------------------------------------
# Result-extraction helpers
# ---------------------------------------------------------------------------

def extract_count(counts: dict, key: str) -> int:
    """Extract a count value from a $facet result dict."""
    return counts.get(key, [{}])[0].get('n', 0) if counts.get(key) else 0


def build_special_filters(counts: dict) -> List[Dict[str, Any]]:
    """Derive the special_filters list from combined-counts facet results."""
    filters: List[Dict[str, Any]] = []
    mapping = [
        ('processed', 'Processed Papers'),
        ('flagged', 'Flagged Papers'),
        ('arxiv', 'ArXiv Papers'),
        ('has_doi', 'Has DOI'),
        ('has_repository', 'Has Repository'),
    ]
    for key, label in mapping:
        count = extract_count(counts, key)
        if count > 0:
            filters.append({'name': key, 'label': label, 'count': count})
    return filters


def build_paper_status(counts: dict) -> Dict[str, int]:
    """Derive paper_status dict from combined-counts facet results."""
    return {
        'flagged': extract_count(counts, 'flagged'),
        'unflagged': extract_count(counts, 'unflagged'),
    }


def build_missing_data_counts(counts: dict) -> Dict[str, int]:
    """Derive basic missing_data counts from combined-counts facet results."""
    return {
        'no_processor': extract_count(counts, 'no_processor'),
        'no_year': extract_count(counts, 'no_year'),
        'no_conference': extract_count(counts, 'no_conference'),
    }


def safe_object_ids_from_strings(ids: list) -> list:
    """Convert a list of mixed-type IDs to ObjectIds where possible."""
    result = []
    for pid in ids:
        pid_str = str(pid)
        if len(pid_str) == 24:
            try:
                result.append(ObjectId(pid_str))
            except Exception:
                result.append(pid)
        else:
            result.append(pid)
    return result


def build_rating_facet(rating_results: list) -> Dict[str, int]:
    """Build the rating facet dict from rating aggregation results."""
    return {
        '5_stars': next((r['count'] for r in rating_results if r['_id'] == 5), 0),
        '4_stars': next((r['count'] for r in rating_results if r['_id'] == 4), 0),
        '3_stars': next((r['count'] for r in rating_results if r['_id'] == 3), 0),
        '2_stars': next((r['count'] for r in rating_results if r['_id'] == 2), 0),
        '1_star': next((r['count'] for r in rating_results if r['_id'] == 1), 0),
    }
