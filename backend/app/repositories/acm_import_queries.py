"""
MongoDB queries of app.api.acm_import, moved verbatim out of the router
(one function per former inline call site).
"""
from app.database.mongodb import get_database

db = get_database()


def papers_insert_one__import_acm_paper(paper_doc):
    """papers.insert_one from acm_import.import_acm_paper()"""
    return db.papers.insert_one(paper_doc)
