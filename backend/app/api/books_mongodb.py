"""
Complete MongoDB-based books API.
Extended from papers API with book-specific metadata and features.
"""

from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Body, Request, BackgroundTasks
from fastapi.responses import FileResponse, Response
from pymongo import ASCENDING, DESCENDING
from app.database.mongodb import get_database
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import logging
from bson import ObjectId
import json
import os
import hashlib
from pathlib import Path
import shutil
import re

from app.services.concept_only_tag_service import ConceptOnlyTagService
from app.services.readability_service import ReadabilityService

logger = logging.getLogger(__name__)
router = APIRouter()

# MongoDB connection
# MongoDB connection
db = get_database()

# Initialize services
concept_service = ConceptOnlyTagService()
readability_service = ReadabilityService()

# Book storage directory
BOOKS_REPOSITORY = Path("data/book_repository")
BOOKS_REPOSITORY.parent.mkdir(parents=True, exist_ok=True)
BOOKS_REPOSITORY.mkdir(exist_ok=True)

# Queue collection for background processing
BOOK_PROCESSING_QUEUE = db.book_processing_jobs

def get_book_by_id(book_id: str):
    """Get book by MongoDB ObjectId - returns ObjectId converted to string"""
    try:
        if len(book_id) == 24:
            # Try as MongoDB ObjectId
            book = db.books.find_one({'_id': ObjectId(book_id)})
            if book:
                # Convert ObjectId to string to prevent serialization errors
                book['_id'] = str(book['_id'])
                if book.get('processing_job_id'):
                    try:
                        book['processing_job_id'] = str(book['processing_job_id'])
                    except Exception:
                        pass
                file_path_value = book.get('file_path')
                file_name_value = book.get('file_name') or (Path(file_path_value).name if file_path_value else None)
                if file_name_value:
                    book['file_name'] = file_name_value
                    book['file_url'] = f"/books/{book['_id']}/{file_name_value}"
                else:
                    book['file_url'] = None
                return book
            return None
        else:
            # Invalid ID format
            return None
    except:
        return None

