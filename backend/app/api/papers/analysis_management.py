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

from .utils import db
from app.repositories import papers_analysis_management as repo
from app.repositories.papers_analysis_management import _find_paper  # noqa: F401 (moved)

router = APIRouter()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------



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

    from app.services.llm_manager import get_llm_manager

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

    llm = get_llm_manager()
    prompt_config = llm.get_prompt('paper_free_analysis')
    user_prompt = prompt_config['user_template'].format(question=prompt, paper_content=paper_content)
    # Frontend model choice -> routable model name (central MIGRATION_MAP);
    # unknown/None falls back to the chat_general route
    model_to_use = llm.resolve_model_override(model)

    # Generate the analysis
    try:
        response = llm.complete_text(
            'chat_general',
            user_prompt,
            system_prompt=prompt_config.get('system'),
            model_override=model_to_use,
        )
        model_to_use = model_to_use or llm._resolve_actual_model('chat_general')

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
    return repo.update_free_analysis(paper_id=paper_id, analysis_id=analysis_id, content=content)

@router.delete("/{paper_id}/analyses/free/{analysis_id}")
async def delete_free_analysis(paper_id: str, analysis_id: str) -> Dict[str, Any]:
    """Delete a free-form analysis"""
    return repo.delete_free_analysis(paper_id=paper_id, analysis_id=analysis_id)


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
    return repo.update_generated_analysis(paper_id=paper_id, analysis_type=analysis_type, data=data)

@router.delete("/{paper_id}/analyses")
def delete_all_analyses(paper_id: str) -> Dict[str, Any]:
    """Delete all saved analyses for a paper"""
    return repo.delete_all_analyses(paper_id=paper_id)

@router.delete("/{paper_id}/analyses/{analysis_type}")
def delete_analysis(paper_id: str, analysis_type: str) -> Dict[str, str]:
    """Delete a saved analysis"""
    return repo.delete_analysis(paper_id=paper_id, analysis_type=analysis_type)
