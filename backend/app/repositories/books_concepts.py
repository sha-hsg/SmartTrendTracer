"""
Data access for app.api.books.concepts (extracted by the arch-audit refactor).

Books concept tag endpoints: add and remove concept tags from books.
"""
from app.repositories.books import get_book_by_id
from app.repositories.concepts import ConceptOnlyTagService
from app.repositories.errors import InvalidInputError, NotFoundError
from bson import ObjectId

concept_service = ConceptOnlyTagService()

from app.database.mongodb import get_database

db = get_database()




def add_concept_to_book(book_id, concept_data):
    """Add a concept tag to a book"""
    book = get_book_by_id(book_id)
    if not book:
        raise NotFoundError("Book not found")

    concept_name = concept_data.get('concept_name', '').strip()
    if not concept_name:
        raise InvalidInputError("Concept name is required")

    # Add concept using the concept service
    success, concept_id = concept_service.add_concept_to_content(
        content_id=book_id,
        content_type='book',
        concept_name=concept_name,
        context=book.get('title', '') + ' ' + book.get('summary', '')
    )

    if not success:
        raise InvalidInputError("Failed to add concept")

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



def remove_concept_from_book(book_id, concept_id):
    """Remove a concept tag from a book"""
    book = get_book_by_id(book_id)
    if not book:
        raise NotFoundError("Book not found")

    # Remove concept using the concept service
    success = concept_service.remove_concept_from_content(
        content_id=book_id,
        content_type='book',
        concept_id=concept_id
    )

    if not success:
        raise NotFoundError("Concept not found on this book")

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

