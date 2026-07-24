"""
Core reorganization endpoints: start, stream, cancel, result, history
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional
import json
import asyncio
import uuid
import time
from datetime import datetime, timezone
from pymongo import DESCENDING

from .utils import (
    logger, tasks_collection, active_tasks,
    ReorganizationTask,
    ComprehensiveTagReorganizer, GPT5TagReorganizer,
)

router = APIRouter()


async def run_reorganization_async(task: ReorganizationTask):
    """Run the reorganization process asynchronously with progress updates"""
    try:
        task.update(status="starting", progress=5,
                   current_step="Initializing reorganization process...")
        await asyncio.sleep(1)  # Small delay for UI to catch up

        if task.mode == "comprehensive":
            reorganizer = ComprehensiveTagReorganizer()
            task.update(message="Using Comprehensive Tag Reorganizer")
        else:
            # Check if there's a model override
            model_override = getattr(task, 'model_override', None)
            reorganizer = GPT5TagReorganizer(model_override=model_override)

            # Update message based on model
            if model_override == 'gpt5':
                task.update(message="Using GPT-5 (2025-08-07) Enhanced Tag Reorganizer")
            else:
                task.update(message="Using Gemini 2.5 Pro Enhanced Tag Reorganizer")

        # Phase 1: Collect existing tags
        task.update(status="collecting", progress=10,
                   current_step="Collecting existing tags from database...")

        # Collect tags from MongoDB
        from app.services.concept_only_tag_service import ConceptOnlyTagService
        concept_service = ConceptOnlyTagService()

        # Get ALL concepts including unused ones - critical for seeing the full hierarchy!
        # This ensures GPT-5 sees parent categories and can properly organize concepts
        all_concepts = concept_service.get_all_concepts_with_counts(include_unused=True)

        # Also collect tags by content type (these only include used concepts)
        tweet_tags = [c['slug'] for c in concept_service.get_all_concepts_with_counts(content_type='tweet')]
        paper_tags = [c['slug'] for c in concept_service.get_all_concepts_with_counts(content_type='paper')]
        article_tags = [c['slug'] for c in concept_service.get_all_concepts_with_counts(content_type='article')]

        all_tags = {
            'tweet_tags': tweet_tags,
            'paper_tags': paper_tags,
            'article_tags': article_tags
        }

        task.update(progress=15, message=f"Found {len(tweet_tags)} tweet concepts (used)")
        await asyncio.sleep(0.5)

        task.update(progress=20, message=f"Found {len(paper_tags)} paper concepts (used)")
        await asyncio.sleep(0.5)

        task.update(progress=25, message=f"Found {len(article_tags)} article concepts (used)")

        total_tags = len(all_concepts)
        used_concepts = len([c for c in all_concepts if c['count'] > 0])
        unused_concepts = len([c for c in all_concepts if c['count'] == 0])
        parent_concepts = len([c for c in all_concepts if c.get('is_parent', False)])

        # Store metadata for recovery
        task.concepts_count = total_tags
        task.organized_count = 0  # Will be updated after reorganization
        task.unorganized_count = total_tags
        task.update(message=f"Total concepts: {total_tags} ({used_concepts} used, {unused_concepts} unused, {parent_concepts} parents)")

        # Phase 2: Analyze with AI
        task.update(status="analyzing", progress=30,
                   current_step="Analyzing tags with AI model...")

        if task.mode == "gpt5":
            task.update(message="Preparing tags for GPT-5 analysis...")
            await asyncio.sleep(1)

            # Call the actual GPT-5 reorganizer
            task.update(progress=40, message="Sending tags to language model...")

            # Run the actual reorganization (this is the long-running part)
            # We'll check for cancellation periodically
            start_time = time.time()

            # Create a callback function for progress updates
            def progress_callback(msg: str, progress_pct: int = None):
                if progress_pct:
                    # Map progress to 40-80% range during analysis
                    mapped_progress = 40 + int(progress_pct * 0.4)
                    task.update(progress=mapped_progress, message=msg)
                else:
                    task.update(message=msg)

            # Prepare tags data for reorganizer - include IDs for proper mapping
            tags_data = []
            for concept in all_concepts:
                tags_data.append({
                    'id': concept.get('id', str(concept.get('_id', ''))),  # Include concept ID
                    'tag': concept['slug'],
                    'display_name': concept.get('display_name', concept['slug']),
                    'count': concept['count'],
                    'entity_type': concept.get('entity_type', 'concept'),
                    'current_parents': [str(p) for p in concept.get('parents', [])]
                })

            # Check for cancellation before starting the (long-running) LLM call
            if task.cancelled:
                task.end_time = datetime.now(timezone.utc)
                task.update(status="cancelled", message="Process cancelled by user")
                task._save_to_db()
                return

            # Call the reorganizer with progress callback and get debug info
            recommendations, debug_info = await asyncio.to_thread(
                reorganizer.reorganize_tags_with_debug,
                tags_data,
                progress_callback
            )

            # Check for cancellation right after the LLM call returns —
            # discard the result instead of formatting/saving it
            if task.cancelled:
                task.end_time = datetime.now(timezone.utc)
                task.update(status="cancelled", message="Process cancelled by user during LLM analysis")
                task._save_to_db()
                return

            # Send the prompt as a debug message
            if debug_info and 'prompt' in debug_info:
                task.update(message=f"[DEBUG] Prompt size: {len(debug_info['prompt'])} characters")
                # Store the prompt in the task for later retrieval
                task.debug_prompt = debug_info.get('prompt', '')
                task.debug_system_prompt = debug_info.get('system_prompt', '')

            elapsed = time.time() - start_time
            task.update(progress=80, message=f"AI analysis completed in {elapsed:.1f} seconds")

        else:
            # Comprehensive mode - use rule-based analysis
            task.update(message="Running comprehensive rule-based analysis...")

            analysis_steps = [
                (35, "Identifying duplicates and variations..."),
                (45, "Finding semantic relationships..."),
                (55, "Building hierarchical structure..."),
                (65, "Detecting entity types..."),
                (75, "Creating canonical forms...")
            ]

            for progress, step_msg in analysis_steps:
                if task.cancelled:
                    task.update(status="cancelled", message="Process cancelled by user")
                    return

                task.update(progress=progress, message=step_msg)
                await asyncio.sleep(1)

            # Get actual recommendations from comprehensive reorganizer - include IDs
            tags_data = []
            for concept in all_concepts:
                tags_data.append({
                    'id': concept.get('id', str(concept.get('_id', ''))),  # Include concept ID
                    'tag': concept['slug'],
                    'display_name': concept.get('display_name', concept['slug']),
                    'count': concept['count'],
                    'entity_type': concept.get('entity_type', 'concept'),
                    'current_parents': [str(p) for p in concept.get('parents', [])]
                })

            recommendations = await asyncio.to_thread(reorganizer.reorganize_tags, tags_data)
            debug_info = {"prompt": "Rule-based reorganization - no LLM prompt", "system_prompt": ""}

        # Final cancellation check before applying/saving the result
        if task.cancelled:
            task.end_time = datetime.now(timezone.utc)
            task.update(status="cancelled", message="Process cancelled by user")
            task._save_to_db()
            return

        # Phase 3: Format results
        task.update(status="generating", progress=85,
                   current_step="Formatting reorganization recommendations...")

        # Ensure recommendations have the expected structure
        if not isinstance(recommendations, dict):
            recommendations = {
                "merge_groups": [],
                "hierarchy": {},
                "entity_types": {},
                "stats": {
                    "total_tags": total_tags,
                    "unique_concepts": 0,
                    "merge_groups": 0,
                    "hierarchy_levels": 0
                }
            }

        # Add statistics
        if "stats" not in recommendations:
            recommendations["stats"] = {
                "total_tags": total_tags,
                "unique_concepts": len(set().union(*[set(g["tags"]) for g in recommendations.get("merge_groups", [])])) if recommendations.get("merge_groups") else 0,
                "merge_groups": len(recommendations.get("merge_groups", [])),
                "hierarchy_levels": max([1] + [len(v) for v in recommendations.get("hierarchy", {}).values()]) if recommendations.get("hierarchy") else 1
            }

        task.update(progress=90, message=f"Generated {len(recommendations.get('merge_groups', []))} merge recommendations")
        await asyncio.sleep(0.5)

        task.update(progress=95, message=f"Built hierarchy with {len(recommendations.get('hierarchy', {}))} parent concepts")
        await asyncio.sleep(0.5)

        # Complete
        task.result = recommendations
        task.end_time = datetime.now(timezone.utc)
        task.update(status="completed", progress=100,
                   current_step="Reorganization complete!",
                   message=f"Successfully analyzed {total_tags} concepts (including {parent_concepts} parent categories)")

        # Final save to MongoDB with complete result
        task._save_to_db()

    except Exception as e:
        logger.error(f"Error in reorganization task {task.task_id}: {e}")
        task.error = str(e)
        task.status = "error"
        task.end_time = datetime.now(timezone.utc)
        task.update(message=f"Error: {str(e)}")

        # Save error state to MongoDB
        task._save_to_db()

@router.post("/start")
async def start_reorganization(
    background_tasks: BackgroundTasks,
    mode: str = Query("gpt5", description="Reorganization mode: 'comprehensive' or 'gpt5'"),
    model: str = Query(None, description="Model to use for AI mode: 'gemini' or 'gpt5'"),
):
    """Start an asynchronous tag reorganization task"""
    task_id = str(uuid.uuid4())
    task = ReorganizationTask(task_id, mode)

    # Store the model selection if provided
    if model:
        task.model_override = model

    active_tasks[task_id] = task

    # Start the reorganization in the background
    background_tasks.add_task(run_reorganization_async, task)

    return {
        "task_id": task_id,
        "status": "started",
        "message": f"Tag reorganization started with mode: {mode}",
        "stream_url": f"/api/tags/reorganize/stream/{task_id}"
    }

@router.get("/stream/{task_id}")
async def stream_reorganization_status(task_id: str):
    """Stream reorganization status updates using Server-Sent Events"""

    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    async def event_generator():
        task = active_tasks[task_id]
        last_update = None

        while True:
            current_state = task.to_dict()

            # Send update if state changed or every 2 seconds
            if current_state != last_update:
                yield f"data: {json.dumps(current_state)}\n\n"
                last_update = current_state

            # Check if task is complete
            if task.status in ["completed", "error", "cancelled"]:
                yield f"data: {json.dumps(current_state)}\n\n"
                # Send final event
                yield f"event: done\ndata: {json.dumps({'task_id': task_id})}\n\n"
                break

            await asyncio.sleep(1)  # Check for updates every second

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable Nginx buffering
        }
    )

@router.post("/cancel/{task_id}")
async def cancel_reorganization(task_id: str):
    """Cancel a running reorganization task"""

    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = active_tasks[task_id]

    if task.status in ["completed", "error", "cancelled"]:
        return {
            "task_id": task_id,
            "status": task.status,
            "message": f"Task already {task.status}"
        }

    task.cancelled = True
    task.update(status="cancelling", message="Cancellation requested...")

    return {
        "task_id": task_id,
        "status": "cancelling",
        "message": "Reorganization task is being cancelled"
    }

@router.get("/result/{task_id}")
async def get_reorganization_result(task_id: str):
    """Get the final result of a completed reorganization task"""

    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = active_tasks[task_id]

    if task.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Task is not completed. Current status: {task.status}"
        )

    return {
        "task_id": task_id,
        "status": "completed",
        "result": task.result,
        "duration_seconds": (task.end_time - task.start_time).total_seconds()
    }

@router.get("/history")
async def get_task_history(limit: int = 10, status: Optional[str] = None):
    """Get recent reorganization tasks from MongoDB"""

    query = {}
    if status:
        query['status'] = status

    # Get recent tasks from MongoDB
    tasks = list(tasks_collection.find(
        query,
        {'_id': 0}  # Exclude MongoDB _id field
    ).sort('created_at', DESCENDING).limit(limit))

    # Convert datetime objects to ISO strings for JSON serialization
    for task in tasks:
        for field in ['created_at', 'updated_at', 'completed_at']:
            if task.get(field) and hasattr(task[field], 'isoformat'):
                task[field] = task[field].isoformat()

    return {
        "tasks": tasks,
        "count": len(tasks),
        "total": tasks_collection.count_documents(query)
    }
