"""
Asynchronous Tag Reorganization API with Server-Sent Events (SSE)
Provides real-time updates during long-running GPT-5 reorganization process
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse
from typing import Dict, List, Optional, Generator
import json
import asyncio
import uuid
import time
from datetime import datetime, timezone
from collections import defaultdict
import logging
from pymongo import DESCENDING
from app.database.mongodb import get_database

from app.services.comprehensive_tag_reorganizer import ComprehensiveTagReorganizer
from app.services.gpt5_tag_reorganizer import GPT5TagReorganizer

logger = logging.getLogger(__name__)
router = APIRouter()

# MongoDB connection for persistent storage
mongo_db = get_database()
tasks_collection = mongo_db.tag_reorganization_tasks

# Store active reorganization tasks (for real-time updates)
active_tasks: Dict[str, Dict] = {}

class ReorganizationTask:
    def __init__(self, task_id: str, mode: str):
        self.task_id = task_id
        self.mode = mode
        self.status = "initializing"
        self.progress = 0
        self.current_step = ""
        self.messages = []
        self.start_time = datetime.now(timezone.utc)
        self.end_time = None
        self.result = None
        self.error = None
        self.cancelled = False
        self.total_steps = 0
        self.completed_steps = 0
        self.debug_prompt = ""
        self.debug_system_prompt = ""
        
        # Save initial state to MongoDB
        self._save_to_db()
        
    def _save_to_db(self):
        """Save current task state to MongoDB"""
        doc = {
            'task_id': self.task_id,
            'status': self.status,
            'mode': self.mode,
            'created_at': self.start_time,
            'updated_at': datetime.now(timezone.utc),
            'completed_at': self.end_time,
            'progress': {
                'current': self.progress,
                'total': self.total_steps,
                'completed_steps': self.completed_steps,
                'current_step': self.current_step,
                'messages': [{'time': msg.get('time'), 'text': msg.get('text')} for msg in self.messages[-20:]]  # Keep last 20 messages
            },
            'result': self.result,
            'error': self.error,
            'cancelled': self.cancelled,
            'debug_info': {
                'prompt': self.debug_prompt[:1000] if self.debug_prompt else None,  # Store first 1000 chars
                'system_prompt': self.debug_system_prompt[:1000] if self.debug_system_prompt else None,
                'prompt_size': len(self.debug_prompt) if self.debug_prompt else 0,
                'system_prompt_size': len(self.debug_system_prompt) if self.debug_system_prompt else 0
            },
            'metadata': {
                'processing_time_seconds': (self.end_time - self.start_time).total_seconds() if self.end_time else None,
                'concepts_count': getattr(self, 'concepts_count', 0),
                'organized_count': getattr(self, 'organized_count', 0),
                'unorganized_count': getattr(self, 'unorganized_count', 0)
            }
        }
        
        # Upsert to MongoDB
        tasks_collection.replace_one(
            {'task_id': self.task_id},
            doc,
            upsert=True
        )
        
    def update(self, status: str = None, progress: int = None, 
               current_step: str = None, message: str = None):
        if status:
            self.status = status
        if progress is not None:
            self.progress = progress
        if current_step:
            self.current_step = current_step
        if message:
            self.messages.append({
                "time": datetime.now(timezone.utc).isoformat(),
                "text": message
            })
        
        # Save updates to MongoDB
        self._save_to_db()
    
    def to_dict(self):
        return {
            "task_id": self.task_id,
            "mode": self.mode,
            "status": self.status,
            "progress": self.progress,
            "current_step": self.current_step,
            "messages": self.messages[-10:],  # Keep last 10 messages
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "elapsed_seconds": (datetime.now(timezone.utc) - self.start_time).total_seconds() if self.start_time else 0,
            "cancelled": self.cancelled,
            "error": self.error,
            "total_steps": self.total_steps,
            "completed_steps": self.completed_steps,
            "debug_prompt": self.debug_prompt[:1000] if self.debug_prompt else "",  # First 1000 chars for preview
            "debug_prompt_full_size": len(self.debug_prompt) if self.debug_prompt else 0
        }

async def run_reorganization_async(task: ReorganizationTask, db):
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
            
            # Call the reorganizer with progress callback and get debug info
            recommendations, debug_info = await asyncio.to_thread(
                reorganizer.reorganize_tags_with_debug,
                tags_data,
                progress_callback
            )
            
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
    background_tasks.add_task(run_reorganization_async, task, db)
    
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

@router.get("/status/{task_id}")
async def get_reorganization_status(task_id: str):
    """Get the current status of a reorganization task"""
    
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = active_tasks[task_id]
    return task.to_dict()

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

@router.delete("/task/{task_id}")
async def cleanup_task(task_id: str):
    """Remove a completed or cancelled task from memory"""
    
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = active_tasks[task_id]
    
    if task.status not in ["completed", "error", "cancelled"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cleanup active task. Current status: {task.status}"
        )
    
    del active_tasks[task_id]
    
    return {
        "task_id": task_id,
        "message": "Task cleaned up successfully"
    }

@router.get("/active")
async def list_active_tasks():
    """List all active reorganization tasks"""
    
    tasks_summary = []
    for task_id, task in active_tasks.items():
        tasks_summary.append({
            "task_id": task_id,
            "mode": task.mode,
            "status": task.status,
            "progress": task.progress,
            "start_time": task.start_time.isoformat(),
            "elapsed_seconds": (datetime.now() - task.start_time).total_seconds()
        })
    
    return {
        "active_count": len(tasks_summary),
        "tasks": tasks_summary
    }

@router.get("/debug/current-concepts")
async def get_debug_concepts():
    """
    Debug endpoint to get current concept statistics and samples
    """
    from app.services.concept_only_tag_service import ConceptOnlyTagService
    
    try:
        concept_service = ConceptOnlyTagService()
        
        # Get ALL concepts including unused ones to show the true count
        all_concepts = concept_service.get_all_concepts_with_counts(include_unused=True)
        
        # Analyze the data
        stats = {
            "total_concepts": len(all_concepts),
            "organized": 0,
            "unorganized": 0,
            "auto_generated": 0,
            "manual": 0,
            "by_content_type": {},
            "sample_concepts": [],
            "unorganized_samples": [],
            "usage_distribution": {
                "unused": 0,
                "low_usage": 0,  # 1-5 uses
                "medium_usage": 0,  # 6-20 uses
                "high_usage": 0  # 20+ uses
            }
        }
        
        for concept in all_concepts:
            # Check if organized (has parents)
            parents = concept.get('parents', [])
            if parents and len(parents) > 0:
                stats["organized"] += 1
            else:
                stats["unorganized"] += 1
                if len(stats["unorganized_samples"]) < 10:
                    stats["unorganized_samples"].append({
                        "id": concept.get('id'),
                        "slug": concept.get('slug'),
                        "display_name": concept.get('display_name'),
                        "count": concept.get('count', 0),
                        "auto_generated": concept.get('auto_generated', False)
                    })
            
            # Check source
            if concept.get('auto_generated'):
                stats["auto_generated"] += 1
            else:
                stats["manual"] += 1
            
            # Track content types
            for content_type in concept.get('content_types', []):
                stats["by_content_type"][content_type] = stats["by_content_type"].get(content_type, 0) + 1
            
            # Usage distribution
            count = concept.get('count', 0)
            if count == 0:
                stats["usage_distribution"]["unused"] += 1
            elif count <= 5:
                stats["usage_distribution"]["low_usage"] += 1
            elif count <= 20:
                stats["usage_distribution"]["medium_usage"] += 1
            else:
                stats["usage_distribution"]["high_usage"] += 1
            
            # Get samples
            if len(stats["sample_concepts"]) < 5:
                stats["sample_concepts"].append({
                    "id": concept.get('id'),
                    "slug": concept.get('slug'),
                    "display_name": concept.get('display_name'),
                    "parents": concept.get('parents', []),
                    "count": concept.get('count', 0)
                })
        
        logger.info(f"[DEBUG] Concept stats: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Error in debug concepts endpoint: {e}")
        return {"error": str(e)}

@router.get("/debug/test-gpt5-config")
async def test_gpt5_configuration():
    """
    Debug endpoint to test GPT-5 configuration and readiness
    """
    import json
    import os
    
    result = {
        "llm_config": {},
        "prompts_config": {},
        "environment": {},
        "test_init": {},
        "sample_input": {}
    }
    
    # Check LLM config
    try:
        with open('llm.json', 'r') as f:
            llm_config = json.load(f)
            if 'tag_reorganization' in llm_config.get('models', {}):
                result['llm_config'] = {
                    "found": True,
                    "model": llm_config['models']['tag_reorganization'].get('model'),
                    "max_tokens": llm_config['models']['tag_reorganization'].get('max_tokens'),
                    "temperature": llm_config['models']['tag_reorganization'].get('temperature')
                }
            else:
                # Try other GPT-5 configurations
                for key in llm_config.get('models', {}):
                    if 'gpt-5' in llm_config['models'][key].get('model', '').lower():
                        result['llm_config'] = {
                            "found": True,
                            "using_key": key,
                            "model": llm_config['models'][key].get('model'),
                            "max_tokens": llm_config['models'][key].get('max_tokens'),
                            "temperature": llm_config['models'][key].get('temperature')
                        }
                        break
                else:
                    result['llm_config'] = {"found": False, "error": "No GPT-5 configuration found"}
    except Exception as e:
        result['llm_config'] = {"error": str(e)}
    
    # Check prompts config
    try:
        with open('prompts_config.json', 'r') as f:
            prompts = json.load(f)
            if 'tag_reorganization' in prompts:
                result['prompts_config'] = {
                    "found": True,
                    "has_system": bool(prompts['tag_reorganization'].get('system')),
                    "has_user_template": bool(prompts['tag_reorganization'].get('user_template')),
                    "system_length": len(prompts['tag_reorganization'].get('system', '')),
                    "template_length": len(prompts['tag_reorganization'].get('user_template', ''))
                }
            else:
                result['prompts_config'] = {"found": False, "error": "tag_reorganization not found"}
    except Exception as e:
        result['prompts_config'] = {"error": str(e)}
    
    # Check environment
    result['environment'] = {
        "OPENAI_API_KEY": bool(os.getenv('OPENAI_API_KEY')),
        "ANTHROPIC_API_KEY": bool(os.getenv('ANTHROPIC_API_KEY')),
        "GEMINI_API_KEY": bool(os.getenv('GEMINI_API_KEY')),
        "top_level_json": os.path.exists('top_level.json') or os.path.exists('../top_level.json')
    }
    
    # Test initialization
    try:
        from app.services.gpt5_tag_reorganizer import GPT5TagReorganizer
        reorganizer = GPT5TagReorganizer()
        result['test_init'] = {
            "success": True,
            "model": reorganizer.model_config.get('model'),
            "max_tokens": reorganizer.model_config.get('max_tokens'),
            "temperature": reorganizer.model_config.get('temperature'),
            "top_level_loaded": bool(reorganizer.top_level_json and reorganizer.top_level_json != "{}")
        }
        
        # Test with sample input
        from app.services.concept_only_tag_service import ConceptOnlyTagService
        concept_service = ConceptOnlyTagService()
        sample_concepts = concept_service.get_all_concepts_with_counts()[:3]
        
        if sample_concepts:
            sample_input = []
            for concept in sample_concepts:
                sample_input.append({
                    'id': concept.get('id'),
                    'tag': concept.get('slug'),
                    'display_name': concept.get('display_name'),
                    'count': concept.get('count', 0)
                })
            
            result['sample_input'] = {
                "concepts_count": len(sample_concepts),
                "sample": sample_input,
                "ready": True
            }
        
    except Exception as e:
        result['test_init'] = {"success": False, "error": str(e)}
    
    logger.info(f"[DEBUG] GPT-5 config test: {result}")
    return result

@router.get("/debug/{task_id}")
async def get_debug_info(task_id: str):
    """Get debug information including full prompts for a task"""
    
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = active_tasks[task_id]
    
    return {
        "task_id": task_id,
        "debug_prompt": task.debug_prompt,
        "debug_system_prompt": task.debug_system_prompt,
        "prompt_size": len(task.debug_prompt) if task.debug_prompt else 0,
        "system_prompt_size": len(task.debug_system_prompt) if task.debug_system_prompt else 0
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
    task_doc = tasks_collection.find_one({'task_id': task_id}, {'_id': 0})
    
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
        tasks_collection.update_one(
            {'task_id': task_id},
            {'$set': {
                'status': 'interrupted', 
                'error': 'Task was interrupted by server restart',
                'updated_at': datetime.now(timezone.utc)
            }}
        )
    
    return {
        "status": "recovered",
        "task": task_doc,
        "can_apply": False
    }

@router.post("/apply-recovered/{task_id}")
async def apply_recovered_task(task_id: str):
    """Apply the results from a recovered completed task"""
    
    # Load task from MongoDB
    task_doc = tasks_collection.find_one({'task_id': task_id})
    
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
        tasks_collection.update_one(
            {'task_id': task_id},
            {'$set': {
                'metadata.applied': True,
                'metadata.applied_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc)
            }}
        )
        
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
    task_doc = tasks_collection.find_one({'task_id': task_id})
    
    if not task_doc:
        # If no task in MongoDB, check in-memory tasks
        if task_id in tasks:
            task = tasks[task_id]
            if task.status != TaskStatus.COMPLETED:
                raise HTTPException(status_code=400, detail="Task is not completed")
            result = task.result
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
            tasks_collection.update_one(
                {'task_id': task_id},
                {'$set': {
                    'metadata.applied': True,
                    'metadata.applied_at': datetime.now(timezone.utc),
                    'updated_at': datetime.now(timezone.utc)
                }}
            )
        
        return {
            "success": True,
            "message": "Reorganization results applied successfully",
            "stats": apply_result.get('stats', {})
        }
        
    except Exception as e:
        logger.error(f"Failed to apply task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
