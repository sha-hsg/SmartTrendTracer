"""
MongoDB queries of app.api.direct_url_import, moved verbatim out of the router
(one function per former inline call site).
"""
from app.database.mongodb import get_database

db = get_database()


def papers_find_one__import_paper_from_url(url):
    """papers.find_one from direct_url_import.import_paper_from_url()"""
    return db.papers.find_one({'pdf_url': url})


def papers_insert_one__import_paper_from_url(paper_doc):
    """papers.insert_one from direct_url_import.import_paper_from_url()"""
    return db.papers.insert_one(paper_doc)


def papers_update_one__import_paper_from_url(result, concept_id):
    """papers.update_one from direct_url_import.import_paper_from_url()"""
    return db.papers.update_one(
        {'_id': result.inserted_id},
        {'$addToSet': {'concept_ids': concept_id}}
    )
