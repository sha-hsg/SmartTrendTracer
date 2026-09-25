"""
MongoDB queries of app.api.papers.crud, moved verbatim out of the router
(one function per former inline call site).
"""
from app.database.mongodb import get_database

db = get_database()


def tag_instances_find__get_paper(paper_id, sqlite_id):
    """tag_instances.find from papers.crud.get_paper()"""
    return db.tag_instances.find({
            'content_type': 'paper',
            '$or': [
                {'content_id': paper_id},
                {'content_id': sqlite_id}
            ]
        })
