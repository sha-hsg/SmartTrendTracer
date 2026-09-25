"""
MongoDB queries of app.api.books.crud, moved verbatim out of the router
(one function per former inline call site).
"""
from bson import ObjectId
from app.database.mongodb import get_database

db = get_database()


def books_count_documents__get_books(query):
    """books.count_documents from books.crud.get_books()"""
    return db.books.count_documents(query)


def books_insert_one__upload_book(book_doc):
    """books.insert_one from books.crud.upload_book()"""
    return db.books.insert_one(book_doc)


def books_delete_one__delete_book(book_id):
    """books.delete_one from books.crud.delete_book()"""
    return db.books.delete_one({'_id': ObjectId(book_id)})


def tag_instances_find__get_books(instances_query):
    """tag_instances.find from books.crud.get_books()"""
    return db.tag_instances.find(instances_query)


def tag_concepts_v2_find__get_books(concept_query):
    """tag_concepts_v2.find from books.crud.get_books()"""
    return db.tag_concepts_v2.find(concept_query)


def tag_concepts_v2_find__get_book_details(concept_object_ids):
    """tag_concepts_v2.find from books.crud.get_book_details()"""
    return db.tag_concepts_v2.find(
                {'_id': {'$in': concept_object_ids}},
                {'name': 1, 'description': 1, 'entity_type': 1}
            )


def books_find__get_books(query):
    """books.find from books.crud.get_books()"""
    return db.books.find(query)
