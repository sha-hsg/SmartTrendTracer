"""
Data access for app.api.books.processing (extracted by the arch-audit refactor).

Book processing endpoints: queue-based and direct processing.
"""
from app.repositories.books import get_book_by_id
from app.repositories.errors import InvalidInputError, NotFoundError
from bson import ObjectId
from datetime import datetime
from datetime import timezone


from app.database.mongodb import get_database

db = get_database()
BOOK_PROCESSING_QUEUE = db.book_processing_jobs




def trigger_book_processing(book_id, preferred_processor):
    """Enqueue book processing job for asynchronous worker"""
    book = get_book_by_id(book_id)
    if not book:
        raise NotFoundError("Book not found")

    if book.get('processing_status') in {'processing', 'queued'}:
        raise InvalidInputError("Book is already scheduled or processing")

    # Prevent duplicate jobs in queue
    existing_job = BOOK_PROCESSING_QUEUE.find_one({
        'book_id': ObjectId(book_id),
        'status': {'$in': ['queued', 'processing']}
    })
    if existing_job:
        raise InvalidInputError("Book already has a queued job")

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