@router.get("/")
def get_books(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    concept_id: Optional[str] = None,
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
    is_processed: Optional[bool] = None,
    no_processor: Optional[bool] = None,
    no_year: Optional[bool] = None,
    no_publisher: Optional[bool] = None,
    no_isbn: Optional[bool] = None,
    no_annotations: Optional[bool] = None
):
    """Get books with filtering and pagination from MongoDB"""

    # Build query
    query = {}

    if search:
        query['$text'] = {'$search': search}

    # Handle concept filters (support legacy string IDs and ObjectIds)
    if concept_ids:
        for cid in concept_ids:
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
    elif concept_id:
        normalized_cid = str(concept_id)
        concept_options = [{'concept_ids': normalized_cid}]

        if len(normalized_cid) == 24:
            try:
                concept_options.append({'concept_ids': ObjectId(normalized_cid)})
            except Exception:
                pass

        if concept_options:
            query.setdefault('$and', [])
            query['$and'].append({'$or': concept_options})

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

    # Missing data filters
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

    # Special filters
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

    skip = (page - 1) * page_size
    total = db.books.count_documents(query)

    books = list(
        db.books.find(query)
        .sort('uploaded_at', DESCENDING)
        .skip(skip)
        .limit(page_size)
    )

    book_id_strings: List[str] = []
    legacy_ids: List[str] = []
    for book in books:
        book_id_strings.append(str(book['_id']))
        legacy_id = book.get('old_sqlite_id')
        if legacy_id:
            legacy_ids.append(str(legacy_id))

    tag_instances_by_book: Dict[str, List[Dict[str, Any]]] = {}
    concept_ids_needed = set()

    if book_id_strings:
        instances_query = {
            'content_type': 'book',
            'content_id': {'$in': book_id_strings + legacy_ids}
        }
        for instance in db.tag_instances.find(instances_query):
            content_id = instance.get('content_id')
            if not content_id:
                continue
            tag_instances_by_book.setdefault(content_id, []).append(instance)
            cid = instance.get('concept_id')
            if cid is not None:
                concept_ids_needed.add(str(cid))

    concept_map: Dict[str, Dict[str, Any]] = {}
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

        concept_query = {'$or': []}
        if object_ids:
            concept_query['$or'].append({'_id': {'$in': object_ids}})
        if string_ids:
            concept_query['$or'].append({'id': {'$in': string_ids}})

        if concept_query['$or']:
            for doc in db.tag_concepts_v2.find(concept_query):
                doc['_id'] = str(doc['_id'])
                concept_map[doc['_id']] = doc
                if doc.get('id'):
                    concept_map[str(doc['id'])] = doc

    for book in books:
        mongo_id = str(book['_id'])
        book['_id'] = mongo_id

        if book.get('processing_job_id'):
            try:
                book['processing_job_id'] = str(book['processing_job_id'])
            except Exception:
                pass

        file_path_value = book.get('file_path')
        file_name_value = book.get('file_name') or (Path(file_path_value).name if file_path_value else None)
        if file_name_value:
            book['file_url'] = f"/books/{mongo_id}/{file_name_value}"
            book['file_name'] = file_name_value
        else:
            book['file_url'] = None

        if not book.get('processing_status'):
            book['processing_status'] = 'uploaded'

        instances = list(tag_instances_by_book.get(mongo_id, []))
        legacy_id = book.get('old_sqlite_id')
        if legacy_id:
            instances.extend(tag_instances_by_book.get(str(legacy_id), []))

        concept_refs = []
        concept_ids = []
        seen = set()

        for instance in instances:
            cid = instance.get('concept_id')
            if cid is None:
                continue
            key = str(cid)
            if key in seen:
                continue
            seen.add(key)
            concept_ids.append(key)
            concept_doc = concept_map.get(key)
            if concept_doc:
                concept_refs.append({
                    'concept_id': concept_doc['_id'],
                    'display_name': concept_doc.get('display_name'),
                    'slug': concept_doc.get('slug')
                })

        if not concept_refs and book.get('concept_ids'):
            for cid in book.get('concept_ids', []):
                key = str(cid)
                if key in seen:
                    continue
                seen.add(key)
                concept_ids.append(key)
                concept_doc = concept_map.get(key)
                if concept_doc:
                    concept_refs.append({
                        'concept_id': concept_doc['_id'],
                        'display_name': concept_doc.get('display_name'),
                        'slug': concept_doc.get('slug')
                    })

        book['concept_ids'] = concept_ids
        book['concepts'] = concept_refs
        book['tags'] = [ref['display_name'] for ref in concept_refs if ref.get('display_name')]

    # Calculate pagination info
    total_pages = (total + page_size - 1) // page_size

    return {
        'books': books,
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total': total,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
    }

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
            except:
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
        cutoff = datetime.utcnow() - timedelta(days=7)
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

@router.get("/{book_id}")
def get_book_details(book_id: str):
    """Get detailed book information"""
    book = get_book_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Convert concept_ids to strings
    if 'concept_ids' in book:
        book['concept_ids'] = [str(cid) for cid in book['concept_ids']]

    # Get associated concepts with details
    if 'concept_ids' in book and book['concept_ids']:
        concept_object_ids = [ObjectId(cid) for cid in book['concept_ids']]
        concepts = list(db.tag_concepts_v2.find(
            {'_id': {'$in': concept_object_ids}},
            {'name': 1, 'description': 1, 'entity_type': 1}
        ))
        for concept in concepts:
            concept['_id'] = str(concept['_id'])
        book['concepts'] = concepts

    return book

