"""
Data access for app.api.papers.crud (extracted by the arch-audit refactor).

Paper CRUD route handlers.

Covers: list papers, get single paper, upload, and delete.
"""
from app.repositories.concepts import ConceptOnlyTagService
from app.repositories.errors import DataAccessError, NotFoundError
from app.repositories.paper_queries import build_author_filter
from app.repositories.paper_queries import build_concept_filter
from app.repositories.paper_queries import build_multi_value_filter
from app.repositories.paper_queries import build_paper_type_filter
from app.repositories.paper_queries import build_search_filter
from app.repositories.paper_queries import build_special_filters
from app.repositories.paper_queries import build_year_filter
from bson import ObjectId
from pymongo import ASCENDING
from pymongo import DESCENDING
from typing import Any
from typing import Dict
import logging

concept_service = ConceptOnlyTagService()

from app.database.mongodb import get_database

db = get_database()

logger = logging.getLogger(__name__)


def _format_paper_list_item(paper: dict, concept_refs: list) -> dict:
    """Format a single paper document for the list endpoint response."""
    readability_metrics = paper.get('readability', {})

    analyses_data = []
    if paper.get('analyses'):
        if isinstance(paper['analyses'], dict):
            for analysis_type, analysis_content in paper['analyses'].items():
                if isinstance(analysis_content, dict) and analysis_content.get('success'):
                    analyses_data.append({
                        'analysis_type': analysis_type,
                        'analysis_name': analysis_type,
                        'content': analysis_content.get('content', ''),
                        'analysis_content': analysis_content.get('content', ''),
                        'model': analysis_content.get('model'),
                        'created_at': analysis_content.get('created_at'),
                    })
        elif isinstance(paper['analyses'], list):
            analyses_data = paper['analyses']

    return {
        'id': str(paper['_id']),
        'title': paper.get('title'),
        'abstract': paper.get('abstract'),
        'authors': paper.get('authors', []),
        'authors_detailed': paper.get('authors_detailed', []),
        'publication_date': paper.get('publication_date'),
        'conference': paper.get('conference'),
        'journal': paper.get('journal'),
        'arxiv_id': paper.get('arxiv_id'),
        'doi': paper.get('doi'),
        'pdf_path': paper.get('pdf_path'),
        'page_count': paper.get('page_count', 0),
        'word_count': paper.get('word_count', 0),
        'concepts': concept_refs,
        'tags': [c['display_name'] for c in concept_refs],
        'is_processed': paper.get('processed', False),
        'processed': paper.get('processed', False),
        'processor': paper.get('processor_used'),
        'processor_used': paper.get('processor_used'),
        'processed_with_mineru': paper.get('processor_used') == 'mineru_service',
        'processed_with_marker': paper.get('processor_used') == 'marker_service',
        'is_flagged': paper.get('is_flagged', False),
        'user_rating': paper.get('user_rating'),
        'created_at': paper.get('created_at').isoformat() if paper.get('created_at') else None,
        'readability': readability_metrics,
        'paper_type': paper.get('paper_type', 'research'),
        'analyses': analyses_data,
    }


def _resolve_concepts_for_papers(papers: list) -> Dict[str, list]:
    """Batch-load tag instances and concept docs for a list of papers.

    Returns a dict mapping paper-id (str) to a list of concept-ref dicts.
    """
    paper_id_strings = []
    legacy_ids = []
    for paper in papers:
        paper_id_strings.append(str(paper['_id']))
        legacy_id = paper.get('old_sqlite_id')
        if legacy_id:
            legacy_ids.append(str(legacy_id))

    tag_instances_by_paper: Dict[str, list] = {}
    concept_ids_needed: set = set()

    if paper_id_strings:
        id_query = {'content_type': 'paper', 'content_id': {'$in': paper_id_strings + legacy_ids}}
        for instance in db.tag_instances.find(id_query):
            content_id = instance.get('content_id')
            if not content_id:
                continue
            tag_instances_by_paper.setdefault(content_id, []).append(instance)
            cid = instance.get('concept_id')
            if cid:
                concept_ids_needed.add(str(cid))

    concept_map: Dict[str, dict] = {}
    if concept_ids_needed:
        object_ids = []
        string_ids = []
        for cid in concept_ids_needed:
            if len(cid) == 24:
                try:
                    object_ids.append(ObjectId(cid))
                    continue
                except Exception:
                    pass
            string_ids.append(cid)

        concepts_query: Dict[str, Any] = {'$or': []}
        if object_ids:
            concepts_query['$or'].append({'_id': {'$in': object_ids}})
        if string_ids:
            concepts_query['$or'].append({'id': {'$in': string_ids}})

        if concepts_query['$or']:
            for doc in concept_service.tag_concepts.find(concepts_query):
                concept_map[str(doc['_id'])] = doc
                if doc.get('id'):
                    concept_map[doc['id']] = doc

    # Build per-paper concept refs
    result: Dict[str, list] = {}
    for paper in papers:
        paper_id = str(paper['_id'])
        sqlite_id = str(paper.get('old_sqlite_id', '')) if paper.get('old_sqlite_id') else None

        instances = list(tag_instances_by_paper.get(paper_id, []))
        if sqlite_id:
            instances.extend(tag_instances_by_paper.get(sqlite_id, []))

        refs = []
        seen: set = set()
        for inst in instances:
            cid = inst.get('concept_id')
            key = str(cid) if cid else None
            if key and key not in seen:
                seen.add(key)
                doc = concept_map.get(key)
                if doc:
                    refs.append({
                        'concept_id': str(doc['_id']),
                        'display_name': doc.get('display_name'),
                        'slug': doc.get('slug'),
                    })
        result[paper_id] = refs

    return result


