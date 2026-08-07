"""
Paper analysis routes: generate, retrieve, update, and delete LLM-powered analyses.

Includes structured (prompt-config-driven) analysis endpoints.
"""

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from bson import ObjectId
from fastapi import APIRouter, Body, HTTPException

from .utils import db, logger

router = APIRouter()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/{paper_id}/analyses/available")
def get_available_analyses(paper_id: str) -> Dict[str, Any]:  # noqa: ARG001
    """Get available analysis types for a paper - dynamically loaded from prompts_config.json"""
    # Note: paper_id is part of the route but analysis types are global
    import json
    import os

    # Load analysis types from prompts_config.json
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    with open(os.path.join(backend_dir, 'prompts_config.json'), 'r') as f:
        prompts_config = json.load(f)

    paper_analyses = prompts_config.get('paper_analyses', {})

    # Build available analyses list from prompts_config
    available_analyses = []

    # Icon mapping for different categories
    icon_map = {
        'summaries': '\U0001f4dd',
        'analysis': '\U0001f4ad',
        'review': '\U0001f4cb',
        'reference': '\U0001f4d6'
    }

    for analysis_id, config in paper_analyses.items():
        category = config.get('category', 'analysis')
        available_analyses.append({
            "id": analysis_id,
            "name": config.get('name', analysis_id.replace('_', ' ').title()),
            "description": config.get('description', ''),
            "icon": icon_map.get(category, '\U0001f4ca'),
            "category": category
        })

    # Sort analyses by category and name for better organization
    available_analyses.sort(key=lambda x: (x.get('category', ''), x.get('name', '')))

    # Group analyses by category for frontend
    by_category = {}
    for analysis in available_analyses:
        category = analysis.get('category', 'analysis')
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(analysis)

    return {"analyses": available_analyses, "by_category": by_category}

@router.get("/{paper_id}/analyses/saved")
def get_saved_analyses(paper_id: str) -> Dict[str, Any]:
    """Get saved analyses for a paper from MongoDB"""

    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except Exception:
        paper = None

    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Get analyses from the paper document
    analyses = paper.get('analyses', [])

    # Convert array to object keyed by analysis type (frontend expects this format)
    analyses_dict = {}
    for analysis in analyses:
        # Get the analysis type (handle both field names)
        analysis_type = analysis.get('type') or analysis.get('analysis_type')
        if not analysis_type:
            continue

        # Format the analysis for frontend
        analyses_dict[analysis_type] = {
            "success": True,
            "content": analysis.get('content', ''),
            "model": analysis.get('model_used') or analysis.get('model', 'gpt-4o-mini'),
            "created_at": analysis.get('created_at') or analysis.get('generated_at'),
            "metadata": {
                "word_count": analysis.get('word_count'),
                "confidence_score": analysis.get('confidence_score'),
                "version": analysis.get('version')
            }
        }

    return {"analyses": analyses_dict}

