"""Book lookups shared by the books API package."""
from pathlib import Path
from bson import ObjectId
from app.database.mongodb import get_database

db = get_database()


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
    except Exception:
        return None