def get_papers(page, page_size, search, search_mode, concept_id, concept_ids, author, conference, conferences, journal, institution, affiliations, processor, processors, year, years, special_filter, is_flagged, no_processor, no_year, no_conference, no_affiliation, no_annotations, no_mollick_summary, min_rating, rating, unrated_only, sort_by, sort_order, paper_type):
    """Get papers with filtering and pagination from MongoDB"""

    # --- Build query using extracted helpers ---
    query: Dict[str, Any] = {}
    build_paper_type_filter(query, paper_type)

    if search:
        build_search_filter(query, search, search_mode)

    build_concept_filter(query, concept_id, concept_ids)
    build_author_filter(query, author)

    build_multi_value_filter(query, field='conference', values=conferences, single_value=conference)
    build_multi_value_filter(query, field='authors_detailed.affiliation', values=affiliations, single_value=institution)
    build_multi_value_filter(query, field='processor_used', values=processors, single_value=processor, use_regex=False)

    if journal:
        query['journal'] = {'$regex': journal, '$options': 'i'}

    build_year_filter(query, year, years)
    build_special_filters(
        query,
        special_filter=special_filter,
        is_flagged=is_flagged,
        no_processor=no_processor,
        no_year=no_year,
        no_conference=no_conference,
        no_affiliation=no_affiliation,
        no_annotations=no_annotations,
        no_mollick_summary=no_mollick_summary,
        min_rating=min_rating,
        rating=rating,
        unrated_only=unrated_only,
    )

    logger.info(f"Final query for papers: {query}")

    # --- Execute query ---
    total = db.papers.count_documents(query)
    skip = (page - 1) * page_size
    sort_direction = DESCENDING if sort_order == "desc" else ASCENDING

    if sort_by == "rating":
        sort_criteria = [
            ('user_rating', DESCENDING if sort_order == "desc" else ASCENDING),
            ('created_at', DESCENDING),
        ]
        cursor = db.papers.find(query).sort(sort_criteria).skip(skip).limit(page_size)
    elif sort_by == "title":
        cursor = db.papers.find(query).sort('title', sort_direction).skip(skip).limit(page_size)
    elif sort_by == "publication_date":
        cursor = db.papers.find(query).sort('publication_date', sort_direction).skip(skip).limit(page_size)
    else:
        cursor = db.papers.find(query).sort('created_at', sort_direction).skip(skip).limit(page_size)

    papers = list(cursor)

    # --- Resolve concepts & format ---
    concepts_by_paper = _resolve_concepts_for_papers(papers)

    result = [
        _format_paper_list_item(paper, concepts_by_paper.get(str(paper['_id']), []))
        for paper in papers
    ]

    return {
        'papers': result,
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': (total + page_size - 1) // page_size,
    }



def delete_paper(paper_id):
    """Delete a paper and all associated data"""

    try:
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except Exception:
        paper = None

    if not paper:
        raise NotFoundError("Paper not found")

    paper_id_str = str(paper['_id'])
    sqlite_id_str = str(paper.get('old_sqlite_id', ''))

    db.tag_instances.delete_many({
        'content_type': 'paper',
        '$or': [
            {'content_id': paper_id_str},
            {'content_id': sqlite_id_str}
        ]
    })

    result = db.papers.delete_one({'_id': paper['_id']})

    if result.deleted_count > 0:
        logger.info(f"Deleted paper {paper_id_str}")
        return {"success": True, "message": "Paper deleted successfully"}
    else:
        raise DataAccessError("Failed to delete paper")

