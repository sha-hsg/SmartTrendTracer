"""
Books facet endpoints: filter options and statistics for the faceted browser.
"""

from fastapi import APIRouter

from .utils import (
    Any,
    Dict,
    List,
    ObjectId,
    Optional,
    Query,
    DESCENDING,
    datetime,
    timezone,
    timedelta,
    logging,
    db,
    concept_service,
)

router = APIRouter()

logger = logging.getLogger("app.api.books.facets")


@router.get("/facets")
def get_book_facets(
    search: Optional[str] = None,
    concept_ids: Optional[List[str]] = Query(None),
    author: Optional[str] = None,
    authors: Optional[List[str]] = Query(None),
    publisher: Optional[str] = None,
    publishers: Optional[List[str]] = Query(None),
    genre: Optional[str] = None,
    genres: Optional[List[str]] = Query(None),
    subject_area: Optional[str] = None,
    subject_areas: Optional[List[str]] = Query(None),
    language: Optional[str] = None,
    languages: Optional[List[str]] = Query(None),
    reading_difficulty: Optional[str] = None,
    difficulty_levels: Optional[List[str]] = Query(None),
    processor: Optional[str] = None,
    processors: Optional[List[str]] = Query(None),
    file_type: Optional[str] = None,
    file_types: Optional[List[str]] = Query(None),
    year: Optional[int] = None,
    years: Optional[List[int]] = Query(None),
    special_filter: Optional[str] = None,
    is_processed: Optional[bool] = None
):
    """Get all available facet values for filtering books, respecting current filters"""

    # Build query using the same logic as the main books endpoint
    query = {}

    if search:
        query['$text'] = {'$search': search}

    # Handle multiple concept IDs (AND logic - book must have ALL selected concepts)
    if concept_ids and len(concept_ids) > 0:
        concept_object_ids = []
        for cid in concept_ids:
            try:
                concept_object_ids.append(ObjectId(cid))
            except Exception:
                pass

        if concept_object_ids:
            query['concept_ids'] = {'$all': concept_object_ids}

    # Author filtering
    if authors and len(authors) > 0:
        query['authors'] = {'$in': authors}
    elif author:
        query['authors'] = {'$regex': author, '$options': 'i'}

    # Publisher filtering
    if publishers and len(publishers) > 0:
        query['publisher'] = {'$in': publishers}
    elif publisher:
        query['publisher'] = {'$regex': publisher, '$options': 'i'}

    # Genre filtering
    if genres and len(genres) > 0:
        query['genre'] = {'$in': genres}
    elif genre:
        query['genre'] = genre

    # Subject area filtering
    if subject_areas and len(subject_areas) > 0:
        query['subject_areas'] = {'$in': subject_areas}
    elif subject_area:
        query['subject_areas'] = subject_area

    # Language filtering
    if languages and len(languages) > 0:
        query['language'] = {'$in': languages}
    elif language:
        query['language'] = language

    # Reading difficulty filtering
    if difficulty_levels and len(difficulty_levels) > 0:
        query['reading_difficulty'] = {'$in': difficulty_levels}
    elif reading_difficulty:
        query['reading_difficulty'] = reading_difficulty

    # Processor filtering
    if processors and len(processors) > 0:
        query['processor'] = {'$in': processors}
    elif processor:
        query['processor'] = processor

    # File type filtering
    if file_types and len(file_types) > 0:
        query['file_type'] = {'$in': file_types}
    elif file_type:
        query['file_type'] = file_type

    # Year filtering
    if years and len(years) > 0:
        query['publication_year'] = {'$in': years}
    elif year:
        query['publication_year'] = year

    # Processing status filtering
    if is_processed is not None:
        if is_processed:
            query['processing_status'] = 'completed'
        else:
            query['processing_status'] = {'$ne': 'completed'}

    # Special filters
    if special_filter == 'recently_uploaded':
        from datetime import timedelta
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

    # Get distinct values for each facet from filtered results
    facets = {
        'authors': list(db.books.distinct('authors', query)),
        'publishers': list(db.books.distinct('publisher', query)),
        'genres': list(db.books.distinct('genre', query)),
        'subject_areas': list(db.books.distinct('subject_areas', query)),
        'languages': list(db.books.distinct('language', query)),
        'reading_difficulties': list(db.books.distinct('reading_difficulty', query)),
        'processors': list(db.books.distinct('processor', query)),
        'file_types': list(db.books.distinct('file_type', query)),
        'years': sorted(list(db.books.distinct('publication_year', query)), reverse=True)
    }

    # Get concept facets respecting the current filters
    concept_facets = concept_service.get_all_concepts_with_counts(content_type='book')
    facets['concepts'] = [
        {
            'concept_id': item.get('concept_id') or str(item.get('_id')),
            'display_name': item.get('display_name', ''),
            'count': item.get('count', 0)
        }
        for item in concept_facets
    ]

    # Get missing data counts based on filtered results
    total_books = db.books.count_documents(query)
    missing_data = {
        'no_processor': db.books.count_documents({**query, 'processor': {'$exists': False}}),
        'no_year': db.books.count_documents({**query, 'publication_year': {'$exists': False}}),
        'no_publisher': db.books.count_documents({**query, 'publisher': {'$exists': False}}),
        'no_isbn': db.books.count_documents({**query, 'isbn': {'$exists': False}}),
        'no_annotations': db.books.count_documents({
            **query,
            '$or': [
                {'concept_ids': {'$exists': False}},
                {'concept_ids': {'$size': 0}}
            ]
        })
    }

    # Get processing statistics based on filtered results
    processing_stats = {
        'completed': db.books.count_documents({**query, 'processing_status': 'completed'}),
        'processing': db.books.count_documents({**query, 'processing_status': 'processing'}),
        'failed': db.books.count_documents({**query, 'processing_status': 'failed'}),
        'pending': db.books.count_documents({**query, 'processing_status': 'pending'}),
        'queued': db.books.count_documents({**query, 'processing_status': 'queued'})
    }

    return {
        'facets': facets,
        'missing_data': missing_data,
        'processing_stats': processing_stats,
        'total_books': total_books
    }
