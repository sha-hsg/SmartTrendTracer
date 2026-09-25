"""
MongoDB queries of app.api.papers.tag_suggestions, moved verbatim out of the router
(one function per former inline call site).
"""
from bson import ObjectId
from app.database.mongodb import get_database

db = get_database()


def tag_instances_find__get_tag_suggestions(paper_id_str, sqlite_id_str):
    """tag_instances.find from papers.tag_suggestions.get_tag_suggestions()"""
    return db.tag_instances.find({
            'content_type': 'paper',
            '$or': [
                {'content_id': paper_id_str},
                {'content_id': sqlite_id_str}
            ]
        })


def papers_find_one__get_tag_suggestions(paper_id):
    """papers.find_one from papers.tag_suggestions.get_tag_suggestions()"""
    return db.papers.find_one({'_id': ObjectId(paper_id)})


def papers_find_one__get_tag_suggestions_2(paper_id):
    """papers.find_one from papers.tag_suggestions.get_tag_suggestions()"""
    return db.papers.find_one({'old_sqlite_id': int(paper_id)})
