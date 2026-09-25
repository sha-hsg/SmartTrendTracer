"""
Recovery and apply endpoints for tag reorganization.
Includes task recovery and result application.
"""

from fastapi import APIRouter, HTTPException

from .utils import (
    logger, active_tasks,
)
from app.repositories import tag_reorganization_recovery_and_apply_queries as queries

router = APIRouter()


@router.get("/recover/{task_id}")
async def recover_task(task_id: str):
    """Recover a task from MongoDB and load it into memory if needed"""

    # First check if task is already in memory
    if task_id in active_tasks:
        task = active_tasks[task_id]
        return {
            "status": "active",
            "task": task.to_dict() if hasattr(task, 'to_dict') else task
        }

    # Try to load from MongoDB
    task_doc = queries.tag_reorganization_tasks_find_one__recover_task(task_id)

    if not task_doc:
        raise HTTPException(status_code=404, detail="Task not found")

    # Convert datetime objects to ISO strings
    for field in ['created_at', 'updated_at', 'completed_at']:
        if task_doc.get(field) and hasattr(task_doc[field], 'isoformat'):
            task_doc[field] = task_doc[field].isoformat()

    # If task is completed or failed, return the stored result
    if task_doc.get('status') in ['completed', 'failed', 'cancelled']:
        return {
            "status": "recovered",
            "task": task_doc,
            "can_apply": task_doc.get('status') == 'completed' and task_doc.get('result') is not None
        }

    # If task was processing, mark it as interrupted
    if task_doc.get('status') in ['processing', 'initializing']:
        task_doc['status'] = 'interrupted'
        task_doc['error'] = 'Task was interrupted by server restart'
        # Update in MongoDB
        queries.tag_reorganization_tasks_update_one__recover_task(task_id)

    return {
        "status": "recovered",
        "task": task_doc,
        "can_apply": False
    }

@router.post("/apply-recovered/{task_id}")
async def apply_recovered_task(task_id: str):
    """Apply the results from a recovered completed task"""

    # Load task from MongoDB
    task_doc = queries.tag_reorganization_tasks_find_one__apply_recovered_task(task_id)

    if not task_doc:
        raise HTTPException(status_code=404, detail="Task not found")

    if task_doc.get('status') != 'completed':
        raise HTTPException(status_code=400, detail="Task is not completed")

    if not task_doc.get('result'):
        raise HTTPException(status_code=400, detail="Task has no result to apply")

    # Apply the reorganization result
    try:
        from app.services.tag_reorganization_apply_service import TagReorganizationApplyService
        apply_service = TagReorganizationApplyService()

        result = task_doc.get('result')
        apply_result = apply_service.apply_gpt5_result(result)

        # Update task to mark as applied
        queries.tag_reorganization_tasks_update_one__apply_recovered_task(task_id)

        return {
            "success": True,
            "message": "Reorganization results applied successfully",
            "stats": apply_result.get('stats', {})
        }

    except Exception as e:
        logger.error(f"Failed to apply recovered task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/apply/{task_id}")
async def apply_task_result(task_id: str, result_data: dict = None):
    """Apply the reorganization results for a task (can accept result data in body)"""

    # First check if task exists and get its result
    task_doc = queries.tag_reorganization_tasks_find_one__apply_task_result(task_id)

    if not task_doc:
        # If no task in MongoDB, check in-memory tasks
        if task_id in active_tasks:
            task = active_tasks[task_id]
            if hasattr(task, 'status') and task.status != 'completed':
                raise HTTPException(status_code=400, detail="Task is not completed")
            result = task.result if hasattr(task, 'result') else None
        else:
            raise HTTPException(status_code=404, detail="Task not found")
    else:
        if task_doc.get('status') != 'completed':
            raise HTTPException(status_code=400, detail="Task is not completed")
        result = task_doc.get('result')

    # Use provided result_data if available, otherwise use task's result
    if result_data:
        result = result_data
    elif not result:
        raise HTTPException(status_code=400, detail="No result data available to apply")

    # Apply the reorganization result
    try:
        from app.services.tag_reorganization_apply_service import TagReorganizationApplyService
        apply_service = TagReorganizationApplyService()

        apply_result = apply_service.apply_gpt5_result(result)

        # Update task to mark as applied (if in MongoDB)
        if task_doc:
            queries.tag_reorganization_tasks_update_one__apply_task_result(task_id)

        return {
            "success": True,
            "message": "Reorganization results applied successfully",
            "stats": apply_result.get('stats', {})
        }

    except Exception as e:
        logger.error(f"Failed to apply task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
