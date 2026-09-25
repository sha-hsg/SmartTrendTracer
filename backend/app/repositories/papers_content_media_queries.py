"""
MongoDB queries of app.api.papers.content_media, moved verbatim out of the router
(one function per former inline call site).
"""
from bson import ObjectId
from app.database.mongodb import get_database

db = get_database()


def papers_find__get_paper_image():
    """papers.find from papers.content_media.get_paper_image()"""
    return db.papers.find({}, {'_id': 1, 'title': 1, 'processor_used': 1})


def papers_find_one__get_paper_image(paper_id):
    """papers.find_one from papers.content_media.get_paper_image()"""
    return db.papers.find_one({'_id': ObjectId(paper_id)})


def papers_find_one__get_paper_image_2(paper_id):
    """papers.find_one from papers.content_media.get_paper_image()"""
    return db.papers.find_one({'old_sqlite_id': int(paper_id)})


def papers_find_one__get_paper_image_3(p):
    """papers.find_one from papers.content_media.get_paper_image()"""
    return db.papers.find_one({'_id': p['_id']})