@router.post("/upload")
async def upload_book(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    authors: Optional[str] = None,
    publisher: Optional[str] = None,
    publication_year: Optional[int] = None,
    isbn: Optional[str] = None,
    genre: Optional[str] = None,
    subject_areas: Optional[str] = None,
    language: Optional[str] = "English"
):
    """Upload a new book (PDF or EPUB)"""

    # Validate file type
    if not file.filename.lower().endswith(('.pdf', '.epub')):
        raise HTTPException(status_code=400, detail="Only PDF and EPUB files are supported")

    file_type = 'pdf' if file.filename.lower().endswith('.pdf') else 'epub'

    # Generate book ID and sanitize filename to prevent traversal/unsafe characters
    book_id = ObjectId()
    book_dir = BOOKS_REPOSITORY / str(book_id)
    book_dir.mkdir(exist_ok=True)

    original_name = Path(file.filename or '').name
    sanitized_name = re.sub(r'[^A-Za-z0-9._-]', '_', original_name) if original_name else ''
    if not sanitized_name or sanitized_name in {'.', '..'}:
        sanitized_name = f"book_{book_id}.{file_type}"

    file_path = book_dir / sanitized_name
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Create book document
    book_doc = {
        '_id': book_id,
        'title': title or file.filename.rsplit('.', 1)[0],
        'authors': authors.split(',') if authors else [],
        'publisher': publisher,
        'publication_year': publication_year,
        'isbn': isbn,
        'genre': [genre] if genre else [],
        'subject_areas': subject_areas.split(',') if subject_areas else [],
        'language': language,
        'file_path': str(file_path),
        'file_name': sanitized_name,
        'file_type': file_type,
        'file_size': file_path.stat().st_size,
        'processing_status': 'pending',
        'concept_ids': [],
        'uploaded_at': datetime.now(timezone.utc),
        'created_at': datetime.now(timezone.utc),
        'updated_at': datetime.now(timezone.utc)
    }

    # Insert into MongoDB
    db.books.insert_one(book_doc)

    return {
        'book_id': str(book_id),
        'message': f'Book "{book_doc["title"]}" uploaded successfully',
        'file_type': file_type,
        'file_size': book_doc['file_size']
    }

@router.put("/{book_id}")
def update_book_metadata(book_id: str, metadata: Dict[str, Any] = Body(...)):
    """Update book metadata"""
    book = get_book_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Prepare update document
    update_doc = {'updated_at': datetime.now(timezone.utc)}

    # Update allowed fields
    allowed_fields = [
        'title', 'authors', 'publisher', 'publication_year', 'isbn',
        'edition', 'language', 'genre', 'subject_areas', 'page_count',
        'summary', 'key_themes', 'reading_difficulty'
    ]

    for field in allowed_fields:
        if field in metadata:
            if field in ['authors', 'genre', 'subject_areas', 'key_themes']:
                # Handle array fields
                if isinstance(metadata[field], str):
                    update_doc[field] = [item.strip() for item in metadata[field].split(',')]
                else:
                    update_doc[field] = metadata[field]
            else:
                update_doc[field] = metadata[field]

    # Update in MongoDB
    db.books.update_one(
        {'_id': ObjectId(book_id)},
        {'$set': update_doc}
    )

    return {'message': 'Book metadata updated successfully'}

@router.post("/{book_id}/concepts")
def add_concept_to_book(book_id: str, concept_data: Dict[str, Any] = Body(...)):
    """Add a concept tag to a book"""
    book = get_book_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    concept_name = concept_data.get('concept_name', '').strip()
    if not concept_name:
        raise HTTPException(status_code=400, detail="Concept name is required")

    # Add concept using the concept service
    success, concept_id = concept_service.add_concept_to_content(
        content_id=book_id,
        content_type='book',
        concept_name=concept_name,
        context=book.get('title', '') + ' ' + book.get('summary', '')
    )

    if not success:
        raise HTTPException(status_code=400, detail="Failed to add concept")

    # Update book's concept_ids in MongoDB
    concept_object_id = concept_id
    if isinstance(concept_id, str) and len(concept_id) == 24:
        try:
            concept_object_id = ObjectId(concept_id)
        except Exception:
            concept_object_id = concept_id

    db.books.update_one(
        {'_id': ObjectId(book_id)},
        {'$addToSet': {'concept_ids': concept_object_id if isinstance(concept_object_id, ObjectId) else concept_id}}
    )

    # Get concept details
    concept = concept_service.get_concept_by_id(concept_id)
    if concept and concept.get('_id'):
        concept['_id'] = str(concept['_id'])

    return {
        'message': f'Concept "{concept_name}" added to book',
        'concept': concept
    }

