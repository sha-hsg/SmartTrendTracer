"""
MongoDB queries of app.api.papers.tag_suggestions, moved verbatim out of the router
(one function per former inline call site).
"""
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
