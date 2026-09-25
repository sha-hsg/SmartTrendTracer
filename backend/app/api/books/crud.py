"""
Books CRUD operations: browse, facets, upload, update, delete, and concept management.
"""

from fastapi import APIRouter

from .utils import (
    Body,
    Dict,
    Any,
    File,
    HTTPException,
    List,
    ObjectId,
    Optional,
    Path,
    Query,
    UploadFile,
    DESCENDING,
    datetime,
    timezone,
    logging,
    re,
    shutil,
    db,
    concept_service,
    BOOKS_REPOSITORY,
    get_book_by_id,
)
from app.repositories.book_queries import (
    build_search_filter,
    build_concept_filter,
    build_multi_value_filter,
    build_year_filter,
    build_special_filters,
)
from app.repositories import books_crud as repo

router = APIRouter()

logger = logging.getLogger("app.api.books.crud")


@router.get("/")
def get_books(
    page: int = Query(1, ge=1, le=10000),
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

    # Build query using extracted helpers
    query = {}
    build_search_filter(query, search)
    build_concept_filter(query, concept_id, concept_ids)
    build_multi_value_filter(query, field='authors', values=authors, single_value=author, use_regex=True)
    build_multi_value_filter(query, field='publisher', values=publishers, single_value=publisher, use_regex=True)
    build_multi_value_filter(query, field='genre', values=genres, single_value=genre)
    build_multi_value_filter(query, field='subject_areas', values=subject_areas, single_value=subject_area)
    build_multi_value_filter(query, field='language', values=languages, single_value=language)
    build_multi_value_filter(query, field='reading_difficulty', values=difficulty_levels, single_value=reading_difficulty)
    build_multi_value_filter(query, field='processor', values=processors, single_value=processor)
    build_multi_value_filter(query, field='file_type', values=file_types, single_value=file_type)
    build_year_filter(query, year, years)
    build_special_filters(
        query,
        special_filter=special_filter,
        is_processed=is_processed,
        no_processor=no_processor,
        no_year=no_year,
        no_publisher=no_publisher,
        no_isbn=no_isbn,
        no_annotations=no_annotations,
    )

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
        concept_object_ids = []
        for cid in book['concept_ids']:
            try:
                concept_object_ids.append(ObjectId(cid))
            except Exception:
                pass  # Skip non-ObjectId concept ids (legacy string ids)
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
    return repo.update_book_metadata(book_id=book_id, metadata=metadata)

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
