"""
MongoDB queries of app.api.tag_reorganization.routes, moved verbatim out of the router
(one function per former inline call site).
"""
from pymongo import DESCENDING
from app.database.mongodb import get_database

db = get_database()


def tag_reorganization_tasks_count_documents__get_task_history(query):
    """tag_reorganization_tasks.count_documents from tag_reorganization.routes.get_task_history()"""
    return db.tag_reorganization_tasks.count_documents(query)


def tag_reorganization_tasks_find__get_task_history(query, limit):
    """tag_reorganization_tasks.find from tag_reorganization.routes.get_task_history()"""
    return db.tag_reorganization_tasks.find(
            query,
            {'_id': 0}  # Exclude MongoDB _id field
        ).sort('created_at', DESCENDING).limit(limit)
