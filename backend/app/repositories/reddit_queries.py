"""
MongoDB queries of app.api.reddit_mongodb, moved verbatim out of the router
(one function per former inline call site).
"""
from app.database.mongodb import get_database

db = get_database()


def tag_instances_find___build_reddit_query(concept_filter):
    """tag_instances.find from reddit_mongodb._build_reddit_query()"""
    return db.tag_instances.find({"concept_id": concept_filter})