@router.delete("/{book_id}/concepts/{concept_id}")
def remove_concept_from_book(book_id: str, concept_id: str):
    """Remove a concept tag from a book"""
    book = get_book_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Remove concept using the concept service
    success = concept_service.remove_concept_from_content(
        content_id=book_id,
        content_type='book',
        concept_id=concept_id
    )

    if not success:
        raise HTTPException(status_code=404, detail="Concept not found on this book")

    # Update book's concept_ids in MongoDB
    pull_values = [concept_id]
    try:
        pull_values.append(ObjectId(concept_id))
    except Exception:
        pass

    db.books.update_one(
        {'_id': ObjectId(book_id)},
        {'$pull': {'concept_ids': {'$in': pull_values}}}
    )

    return {'message': 'Concept removed from book'}

@router.delete("/{book_id}")
def delete_book(book_id: str):
    """Delete a book and its associated files"""
    book = get_book_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Delete files
    book_dir = BOOKS_REPOSITORY / book_id
    if book_dir.exists():
        shutil.rmtree(book_dir)

    # Remove from MongoDB
    db.books.delete_one({'_id': ObjectId(book_id)})

    # Remove associated concept instances
    concept_service.remove_all_concepts_from_content(book_id, 'book')

    return {'message': f'Book "{book["title"]}" deleted successfully'}

@router.get("/{book_id}/content")
def get_book_content(book_id: str):
    """Get book's markdown content"""
    book = get_book_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    if not book.get('markdown_content'):
        raise HTTPException(status_code=404, detail="Book content not available - processing may be pending")

    return {
        'book_id': book_id,
        'title': book['title'],
        'content': book['markdown_content'],
        'processing_status': book.get('processing_status', 'unknown')
    }


@router.get("/{book_id}/download")
def download_book_file(book_id: str):
    """Download the original book file (PDF/EPUB)."""
    book = get_book_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    file_path_value = book.get('file_path')
    if not file_path_value:
        raise HTTPException(status_code=404, detail="Book file not found")

    file_path = Path(file_path_value)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Book file is missing on disk")

    filename = book.get('file_name') or file_path.name
    media_type = 'application/pdf' if file_path.suffix.lower() == '.pdf' else 'application/epub+zip'

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type
    )

@router.post("/{book_id}/process")
async def trigger_book_processing(
    book_id: str,
    preferred_processor: str = "auto"
):
    """Enqueue book processing job for asynchronous worker"""
    book = get_book_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    if book.get('processing_status') in {'processing', 'queued'}:
        raise HTTPException(status_code=400, detail="Book is already scheduled or processing")

    # Prevent duplicate jobs in queue
    existing_job = BOOK_PROCESSING_QUEUE.find_one({
        'book_id': ObjectId(book_id),
        'status': {'$in': ['queued', 'processing']}
    })
    if existing_job:
        raise HTTPException(status_code=400, detail="Book already has a queued job")

    job_doc = {
        'book_id': ObjectId(book_id),
        'preferred_processor': preferred_processor,
        'status': 'queued',
        'created_at': datetime.now(timezone.utc),
        'started_at': None,
        'completed_at': None,
        'attempts': 0,
        'last_error': None
    }

    result = BOOK_PROCESSING_QUEUE.insert_one(job_doc)

    # Update book status to queued and track current job id
    db.books.update_one(
        {'_id': ObjectId(book_id)},
        {'$set': {
            'processing_status': 'queued',
            'processing_error': None,
            'processing_job_id': result.inserted_id,
            'updated_at': datetime.now(timezone.utc)
        }}
    )

    return {
        'message': f'Book "{book["title"]}" queued for processing',
        'book_id': book_id,
        'job_id': str(result.inserted_id),
        'status': 'queued',
        'processor': preferred_processor,
        'file_type': book.get('file_type', 'unknown')
    }

