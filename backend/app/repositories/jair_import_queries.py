"""
MongoDB queries of app.api.jair_import, moved verbatim out of the router
(one function per former inline call site).
"""
from app.database.mongodb import get_database

db = get_database()


def papers_find_one__import_jair_paper(dup_query):
    """papers.find_one from jair_import.import_jair_paper()"""
    return db.papers.find_one(dup_query)


def papers_insert_one__import_jair_paper(paper_doc):
    """papers.insert_one from jair_import.import_jair_paper()"""
    return db.papers.insert_one(paper_doc)
