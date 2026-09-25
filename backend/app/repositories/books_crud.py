"""
Data access for app.api.books.crud (extracted by the arch-audit refactor).

Books CRUD operations: browse, facets, upload, update, delete, and concept management.
"""
from app.repositories.books import get_book_by_id
from app.repositories.errors import NotFoundError
from bson import ObjectId
from datetime import datetime
from datetime import timezone

from app.database.mongodb import get_database

db = get_database()




def update_book_metadata(book_id, metadata):
    """Update book metadata"""
    book = get_book_by_id(book_id)
    if not book:
        raise NotFoundError("Book not found")

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

