"""
MongoDB queries of app.api.dblp_mongodb, moved verbatim out of the router
(one function per former inline call site).
"""
from bson import ObjectId
from app.database.mongodb import get_database

db = get_database()


def papers_update_one__attach_dblp_metadata(update_data, paper):
    """papers.update_one from dblp_mongodb.attach_dblp_metadata()"""
    return db.papers.update_one(
                    {'_id': paper['_id']},
                    {'$set': update_data}
                )


def papers_find_one__attach_dblp_metadata(paper_id):
    """papers.find_one from dblp_mongodb.attach_dblp_metadata()"""
    return db.papers.find_one({'_id': ObjectId(paper_id)})


def papers_find_one__attach_dblp_metadata_2(paper_id):
    """papers.find_one from dblp_mongodb.attach_dblp_metadata()"""
    return db.papers.find_one({'old_sqlite_id': int(paper_id)})
