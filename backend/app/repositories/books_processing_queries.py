"""
MongoDB queries of app.api.books.processing, moved verbatim out of the router
(one function per former inline call site).
"""
from bson import ObjectId
from datetime import datetime
from datetime import timezone
from app.database.mongodb import get_database

db = get_database()


def books_update_one__process_book_direct(book_id):
    """books.update_one from books.processing.process_book_direct()"""
    return db.books.update_one(
        {'_id': ObjectId(book_id)},
        {'$set': {
            'processing_status': 'processing',
            'processing_job_id': None,
            'updated_at': datetime.now(timezone.utc)
        }}
    )


def books_update_one__process_book_direct_2(update_data, book_id):
    """books.update_one from books.processing.process_book_direct()"""
    return db.books.update_one(
        {"_id": ObjectId(book_id)},
        {"$set": update_data}
    )


def books_update_one__process_book_direct_3(book_id, result):
    """books.update_one from books.processing.process_book_direct()"""
    return db.books.update_one(
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


def books_update_one__process_book_direct_4(book_id, e):
    """books.update_one from books.processing.process_book_direct()"""
    return db.books.update_one(
        {'_id': ObjectId(book_id)},
        {'$set': {
            'processing_status': 'failed',
            'processing_error': str(e),
            'processed_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
            'processing_job_id': None
        }}
    )
