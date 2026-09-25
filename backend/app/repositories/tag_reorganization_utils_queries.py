"""
MongoDB queries of app.api.tag_reorganization.utils, moved verbatim out of the router
(one function per former inline call site).
"""
from app.database.mongodb import get_database

db = get_database()


def tag_reorganization_tasks_replace_one___save_to_db(doc, self):
    """tag_reorganization_tasks.replace_one from tag_reorganization.utils._save_to_db()"""
    return db.tag_reorganization_tasks.replace_one(
        {'task_id': self.task_id},
        doc,
        upsert=True
    )
