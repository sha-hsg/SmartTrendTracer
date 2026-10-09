"""
Batch annotation endpoints and helpers for tweets.
Routes: POST /batch-annotate, POST /batch-annotate-all, GET /batch-annotate/{task_id}/status, POST /batch-annotate/{task_id}/cancel
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, timezone
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from .utils import (
    logger, concept_service,
    batch_annotation_tasks, BatchAnnotateRequest,
)

router = APIRouter()


# =============================================================================
# Batch Annotation Helpers
# =============================================================================

class LLMSuggestionError(Exception):
    """Raised when the LLM call fails so callers can distinguish 'no suggestions' from 'call failed'."""


def generate_tag_suggestions_for_text(text: str, model: Optional[str] = None) -> List[Dict]:
    """Concept suggestions for a tweet text (app.services.concept_tagging).
    Raises LLMSuggestionError on transport/model errors — do NOT mark the tweet
    as annotated then."""
    from app.services import concept_tagging
    try:
        suggestions, _ = concept_tagging.suggest('tweet', {'text': text}, [], model=model)
    except concept_tagging.SuggestionError as e:
        raise LLMSuggestionError(str(e)) from e
    return suggestions


MAX_FINISHED_TASKS = 20


def create_annotation_task(task_id: str, total: int, annotate_all: bool = False) -> dict:
    """Register a task BEFORE the background worker starts, so status/cancel
    never 404 in the request-to-worker window (the frontend treats that 404 as
    'backend restarted, task finished'). Also evicts old finished tasks so the
    in-memory dict cannot grow forever."""
    finished = [tid for tid, t in batch_annotation_tasks.items()
                if t.get("status") in ("completed", "cancelled", "failed")]
    if len(finished) > MAX_FINISHED_TASKS:
        finished.sort(key=lambda tid: batch_annotation_tasks[tid].get("completed_at") or "")
        for tid in finished[:len(finished) - MAX_FINISHED_TASKS]:
            batch_annotation_tasks.pop(tid, None)

    batch_annotation_tasks[task_id] = {
        "status": "queued",
        "progress": 0,
        "total": total,
        "processed": 0,
        "new_tags_count": 0,
        "skipped_count": 0,
        "error_count": 0,
        "annotate_all": annotate_all,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "_cancel_event": threading.Event(),
    }
    return batch_annotation_tasks[task_id]


def run_batch_annotation(task_id: str, tweet_ids: List[str], model: Optional[str], concurrency: int = 1):
    """Process batch annotation in background, optionally parallel."""

    task = batch_annotation_tasks.get(task_id)
    if task is None:
        task = create_annotation_task(task_id, len(tweet_ids))
    task["status"] = "running"
    cancel_event = task["_cancel_event"]
    progress_lock = threading.Lock()
    total = len(tweet_ids)

    def annotate_one(tweet_id):
        if cancel_event.is_set():
            return

        local_new = 0
        local_skipped = 0
        local_error = 0
        result = None

        try:
            from app.services import concept_tagging
            outcome = concept_tagging.tag_item('tweet', str(tweet_id), model=model, concept_service=concept_service)
            if 'error' in outcome:
                result = outcome          # LLM failure or unknown tweet: stays in the unannotated pool
                local_error = 1
            else:
                result = {"status": "success", "new_concepts": outcome['new'], "skipped": outcome['skipped']}
                local_new = len(outcome['new'])
                local_skipped = outcome['skipped']
                local_error = 1 if outcome['failed'] else 0
        except Exception as e:
            logger.error(f"Error annotating tweet {tweet_id}: {e}")
            result = {"error": str(e)}
            local_error = 1

        with progress_lock:
            task["processed"] += 1
            task["new_tags_count"] += local_new
            task["skipped_count"] += local_skipped
            task["error_count"] += local_error
            task["progress"] = int((task["processed"] / total) * 100)
            # Keep only failures (bounded) — full per-tweet results for a 50k
            # run leaked memory for the process lifetime and were never read
            if local_error and len(task.setdefault("failed_tweets", {})) < 500:
                task["failed_tweets"][str(tweet_id)] = result

    try:
        _run_annotation_loop(task, tweet_ids, cancel_event, annotate_one, concurrency, task_id, total)
    except Exception as e:
        logger.error(f"Batch annotation {task_id} crashed: {e}")
        task["status"] = "failed"
        task["error"] = str(e)
        task["completed_at"] = datetime.now(timezone.utc).isoformat()
        task.pop("_cancel_event", None)
        return

    task["status"] = "cancelled" if cancel_event.is_set() else "completed"
    task["completed_at"] = datetime.now(timezone.utc).isoformat()
    task.pop("_cancel_event", None)  # Clean up internal reference

    logger.info(f"Batch annotation {task_id} {task['status']}: {task['new_tags_count']} new tags, {task['skipped_count']} skipped, {task['error_count']} errors")


def _run_annotation_loop(task, tweet_ids, cancel_event, annotate_one, concurrency, task_id, total):
    if concurrency <= 1:
        # Sequential (existing behavior for page-batch)
        for tweet_id in tweet_ids:
            if cancel_event.is_set():
                break
            annotate_one(tweet_id)
    else:
        # Parallel
        logger.info(f"Batch annotation {task_id}: using {concurrency} parallel workers for {total} tweets")
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = {executor.submit(annotate_one, tid): tid for tid in tweet_ids}
            for future in as_completed(futures):
                if cancel_event.is_set():
                    executor.shutdown(wait=False, cancel_futures=True)
                    break
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Unexpected error in annotation worker: {e}")


# =============================================================================
# Batch Annotation Endpoints
# =============================================================================

@router.post("/batch-annotate")
async def batch_annotate_tweets(
    request: BatchAnnotateRequest,
    background_tasks: BackgroundTasks
):
    """
    Start batch annotation of tweets.
    Returns immediately with a task_id for status polling.
    """
    if not request.tweet_ids:
        raise HTTPException(status_code=400, detail="No tweet IDs provided")

    # Dedupe while preserving order (a repeated id would be annotated twice)
    tweet_ids = list(dict.fromkeys(request.tweet_ids))

    task_id = str(uuid.uuid4())
    create_annotation_task(task_id, len(tweet_ids))

    # Start background task
    background_tasks.add_task(
        run_batch_annotation,
        task_id,
        tweet_ids,
        request.model
    )

    logger.info(f"Started batch annotation task {task_id} for {len(tweet_ids)} tweets")

    return {
        "task_id": task_id,
        "status": "started",
        "total": len(tweet_ids),
        "message": f"Batch annotation started for {len(tweet_ids)} tweets"
    }


@router.get("/batch-annotate/{task_id}/status")
async def get_batch_annotation_status(task_id: str):
    """
    Get the status of a batch annotation task.
    """
    task = batch_annotation_tasks.get(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        "task_id": task_id,
        "status": task["status"],
        "progress": task["progress"],
        "total": task["total"],
        "processed": task["processed"],
        "new_tags_count": task.get("new_tags_count", 0),
        "skipped_count": task.get("skipped_count", 0),
        "error_count": task.get("error_count", 0),
        "started_at": task.get("started_at"),
        "completed_at": task.get("completed_at")
    }


class BatchAnnotateAllRequest(BaseModel):
    """Request model for annotating all unannotated tweets"""
    model: Optional[str] = None
    concurrency: int = 4


@router.post("/batch-annotate-all")
async def batch_annotate_all_unannotated(
    request: BatchAnnotateAllRequest,
    background_tasks: BackgroundTasks
):
    """
    Start batch annotation for ALL unannotated tweets.
    Queries unannotated tweet IDs internally and starts background processing.
    Returns immediately with a task_id for status polling.
    """
    # Refuse overlapping annotate-all runs: two concurrent runs would compute
    # the same unannotated set and process every tweet twice (2x LLM spend)
    for tid, t in batch_annotation_tasks.items():
        if t.get("annotate_all") and t.get("status") in ("queued", "running"):
            raise HTTPException(
                status_code=409,
                detail=f"An annotate-all task is already running (task_id={tid})"
            )

    from app.services import concept_tagging
    unannotated_ids = concept_tagging.untagged_ids('tweet')

    if not unannotated_ids:
        return {
            "task_id": None,
            "status": "completed",
            "total": 0,
            "message": "All tweets are already annotated"
        }

    task_id = str(uuid.uuid4())
    create_annotation_task(task_id, len(unannotated_ids), annotate_all=True)

    concurrency = max(1, min(request.concurrency, 8))

    # Start background task
    background_tasks.add_task(
        run_batch_annotation,
        task_id,
        unannotated_ids,
        request.model,
        concurrency
    )

    logger.info(f"Started batch-annotate-all task {task_id} for {len(unannotated_ids)} unannotated tweets (concurrency={concurrency})")

    return {
        "task_id": task_id,
        "status": "started",
        "total": len(unannotated_ids),
        "concurrency": concurrency,
        "message": f"Batch annotation started for {len(unannotated_ids)} unannotated tweets ({concurrency} workers)"
    }


@router.post("/batch-annotate/{task_id}/cancel")
async def cancel_batch_annotation(task_id: str):
    """
    Cancel a running batch annotation task.
    The task will stop after completing the current tweet.
    """
    task = batch_annotation_tasks.get(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task["status"] != "running":
        raise HTTPException(status_code=400, detail=f"Task is not running (status: {task['status']})")

    cancel_event = task.get("_cancel_event")
    if cancel_event:
        cancel_event.set()
    else:
        task["cancelled"] = True  # fallback for legacy tasks
    logger.info(f"Cancel requested for batch annotation task {task_id}")

    return {
        "task_id": task_id,
        "status": "cancelling",
        "message": "Cancellation requested. Task will stop after current tweet."
    }
