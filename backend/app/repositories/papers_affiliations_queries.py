"""
MongoDB queries of app.api.papers.affiliations, moved verbatim out of the router
(one function per former inline call site).
"""
from bson import ObjectId
from app.database.mongodb import get_database

db = get_database()


def papers_find_one__extract_paper_affiliations(paper_id):
    """papers.find_one from papers.affiliations.extract_paper_affiliations()"""
    return db.papers.find_one({'_id': ObjectId(paper_id)})


def papers_find_one__extract_paper_affiliations_2(paper_id):
    """papers.find_one from papers.affiliations.extract_paper_affiliations()"""
    return db.papers.find_one({'old_sqlite_id': int(paper_id)})