@router.post("/{book_id}/process-direct")
async def process_book_direct(
    book_id: str,
    preferred_processor: str = "auto"  # "auto", "marker", "mineru", "epub_native"
):
    """
    Process book content directly (synchronous) - use for immediate processing
    WARNING: Can take 1-6 hours for large books, client timeout recommended
    """
    book = get_book_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    if not book.get("file_path"):
        raise HTTPException(status_code=400, detail="Book file not found")

    if book.get('processing_status') == 'processing':
        raise HTTPException(status_code=400, detail="Book is already being processed")

    # Update status to processing
    db.books.update_one(
        {'_id': ObjectId(book_id)},
        {'$set': {
            'processing_status': 'processing',
            'processing_job_id': None,
            'updated_at': datetime.now(timezone.utc)
        }}
    )

    try:
        # Import and use BookProcessorService
        from app.services.book_processor_service import BookProcessorService
        processor = BookProcessorService()

        # Determine file type from extension
        file_path = book["file_path"]
        file_type = "epub" if file_path.lower().endswith('.epub') else "pdf"

        logger.info(f"Direct processing book {book_id} ({file_type}) with {preferred_processor}")

        # Process the book
        result = await processor.process_book(
            book_id=book_id,
            file_path=file_path,
            file_type=file_type,
            preferred_processor=preferred_processor
        )

        if result["success"]:
            # Update book document with extracted content and metadata
            update_data = {
                "markdown_content": result["markdown"],
                "processing_metadata": result.get("metadata", {}),
                "processing_method": result["method_used"],
                "processing_time": result.get("processing_time"),
                "images_extracted": result.get("images_extracted", False),
                "page_count": result.get("page_count"),
                "processing_status": "completed",
                "processed_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "processing_job_id": None
            }

            # Extract book-specific metadata if available
            metadata = result.get("metadata", {})
            if "table_of_contents" in metadata:
                update_data["table_of_contents"] = metadata["table_of_contents"]

            if "glossary_terms" in metadata:
                update_data["glossary_terms"] = metadata["glossary_terms"]

            if "reading_difficulty" in metadata:
                update_data["reading_difficulty"] = metadata["reading_difficulty"]

            # Update the book document
            db.books.update_one(
                {"_id": ObjectId(book_id)},
                {"$set": update_data}
            )

            logger.info(f"Book {book_id} processed successfully with {result['method_used']}")

            return {
                "status": "completed",
                "message": f"Book processed successfully using {result['method_used']}",
                "book_id": book_id,
                "processor": result["method_used"],
                "markdown_length": len(result["markdown"]),
                "processing_time": result.get("processing_time"),
                "images_extracted": result.get("images_extracted", False),
                "has_toc": "table_of_contents" in metadata,
                "has_glossary": "glossary_terms" in metadata,
                "reading_difficulty": metadata.get("reading_difficulty")
            }
        else:
            # Update book with error status
            db.books.update_one(
                {"_id": ObjectId(book_id)},
                {"$set": {
                    "processing_status": "failed",
                    "processing_error": result.get("error", "Processing failed"),
                    "processing_method": result.get("method_used"),
                    "processed_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                    "processing_job_id": None
                }}
            )

            logger.error(f"Book {book_id} processing failed: {result.get('error')}")

            raise HTTPException(
                status_code=500,
                detail=f"Processing failed: {result.get('error', 'Unknown error')}"
            )

    except Exception as e:
        logger.error(f"Error processing book {book_id}: {e}")
        # Update book with error status
        db.books.update_one(
            {'_id': ObjectId(book_id)},
            {'$set': {
                'processing_status': 'failed',
                'processing_error': str(e),
                'processed_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc),
                'processing_job_id': None
            }}
        )
        raise HTTPException(status_code=500, detail=str(e))