@router.post("/{paper_id}/analyses")
async def create_analysis(paper_id: str, analysis_type: str = Body(...), regenerate: bool = Body(False), model: Optional[str] = None) -> Dict[str, Any]:
    """Create a new analysis for a paper using prompts_config.json and llm.json"""

    try:
        # Try to convert to ObjectId if it's a valid format
        if len(paper_id) == 24:
            paper = db.papers.find_one({'_id': ObjectId(paper_id)})
        else:
            # Try old SQLite ID
            paper = db.papers.find_one({'old_sqlite_id': int(paper_id)})
    except Exception:
        paper = None

    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Check if analysis already exists and not regenerating
    existing_analyses = paper.get('analyses', [])
    existing = next((a for a in existing_analyses if (a.get('type') == analysis_type or a.get('analysis_type') == analysis_type)), None)

    if existing and not regenerate:
        return existing

    # Import required modules
    from app.services.llm_manager import get_llm_manager
    import json
    import os

    # Load configurations
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

    with open(os.path.join(backend_dir, 'prompts_config.json'), 'r') as f:
        prompts_config = json.load(f)

    # Get paper content - use full content for better analysis
    paper_content = paper.get('content', '')
    if not paper_content or len(paper_content) < 100:
        raise HTTPException(
            status_code=400,
            detail="No extracted content available. Please process the PDF with Marker or MinerU first before generating analyses."
        )

    # Get the appropriate prompt configuration from prompts_config.json
    paper_analyses = prompts_config.get('paper_analyses', {})

    # Get the analysis configuration directly from prompts_config
    # No mapping needed - analysis_type should match the key in prompts_config.json
    analysis_config = paper_analyses.get(analysis_type)

    if not analysis_config:
        # Fallback configuration
        analysis_config = {
            'system': 'You are an expert at analyzing research papers.',
            'user_template': 'Analyze this paper:\n\n{paper_content}'
        }

    # Prepare prompts
    system_prompt = analysis_config.get('system', '')
    user_template = analysis_config.get('user_template', '')
    user_prompt = user_template.replace('{paper_content}', paper_content)

    # Initialize LLM manager (uses LiteLLM)
    llm_manager = get_llm_manager()

    # Build messages in OpenAI format
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})

    # Determine task type for LiteLLM routing
    if analysis_type in ['review', 'sas_review', 'switt']:
        task_type = 'paper_analysis_deep'
    else:
        task_type = 'paper_analysis'

    # Map frontend model selections to LiteLLM Router model_name (from litellm_config.yaml)
    # IMPORTANT: Values must match model_name in litellm_config.yaml, NOT the full litellm_params.model
    model_mapping = {
        # GPT models (model_name matches frontend value)
        "gpt-5": "gpt-5-2025-08-07",
        "gpt-5.1": "gpt-5.1",
        "gpt-5-mini": "gpt-5-mini",
        "gpt-5-nano": "gpt-5-nano",
        "gpt-4o": "gpt-4o",
        "gpt-4o-mini": "gpt-4o-mini",
        # Claude models
        "claude-opus-5": "claude-opus-5",
        "claude-opus-4.5": "claude-opus-5",
        "claude-sonnet-4.5": "claude-sonnet-4-5-20250929",
        "claude-opus-4.1": "claude-opus-5",
        "claude-haiku-4.5": "claude-haiku-4-5-20251001",
        "claude-3.5-sonnet": "claude-sonnet-5",
        # Gemini 3.x models - map to model_name (without gemini/ prefix)
        "gemini-3.1-pro-preview": "gemini-3.1-pro-preview",
        "gemini/gemini-3.1-pro-preview": "gemini-3.1-pro-preview",
        "gemini-3.5-flash": "gemini-3.5-flash",
        "gemini/gemini-3.5-flash": "gemini-3.5-flash",
        "gemini-3.1-flash-lite": "gemini-3.1-flash-lite",
        "gemini/gemini-3.1-flash-lite": "gemini-3.1-flash-lite",
        # Gemini 2.5 models - map to model_name (without gemini/ prefix)
        "gemini-2.5-pro": "gemini-2.5-pro",
        "gemini/gemini-2.5-pro": "gemini-2.5-pro",
        "gemini-2.5-flash": "gemini-2.5-flash",
        "gemini/gemini-2.5-flash": "gemini-2.5-flash",
        "gemini-2.5-flash-lite": "gemini-2.5-flash-lite",
        "gemini/gemini-2.5-flash-lite": "gemini-2.5-flash-lite",
    }

    # Prepare override parameters if user selected a specific model
    override_params = None
    if model and model in model_mapping:
        litellm_model = model_mapping[model]
        override_params = {'model': litellm_model}
        logger.info(f"User selected model: {model} → Router model_name: {litellm_model}")
    elif model:
        # User selected a model but it's not in mapping - LOG WARNING
        logger.warning(f"Model '{model}' not found in model_mapping, falling back to task default")

    # Generate the analysis using LiteLLM manager
    # If override_params is set, it will use the user's selected model
    # Otherwise, LiteLLM uses configured routing for the task_type
    try:
        llm_response = await llm_manager.completion(
            task_type=task_type,
            messages=messages,
            user_id='default',
            override_params=override_params
        )
    except Exception as e:
        # If user's selected model fails, fall back to default routing
        if override_params:
            logger.warning(f"User's selected model failed, using default routing: {e}")
            llm_response = await llm_manager.completion(
                task_type=task_type,
                messages=messages,
                user_id='default',
                override_params=None  # Let LiteLLM use default routing
            )
        else:
            raise  # Re-raise if it wasn't a model selection issue

    result = llm_response.choices[0].message.content
    model_name = llm_response.model  # Get actual model used by LiteLLM

    # Create analysis object
    analysis = {
        "type": analysis_type,
        "analysis_type": analysis_type,  # Keep both for backwards compatibility
        "content": result,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "model": model_name,
        "model_used": model_name,
        "prompt_config": analysis_type  # Use analysis_type as the config key
        # Note: temperature and max_tokens are handled by LiteLLM config
    }

    # Update paper with new analysis using atomic operations
    # Using $push instead of $set to prevent race conditions when generating multiple analyses
    if existing and regenerate:
        # First remove the existing analysis of this type atomically
        db.papers.update_one(
            {'_id': paper['_id']},
            {'$pull': {'analyses': {'$or': [
                {'type': analysis_type},
                {'analysis_type': analysis_type}
            ]}}}
        )

    # Then push the new analysis atomically
    db.papers.update_one(
        {'_id': paper['_id']},
        {'$push': {'analyses': analysis}}
    )

    return analysis

