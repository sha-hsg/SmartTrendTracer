"""
Batch annotation endpoints and helpers for tweets.
Routes: POST /batch-annotate, POST /batch-annotate-all, GET /batch-annotate/{task_id}/status, POST /batch-annotate/{task_id}/cancel
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, timezone
from bson import ObjectId
import uuid
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from .utils import (
    logger, db, concept_service, llm_manager,
    batch_annotation_tasks, BatchAnnotateRequest,
)

router = APIRouter()


# =============================================================================
# Batch Annotation Helpers
# =============================================================================

class LLMSuggestionError(Exception):
    """Raised when the LLM call fails so callers can distinguish 'no suggestions' from 'call failed'."""


def generate_tag_suggestions_for_text(text: str, model: Optional[str] = None) -> List[Dict]:
    """
    Generate tag suggestions for a given text using LLM.
    Returns list of suggested concepts with display_name, slug, and entity_type.
    Raises LLMSuggestionError on transport/model errors — do NOT mark the tweet as
    annotated when this fires; the sentinel write is only correct when the model
    genuinely returned an empty list.

    Model resolution: if `model` is None, llm_manager routes via the 'tag_suggestion'
    task_type — respecting the user preference in llm_preferences and the fallback
    chain in litellm_config.yaml. Do not hardcode model IDs here.
    """
    prompt = f"""Analyze this tweet and suggest relevant concept tags.

Tweet: {text}

Instructions:
1. Suggest 3-5 relevant concepts for this tweet
2. Focus on main topics, technologies, people, organizations mentioned
3. Use snake_case for slugs (e.g., machine_learning, sam_altman)
4. Use proper capitalization for display names (e.g., "Machine Learning", "Sam Altman")

Return as JSON array with format:
[
  {{
    "display_name": "Proper Name",
    "slug": "snake_case_slug",
    "entity_type": "topic|person|organisation|location|event|product"
  }}
]
"""

    try:
        messages = [{"role": "user", "content": prompt}]

        response = llm_manager.completion_sync(
            task_type='tag_suggestion',
            messages=messages,
            user_id='default',
            override_params={'model': model} if model else None
        )

        response_text = response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error generating tag suggestions: {e}")
        raise LLMSuggestionError(str(e)) from e

    if not response_text:
        return []

    # Extract JSON from response (handle markdown code blocks)
    json_text = response_text.strip()
    if json_text.startswith("```json"):
        json_text = json_text[7:]
    if json_text.startswith("```"):
        json_text = json_text[3:]
    if json_text.endswith("```"):
        json_text = json_text[:-3]

    try:
        return json.loads(json_text.strip())
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse LLM tag response as JSON: {e}; text={json_text[:200]!r}")
        return []


def run_batch_annotation(task_id: str, tweet_ids: List[str], model: Optional[str], concurrency: int = 1):
    """Process batch annotation in background, optionally parallel."""

    cancel_event = threading.Event()
    progress_lock = threading.Lock()
    total = len(tweet_ids)

    batch_annotation_tasks[task_id] = {
        "status": "running",
        "progress": 0,
        "total": total,
        "processed": 0,
        "new_tags_count": 0,
        "skipped_count": 0,
        "error_count": 0,
        "results": {},
        "started_at": datetime.now(timezone.utc).isoformat(),
        "_cancel_event": cancel_event,
    }

    task = batch_annotation_tasks[task_id]

    def annotate_one(tweet_id):
        if cancel_event.is_set():
            return

        local_new = 0
        local_skipped = 0
        local_error = 0
        result = None

        try:
            tweet = db.tweets.find_one({"_id": tweet_id})
            if not tweet:
                result = {"error": "not_found"}
                local_error = 1
            else:
                existing_concepts = concept_service.get_tags_for_content('tweet', tweet_id)
                existing_slugs = {c['slug'] for c in existing_concepts}

                tweet_text = tweet.get('full_text', '') or tweet.get('text', '')
                try:
                    suggestions = generate_tag_suggestions_for_text(tweet_text, model)
                except LLMSuggestionError as e:
                    # LLM call failed — do NOT write a sentinel; the tweet must remain
                    # in the unannotated pool so a retry can pick it up.
                    result = {"error": f"llm_failed: {e}"}
                    local_error = 1
                    suggestions = None

                if suggestions is not None:
                    new_concepts = []
                    skipped = 0
                    for suggestion in suggestions:
                        slug = suggestion.get('slug', '')
                        if slug and slug not in existing_slugs:
                            success, concept_id = concept_service.add_tag(
                                content_type='tweet',
                                content_id=tweet_id,
                                text=suggestion['display_name'],
                                preserve_display_name=True
                            )
                            if success:
                                new_concepts.append(suggestion['display_name'])
                                existing_slugs.add(slug)
                        else:
                            skipped += 1

                    # Sentinel only when the LLM genuinely returned no useful concepts
                    # AND the tweet had none before — prevents re-processing empty tweets.
                    if not new_concepts and not existing_concepts:
                        db.tag_instances.update_one(
                            {'content_type': 'tweet', 'content_id': str(tweet_id), 'concept_id': None},
                            {'$setOnInsert': {
                                'content_type': 'tweet',
                                'content_id': str(tweet_id),
                                'concept_id': None,
                                'display_name': '_no_concepts',
                                'created_at': datetime.now(timezone.utc),
                                'source': 'auto_annotation',
                            }},
                            upsert=True
                        )

                    result = {"status": "success", "new_concepts": new_concepts, "skipped": skipped}
                    local_new = len(new_concepts)
                    local_skipped = skipped

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
            task["results"][str(tweet_id)] = result

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

    task["status"] = "cancelled" if cancel_event.is_set() else "completed"
    task["completed_at"] = datetime.now(timezone.utc).isoformat()
    task.pop("_cancel_event", None)  # Clean up internal reference

    logger.info(f"Batch annotation {task_id} {task['status']}: {task['new_tags_count']} new tags, {task['skipped_count']} skipped, {task['error_count']} errors")


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

    task_id = str(uuid.uuid4())

    # Start background task
    background_tasks.add_task(
        run_batch_annotation,
        task_id,
        request.tweet_ids,
        request.model
    )

    logger.info(f"Started batch annotation task {task_id} for {len(request.tweet_ids)} tweets")

    return {
        "task_id": task_id,
        "status": "started",
        "total": len(request.tweet_ids),
        "message": f"Batch annotation started for {len(request.tweet_ids)} tweets"
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
    # Get all annotated tweet IDs from tag_instances
    annotated_pipeline = [
        {'$match': {'content_type': 'tweet'}},
        {'$group': {'_id': '$content_id'}},
        {'$project': {'content_id': '$_id', '_id': 0}}
    ]
    annotated_results = list(db.tag_instances.aggregate(annotated_pipeline))
    annotated_ids = set()
    for r in annotated_results:
        tid = r['content_id']
        annotated_ids.add(tid)
        # Also add as ObjectId if it's a valid string
        if isinstance(tid, str) and len(tid) == 24:
            try:
                annotated_ids.add(ObjectId(tid))
            except Exception:
                pass

    # Get all tweet IDs that are NOT annotated
    all_tweet_ids = db.tweets.distinct('_id')
    unannotated_ids = [tid for tid in all_tweet_ids if tid not in annotated_ids and str(tid) not in annotated_ids]

    if not unannotated_ids:
        return {
            "task_id": None,
            "status": "completed",
            "total": 0,
            "message": "All tweets are already annotated"
        }

    task_id = str(uuid.uuid4())

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
