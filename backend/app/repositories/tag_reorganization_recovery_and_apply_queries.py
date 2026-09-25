"""
MongoDB queries of app.api.tag_reorganization.recovery_and_apply, moved verbatim out of the router
(one function per former inline call site).
"""
from datetime import datetime
from datetime import timezone
from app.database.mongodb import get_database

db = get_database()


def tag_reorganization_tasks_find_one__recover_task(task_id):
    """tag_reorganization_tasks.find_one from tag_reorganization.recovery_and_apply.recover_task()"""
    return db.tag_reorganization_tasks.find_one({'task_id': task_id}, {'_id': 0})


def tag_reorganization_tasks_find_one__apply_recovered_task(task_id):
    """tag_reorganization_tasks.find_one from tag_reorganization.recovery_and_apply.apply_recovered_task()"""
    return db.tag_reorganization_tasks.find_one({'task_id': task_id})


def tag_reorganization_tasks_find_one__apply_task_result(task_id):
    """tag_reorganization_tasks.find_one from tag_reorganization.recovery_and_apply.apply_task_result()"""
    return db.tag_reorganization_tasks.find_one({'task_id': task_id})


def tag_reorganization_tasks_update_one__recover_task(task_id):
    """tag_reorganization_tasks.update_one from tag_reorganization.recovery_and_apply.recover_task()"""
    return db.tag_reorganization_tasks.update_one(
        {'task_id': task_id},
        {'$set': {
            'status': 'interrupted',
            'error': 'Task was interrupted by server restart',
            'updated_at': datetime.now(timezone.utc)
        }}
    )


def tag_reorganization_tasks_update_one__apply_recovered_task(task_id):
    """tag_reorganization_tasks.update_one from tag_reorganization.recovery_and_apply.apply_recovered_task()"""
    return db.tag_reorganization_tasks.update_one(
        {'task_id': task_id},
        {'$set': {
            'metadata.applied': True,
            'metadata.applied_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        }}
    )


def tag_reorganization_tasks_update_one__apply_task_result(task_id):
    """tag_reorganization_tasks.update_one from tag_reorganization.recovery_and_apply.apply_task_result()"""
    return db.tag_reorganization_tasks.update_one(
        {'task_id': task_id},
        {'$set': {
            'metadata.applied': True,
            'metadata.applied_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        }}
    )
