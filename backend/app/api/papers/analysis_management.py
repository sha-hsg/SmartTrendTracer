"""
Paper analysis management routes: free-form analyses, updates, and deletions.

Handles CRUD for free-form (custom-prompt) analyses, content updates for
generated analyses, and deletion of individual or all analyses.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from bson import ObjectId
from fastapi import APIRouter, Body, HTTPException

from .utils import db, logger, find_paper_by_id

router = APIRouter()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _find_paper(paper_id: str):
    """Look up a paper by ObjectId or legacy SQLite id."""
    try:
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except Exception:
        paper = None
    return paper


# ---------------------------------------------------------------------------
# Free-form analysis routes
# ---------------------------------------------------------------------------

@router.post("/{paper_id}/analyses/free")
async def create_free_analysis(
    paper_id: str,
    data: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """Create a free-form analysis with custom user prompt"""
    prompt = data.get('prompt')
    regenerate = data.get('regenerate', False)
    model = data.get('model')  # Get model from frontend

    paper = _find_paper(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Import required modules
    from app.services.llm_service import LLMService

    # Get paper content
    paper_content = paper.get('content', '')
    if not paper_content or len(paper_content) < 100:
        paper_content = f"Title: {paper.get('title', '')}\n\nAbstract: {paper.get('abstract', '')}"

    # Generate a unique ID for this free analysis
    analysis_id = f"free_{uuid.uuid4().hex[:8]}"

    # Check if this exact prompt already exists and not regenerating
    free_analyses = paper.get('free_analyses', [])
    existing = next((a for a in free_analyses if a.get('prompt') == prompt), None)

    if existing and not regenerate:
        return existing

    # Load LLM configuration
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    with open(os.path.join(backend_dir, 'llm.json'), 'r') as f:
        llm_config = json.load(f)

    # Use the chat_general model for free-form analysis
    model_config = llm_config.get('models', {}).get('chat_general', {})

    # Prefer frontend-provided model, fall back to config
    model_to_use = model if model else model_config.get('model', 'gemini/gemini-2.5-pro')

    # Map frontend model selections to correct LiteLLM model names
    # Include both key formats (with and without gemini/ prefix) for compatibility
    model_mapping = {
        # Claude models
        "claude-opus-4-5-20251101": "claude-opus-4-5-20251101",
        "claude-opus-4.5": "claude-opus-4-5-20251101",
        "claude-3.5-sonnet": "claude-sonnet-4-20250514",
        "claude-sonnet-4": "claude-sonnet-4-20250514",
        # Gemini 3.x models - CORRECT mappings (both key formats)
        "gemini-3.1-pro-preview": "gemini/gemini-3.1-pro-preview",
        "gemini/gemini-3.1-pro-preview": "gemini/gemini-3.1-pro-preview",
        "gemini-3.5-flash": "gemini/gemini-3.5-flash",
        "gemini/gemini-3.5-flash": "gemini/gemini-3.5-flash",
        "gemini-3.1-flash-lite": "gemini/gemini-3.1-flash-lite",
        "gemini/gemini-3.1-flash-lite": "gemini/gemini-3.1-flash-lite",
        # Gemini 2.5 models (both key formats)
        "gemini-2.5-pro": "gemini/gemini-2.5-pro",
        "gemini/gemini-2.5-pro": "gemini/gemini-2.5-pro",
        "gemini-2.5-flash": "gemini/gemini-2.5-flash",
        "gemini/gemini-2.5-flash": "gemini/gemini-2.5-flash",
        # GPT models
        "gpt-5.2-thinking": "openai/gpt-5.2",
        "gpt-5.2-pro": "openai/gpt-5.1",
        "gpt-5.2-codex": "openai/gpt-5-nano",
    }
    if model_to_use in model_mapping:
        logger.info(f"Mapped model {model_to_use} → {model_mapping[model_to_use]}")
        model_to_use = model_mapping[model_to_use]
    elif model:
        # User provided a model that's not in mapping - log for debugging
        logger.info(f"Using model directly (no mapping needed): {model_to_use}")

    # Initialize LLM service
    llm_service = LLMService()

    # Create the full prompt with system context
    system_context = "You are an expert at analyzing research papers. Provide detailed, insightful responses to user questions about the paper."
    full_prompt = f"{system_context}\n\nUser question: {prompt}\n\nPaper content:\n{paper_content}"

    # Generate the analysis
    try:
        response = llm_service.generate_completion(
            prompt=full_prompt,
            model=model_to_use,
            max_tokens=model_config.get('max_tokens', 8000),
            temperature=model_config.get('temperature', 0.5)
        )

        # Create the analysis object
        analysis = {
            "id": analysis_id,
            "prompt": prompt,
            "content": response,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "model": model_to_use
        }

        # Save atomically to avoid the same race condition that was fixed for
        # the `analyses` array: $pull the stale copy on regenerate, then $push.
        if existing and regenerate:
            db.papers.update_one(
                {'_id': paper['_id']},
                {'$pull': {'free_analyses': {'prompt': prompt}}}
            )

        db.papers.update_one(
            {'_id': paper['_id']},
            {'$push': {'free_analyses': analysis}}
        )

        return analysis

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate analysis: {str(e)}")

@router.get("/{paper_id}/analyses/free")
async def get_free_analyses(paper_id: str) -> Dict[str, Any]:
    """Get all free-form analyses for a paper"""

    paper = _find_paper(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Get free analyses and convert ObjectIds for safety
    free_analyses = paper.get('free_analyses', [])

    # Convert any ObjectIds to strings in analyses
    for analysis in free_analyses:
        if isinstance(analysis, dict):
            for key, value in analysis.items():
                if isinstance(value, ObjectId):
                    analysis[key] = str(value)

    return {"analyses": free_analyses}

@router.put("/{paper_id}/analyses/free/{analysis_id}")
async def update_free_analysis(
    paper_id: str,
    analysis_id: str,
    content: str = Body(..., embed=True)
) -> Dict[str, Any]:
    """Update the content of a free-form analysis"""

    paper = _find_paper(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Find and update the analysis
    free_analyses = paper.get('free_analyses', [])
    updated = False

    for analysis in free_analyses:
        if analysis.get('id') == analysis_id:
            analysis['content'] = content
            analysis['updated_at'] = datetime.now(timezone.utc).isoformat()
            updated = True
            break

    if not updated:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Save to database
    db.papers.update_one(
        {'_id': paper['_id']},
        {'$set': {'free_analyses': free_analyses}}
    )

    return {"success": True, "message": "Analysis updated"}

@router.delete("/{paper_id}/analyses/free/{analysis_id}")
async def delete_free_analysis(paper_id: str, analysis_id: str) -> Dict[str, Any]:
    """Delete a free-form analysis"""

    paper = _find_paper(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Filter out the analysis to delete
    free_analyses = paper.get('free_analyses', [])
    filtered_analyses = [a for a in free_analyses if a.get('id') != analysis_id]

    if len(filtered_analyses) == len(free_analyses):
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Save to database
    db.papers.update_one(
        {'_id': paper['_id']},
        {'$set': {'free_analyses': filtered_analyses}}
    )

    return {"success": True, "message": "Analysis deleted"}


# ---------------------------------------------------------------------------
# Update / delete generated (structured) analyses
# ---------------------------------------------------------------------------

@router.put("/{paper_id}/analyses/generated/{analysis_type}")
async def update_generated_analysis(
    paper_id: str,
    analysis_type: str,
    data: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """Update the content of a generated analysis (like mollick_summary)"""

    content = data.get('content', '')

    paper = _find_paper(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Get existing analyses - handle both dict and list formats
    analyses = paper.get('analyses', {})
    updated = False

    if isinstance(analyses, dict):
        # Dict format - used by the generation endpoint
        if analysis_type not in analyses:
            raise HTTPException(status_code=404, detail=f"Analysis type '{analysis_type}' not found")

        # Update the content while preserving other fields
        analyses[analysis_type]['content'] = content
        analyses[analysis_type]['updated_at'] = datetime.now(timezone.utc).isoformat()
        updated = True

    elif isinstance(analyses, list):
        # List format - handle legacy format
        for analysis in analyses:
            # Check both 'type' and 'analysis_type' fields
            if (analysis.get('type') == analysis_type or
                analysis.get('analysis_type') == analysis_type):
                analysis['content'] = content
                analysis['updated_at'] = datetime.now(timezone.utc).isoformat()
                updated = True
                break

        if not updated:
            raise HTTPException(status_code=404, detail=f"Analysis type '{analysis_type}' not found")
    else:
        raise HTTPException(status_code=400, detail="Invalid analyses format")

    # Save to database
    db.papers.update_one(
        {'_id': paper['_id']},
        {'$set': {'analyses': analyses}}
    )

    return {"success": True, "message": f"Analysis '{analysis_type}' updated"}

@router.delete("/{paper_id}/analyses")
def delete_all_analyses(paper_id: str) -> Dict[str, Any]:
    """Delete all saved analyses for a paper"""
    paper = find_paper_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    count = len(paper.get('analyses', []))
    db.papers.update_one(
        {'_id': paper['_id']},
        {'$set': {'analyses': []}}
    )

    return {"message": f"Deleted {count} analyses", "deleted_count": count}

@router.delete("/{paper_id}/analyses/{analysis_type}")
def delete_analysis(paper_id: str, analysis_type: str) -> Dict[str, str]:
    """Delete a saved analysis"""

    paper = _find_paper(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Remove analysis from paper atomically - check both type and analysis_type fields
    db.papers.update_one(
        {'_id': paper['_id']},
        {'$pull': {'analyses': {'$or': [
            {'type': analysis_type},
            {'analysis_type': analysis_type}
        ]}}}
    )

    return {"message": "Analysis deleted successfully"}
