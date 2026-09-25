"""
MongoDB queries of app.api.papers.grobid, moved verbatim out of the router
(one function per former inline call site).
"""
from bson import ObjectId
from app.database.mongodb import get_database

db = get_database()


def papers_update_one__process_with_grobid(update_data, paper):
    """papers.update_one from papers.grobid.process_with_grobid()"""
    return db.papers.update_one(
        {'_id': paper['_id']},
        {'$set': update_data}
    )


def papers_find_one__process_with_grobid(paper_id):
    """papers.find_one from papers.grobid.process_with_grobid()"""
    return db.papers.find_one({'_id': ObjectId(paper_id)})


def papers_find_one__process_with_grobid_2(paper_id):
    """papers.find_one from papers.grobid.process_with_grobid()"""
    return db.papers.find_one({'old_sqlite_id': int(paper_id)})
