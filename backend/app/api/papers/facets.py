"""
Paper facets, statistics, and DBLP search route handlers.

Covers: get_facets (filter facets for papers dashboard), get_statistics
(paper collection overview), and search_dblp (DBLP bibliography search).
"""

from .utils import (
    # Standard library re-exports used by the handlers
    re,
    # typing
    Any,
    Dict,
    List,
    Optional,
    # Third-party
    ObjectId,
    InvalidId,
    APIRouter,
    HTTPException,
    Query,
    ASCENDING,
    DESCENDING,
    # Shared application state
    db,
    concept_service,
    logger,
)

from .facet_helpers import (
    build_author_pipeline,
    build_author_fallback_pipeline,
    build_year_pipeline,
    build_simple_field_pipeline,
    build_institution_pipeline,
    build_processor_pipeline,
    build_rating_pipeline,
    build_combined_counts_pipeline,
    build_no_affiliation_pipeline,
    extract_count,
    build_special_filters,
    build_paper_status,
    build_missing_data_counts,
    safe_object_ids_from_strings,
    build_rating_facet,
)

router = APIRouter()


@router.get("/facets")
def get_facets(
    search: Optional[str] = None,
    concept_ids: Optional[List[str]] = Query(None),
    author: Optional[str] = None,
    conference: Optional[str] = None,
    conferences: Optional[List[str]] = Query(None),
    year: Optional[int] = None,
    years: Optional[List[int]] = Query(None),
    affiliation: Optional[str] = None,
    affiliations: Optional[List[str]] = Query(None),
    processor: Optional[str] = None,
    processors: Optional[List[str]] = Query(None),
    search_mode: Optional[str] = Query("title", regex="^(title|content|all)$"),
    paper_type: str = Query("research", description="Paper type: research or review"),
) -> Dict[str, Any]:
    """Get facets for filtering papers - facets update based on current filters"""

    logger.debug("Starting facets generation with filters")

    # Build base query for filtering (same as in get_papers)
    base_query = {}
    base_query['paper_type'] = paper_type

    if search:
        escaped = re.escape(search)
        if search_mode == "content":
            base_query['$or'] = [
                {'markdown_content': {'$regex': escaped, '$options': 'i'}},
                {'content': {'$regex': escaped, '$options': 'i'}}
            ]
        elif search_mode == "all":
            base_query['$or'] = [
                {'title': {'$regex': escaped, '$options': 'i'}},
                {'markdown_content': {'$regex': escaped, '$options': 'i'}},
                {'content': {'$regex': escaped, '$options': 'i'}}
            ]
        else:  # "title" (default)
            base_query['title'] = {'$regex': escaped, '$options': 'i'}

    # Handle multiple concept IDs for filtering
    if concept_ids and len(concept_ids) > 0:
        concept_object_ids = []
        for cid in concept_ids:
            try:
                concept_object_ids.append(ObjectId(cid))
            except (InvalidId, TypeError):
                pass
        if concept_object_ids:
            base_query['concept_ids'] = {'$all': concept_object_ids}

    if author:
        base_query['authors_detailed.name'] = {'$regex': author, '$options': 'i'}

    # Handle conferences (plural has priority over singular)
    if conferences and len(conferences) > 0:
        if len(conferences) == 1:
            base_query['conference'] = {'$regex': conferences[0], '$options': 'i'}
        else:
            conference_conditions = [{'conference': {'$regex': conf, '$options': 'i'}} for conf in conferences]
            if '$and' not in base_query:
                base_query['$and'] = []
            base_query['$and'].append({'$or': conference_conditions})
    elif conference:
        base_query['conference'] = {'$regex': conference, '$options': 'i'}

    # Handle years (plural has priority over singular)
    year_list = years if years and len(years) > 0 else ([year] if year else None)
    if year_list:
        year_expr = {
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
        if len(year_list) == 1:
            base_query['$expr'] = {'$eq': [year_expr, year_list[0]]}
        else:
            base_query['$expr'] = {'$in': [year_expr, year_list]}

    # Handle affiliations (plural has priority over singular)
    if affiliations and len(affiliations) > 0:
        if len(affiliations) == 1:
            base_query['authors_detailed.affiliation'] = {'$regex': affiliations[0], '$options': 'i'}
        else:
            affiliation_conditions = [{'authors_detailed.affiliation': {'$regex': aff, '$options': 'i'}} for aff in affiliations]
            if '$and' not in base_query:
                base_query['$and'] = []
            base_query['$and'].append({'$or': affiliation_conditions})
    elif affiliation:
        base_query['authors_detailed.affiliation'] = {'$regex': affiliation, '$options': 'i'}

    # Handle processors (plural has priority over singular)
    if processors and len(processors) > 0:
        if len(processors) == 1:
            base_query['processor_used'] = processors[0]
        else:
            base_query['processor_used'] = {'$in': processors}
    elif processor:
        base_query['processor_used'] = processor

    # Create base match stage for pipelines
    base_match = {'$match': base_query} if base_query else None

    # --- Run aggregation pipelines (delegated to facet_helpers) ---

    # Author facets
    author_facets = list(db.papers.aggregate(build_author_pipeline(base_match)))
    logger.debug(f"Found {len(author_facets)} author facets")
    if author_facets:
        logger.debug(f"First author facet: {author_facets[0]}")
    else:
        logger.debug("Trying fallback to regular authors field")
        author_facets = list(db.papers.aggregate(build_author_fallback_pipeline(base_match)))
        logger.debug(f"Fallback found {len(author_facets)} author facets")

    # Year facets
    year_facets = list(db.papers.aggregate(build_year_pipeline(base_match)))
    logger.debug(f"Found {len(year_facets)} year facets")

    # Conference facets
    conference_facets = list(db.papers.aggregate(build_simple_field_pipeline(base_match, 'conference')))

    # Journal facets
    journal_facets = list(db.papers.aggregate(build_simple_field_pipeline(base_match, 'journal')))

    # Institution facets
    institution_facets = list(db.papers.aggregate(build_institution_pipeline(base_match)))

    # Processor facets
    processor_facets = list(db.papers.aggregate(build_processor_pipeline(base_match)))

    # Rating facets
    rating_results = list(db.papers.aggregate(build_rating_pipeline(base_match)))

    # Count unrated papers
    unrated_query = {**base_query, '$or': [
        {'user_rating': {'$exists': False}},
        {'user_rating': None}
    ]} if base_query else {'$or': [
        {'user_rating': {'$exists': False}},
        {'user_rating': None}
    ]}
    unrated_count = db.papers.count_documents(unrated_query)

    rating_facet = build_rating_facet(rating_results)
    rating_facet['unrated'] = unrated_count
    logger.debug(f"Rating facet: {rating_facet}")

    # --- Combined counts (single $facet aggregation) ---
    facet_result = list(db.papers.aggregate(build_combined_counts_pipeline(base_match)))
    counts = facet_result[0] if facet_result else {}

    special_filters = build_special_filters(counts)
    paper_status = build_paper_status(counts)
    missing_data_counts = build_missing_data_counts(counts)

    # No-affiliation count (complex pipeline)
    no_affiliation_result = list(db.papers.aggregate(build_no_affiliation_pipeline(base_match)))
    missing_data_counts['no_affiliation'] = no_affiliation_result[0]['total'] if no_affiliation_result else 0

    # No-annotations count
    papers_with_tags = db.tag_instances.distinct('content_id', {'content_type': 'paper'})
    papers_with_tags_oids = safe_object_ids_from_strings(papers_with_tags)
    no_annotations_query = {**base_query, '_id': {'$nin': papers_with_tags_oids}} if base_query else {'_id': {'$nin': papers_with_tags_oids}}
    missing_data_counts['no_annotations'] = db.papers.count_documents(no_annotations_query)

    # No-mollick_summary count
    no_mollick_condition = {
        'analyses': {'$not': {'$elemMatch': {'analysis_type': 'mollick_summary'}}}
    }
    if base_query:
        no_mollick_query = {'$and': [base_query, no_mollick_condition]}
    else:
        no_mollick_query = no_mollick_condition
    missing_data_counts['no_mollick_summary'] = db.papers.count_documents(no_mollick_query)

    # --- Concept facets ---
    concept_facets = []

    if base_query:
        logger.debug(f"Getting filtered concepts with base_query: {base_query}")
        concept_pipeline = [
            {'$match': base_query},
            {'$unwind': '$concept_ids'},
            {'$group': {
                '_id': '$concept_ids',
                'count': {'$sum': 1}
            }}
        ]
        filtered_concepts = list(db.papers.aggregate(concept_pipeline))
        logger.debug(f"Found {len(filtered_concepts)} unique concepts in filtered papers")

        if filtered_concepts:
            concept_ids_list = [c['_id'] for c in filtered_concepts]
            concept_details = list(db.tag_concepts_v2.find({'_id': {'$in': concept_ids_list}}))
            concept_map = {str(c['_id']): c['count'] for c in filtered_concepts}
            for concept in concept_details:
                concept_id = str(concept['_id'])
                if concept_id in concept_map:
                    concept_facets.append({
                        'concept_id': concept_id,
                        'id': f"c_{concept_id[:4]}",
                        'slug': concept.get('slug', ''),
                        'display_name': concept.get('display_name', ''),
                        'count': concept_map[concept_id]
                    })
            concept_facets.sort(key=lambda x: x['count'], reverse=True)
            logger.debug(f"Returning {len(concept_facets)} concept facets")
    else:
        logger.debug("No filters - returning all paper concepts")
        all_concepts = concept_service.get_all_concepts_with_counts(content_type='paper')
        concept_facets = all_concepts
        logger.debug(f"Returning {len(concept_facets)} concept facets")

    result = {
        'authors': [{'name': f['_id'], 'count': f['count']} for f in author_facets if f['_id']],
        'years': [{'year': f['_id'], 'count': f['count']} for f in year_facets if f['_id']],
        'conferences': [{'name': f['_id'], 'count': f['count']} for f in conference_facets if f['_id']],
        'journals': [{'name': f['_id'], 'count': f['count']} for f in journal_facets if f['_id']],
        'institutions': [{'name': f['_id'], 'count': f['count']} for f in institution_facets if f['_id']],
        'processors': [{'name': f['_id'], 'count': f['count']} for f in processor_facets if f['_id']],
        'special_filters': special_filters,
        'concepts': concept_facets,
        'missing_data': missing_data_counts,
        'paper_status': paper_status,
        'rating': rating_facet
    }

    logger.debug(f"Returning facets: authors={len(result['authors'])}, years={len(result['years'])}, institutions={len(result['institutions'])}, concepts={len(result['concepts'])}")
    return result



@router.get("/stats/overview")
def get_statistics(
    paper_type: str = Query("research", description="Paper type: research or review"),
) -> Dict[str, Any]:
    """Get paper statistics from MongoDB"""

    base_filter = {'paper_type': paper_type}

    # Count papers
    total_papers = db.papers.count_documents(base_filter)

    # Count papers with PDFs
    papers_with_pdf = db.papers.count_documents({**base_filter, 'pdf_path': {'$ne': None}})

    # Count unique authors - handle both string and array formats
    all_authors = set()

    # Get all papers to process authors
    papers = db.papers.find(base_filter, {'authors': 1, 'authors_detailed': 1})
    for paper in papers:
        # Try authors_detailed first (array of objects or strings)
        if paper.get('authors_detailed'):
            for author_a in paper['authors_detailed']:
                if isinstance(author_a, dict) and author_a.get('name'):
                    all_authors.add(author_a['name'].strip())
                elif isinstance(author_a, str) and author_a.strip():
                    all_authors.add(author_a.strip())
        # Fall back to authors field (might be string or array)
        elif paper.get('authors'):
            if isinstance(paper['authors'], str):
                for author_name in paper['authors'].split(','):
                    all_authors.add(author_name.strip())
            elif isinstance(paper['authors'], list):
                for author_a in paper['authors']:
                    if isinstance(author_a, str):
                        all_authors.add(author_a.strip())
                    elif isinstance(author_a, dict) and author_a.get('name'):
                        all_authors.add(author_a['name'].strip())

    unique_authors = len(all_authors)

    # Get date range
    oldest_paper = db.papers.find_one(base_filter, sort=[('publication_date', ASCENDING)])
    newest_paper = db.papers.find_one(base_filter, sort=[('publication_date', DESCENDING)])

    # Count concepts
    concepts = concept_service.get_all_concepts_with_counts(content_type='paper')

    # Count total snippets across all papers
    snippet_pipeline = [
        {'$match': base_filter},
        {'$unwind': '$snippets'},
        {'$count': 'total'}
    ]
    snippet_count_result = list(db.papers.aggregate(snippet_pipeline))
    total_snippets = snippet_count_result[0]['total'] if snippet_count_result else 0

    # Get top conferences
    top_conferences = list(db.papers.aggregate([
        {'$match': {**base_filter, 'conference': {'$ne': None}}},
        {'$group': {
            '_id': '$conference',
            'count': {'$sum': 1}
        }},
        {'$sort': {'count': -1}},
        {'$limit': 10}
    ]))

    return {
        "total_papers": total_papers,
        "papers_with_pdf": papers_with_pdf,
        "unique_authors": unique_authors,
        "total_authors": unique_authors,  # For frontend compatibility
        "total_concepts": len(concepts),
        "total_concept_tags": len(concepts),  # Updated naming
        "total_tags": len(concepts),  # For backwards compatibility
        "total_snippets": total_snippets,
        "date_range": {
            "oldest": oldest_paper.get('publication_date') if oldest_paper else None,
            "newest": newest_paper.get('publication_date') if newest_paper else None
        },
        "top_conferences": [
            {'name': conf['_id'], 'count': conf['count']}
            for conf in top_conferences
        ],
        "top_concepts": concepts[:10] if concepts else []
    }
