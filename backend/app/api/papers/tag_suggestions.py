"""
AI-powered tag/concept suggestion endpoints for papers.

Split from entities.py to keep modules under 600 LOC.
"""

from fastapi import APIRouter, HTTPException, Body
from typing import Optional, Dict, Any
from bson import ObjectId

from .utils import db, concept_service, logger

router = APIRouter()


async def get_tag_suggestions(paper_id: str, model: Optional[str] = None) -> Dict[str, Any]:
    """Get AI-powered concept suggestions for a paper.

    Internal implementation used by the POST /{paper_id}/tags/suggest endpoint.
    """

    logger.info(f"Getting tag suggestions for paper {paper_id} with model: {model}")

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

    # Get existing concepts on this paper
    paper_id_str = str(paper['_id'])
    sqlite_id_str = str(paper.get('old_sqlite_id', ''))

    existing_tags = list(db.tag_instances.find({
        'content_type': 'paper',
        '$or': [
            {'content_id': paper_id_str},
            {'content_id': sqlite_id_str}
        ]
    }))

    existing_concept_ids = [ti['concept_id'] for ti in existing_tags if ti.get('concept_id')]

    # Get concept display names for already tagged in a single batch query (avoids N+1)
    concepts_lookup = concept_service.get_concepts_by_ids(existing_concept_ids)
    already_tagged = []
    for cid in existing_concept_ids:
        concept = concepts_lookup.get(str(cid))
        if concept:
            already_tagged.append(concept.get('display_name', ''))

    # Find similar existing concepts based on title/abstract
    existing_suggestions = []
    all_concepts = concept_service.get_all_concepts_with_counts(content_type='paper')

    # Simple text matching for suggestions
    paper_text = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()

    for concept in all_concepts[:30]:  # Check top 30 concepts
        if concept['id'] not in existing_concept_ids:
            # Check if concept name appears in paper text
            if concept['display_name'].lower() in paper_text or \
               any(alias.lower() in paper_text for alias in concept.get('aliases', [])):
                existing_suggestions.append({
                    'concept_id': concept['id'],
                    'display_name': concept['display_name'],
                    'slug': concept['slug'],
                    'usage_count': concept.get('usage_count', 0)
                })
                if len(existing_suggestions) >= 5:
                    break

    # Require processed content - no silent fallback to title+abstract.
    # Must be raised BEFORE the LLM try/except below, otherwise the broad
    # except would swallow the 400 and return 200 with empty suggestions.
    if not paper.get('content') and not paper.get('markdown_content'):
        raise HTTPException(status_code=400, detail="Paper must be processed first — no content available")

    # Generate new suggestions using LLM
    new_suggestions = []
    try:
        from app.services.llm_manager import get_llm_manager
        llm_manager = get_llm_manager()

        # Prepare FULL paper text for LLM - send everything!
        paper_text_for_llm = f"Title: {paper.get('title', '')}\n\n"
        paper_text_for_llm += f"Abstract: {paper.get('abstract', '')}\n\n"

        full_content = paper.get('content') or paper.get('markdown_content')
        paper_text_for_llm += f"Full Paper Content:\n{full_content}"
        logger.info(f"Sending full paper content to LLM: {len(full_content)} characters")

        # Get author names
        authors = paper.get('authors', '')
        if isinstance(authors, list):
            authors = ', '.join(authors)

        # Load prompts configuration
        import json
        import os
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        with open(os.path.join(backend_dir, 'prompts_config.json'), 'r') as f:
            prompts_config = json.load(f)

        # Get paper tag suggestion prompt
        tag_config = prompts_config.get('paper_tag_suggestion', {})
        system_prompt = tag_config.get('system', '')
        user_template = tag_config.get('user_template', '')
        max_tags = tag_config.get('max_tags', 30)

        # Replace placeholders
        user_prompt = user_template.replace('{author}', authors).replace('{text}', paper_text_for_llm).replace('{max_tags}', str(max_tags))

        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

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

        # Prepare override parameters if user selected a model
        override_params = None
        if model and model in model_mapping:
            litellm_model = model_mapping[model]
            override_params = {'model': litellm_model}
            logger.info(f"Using user-selected model: {model} → {litellm_model}")
        elif model:
            # User selected a model but it's not in mapping - LOG WARNING
            logger.warning(f"Model '{model}' not found in model_mapping, falling back to task default")

        # Call LLM
        task_type = 'paper_tag_suggestion_gpt5' if not model else 'paper_tag_suggestion_deep'
        llm_response = await llm_manager.completion(
            task_type=task_type,
            messages=messages,
            user_id='default',
            override_params=override_params
        )

        result = llm_response.choices[0].message.content
        model_used = llm_response.model

        logger.info(f"LLM response from {model_used}: {len(result)} chars")
        logger.debug(f"Raw LLM response: {result[:500]}")

        # Parse JSON response - handle cases where LLM returns text before JSON
        import json
        import re
        try:
            llm_tags = json.loads(result)
            if not isinstance(llm_tags, list):
                logger.error(f"LLM returned non-list response: {type(llm_tags)}")
                llm_tags = []
        except json.JSONDecodeError as je:
            # Try to extract JSON array from response text
            logger.warning(f"Direct JSON parse failed, attempting extraction: {je}")
            json_match = re.search(r'\[[\s\S]*\]', result)
            if json_match:
                try:
                    llm_tags = json.loads(json_match.group())
                    logger.info(f"Successfully extracted JSON array from response")
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse extracted JSON: {result[:200]}")
                    llm_tags = []
            else:
                logger.error(f"No JSON array found in response: {result[:200]}")
                llm_tags = []

        # Filter out tags that already exist or are already tagged
        already_tagged_names = {t.lower() for t in already_tagged}
        existing_suggestion_names = {s['display_name'].lower() for s in existing_suggestions}

        for tag in llm_tags:
            tag_lower = tag.lower()
            if tag_lower not in already_tagged_names and tag_lower not in existing_suggestion_names:
                # It's a genuinely new suggestion from LLM
                new_suggestions.append({
                    'display_name': tag,
                    'slug': tag.lower().replace(' ', '-'),
                    'is_new': True
                })

        logger.info(f"Generated {len(new_suggestions)} new tag suggestions for paper {paper_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate LLM tag suggestions: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Continue without LLM suggestions

    return {
        "existing_suggestions": existing_suggestions,
        "new_suggestions": new_suggestions,
        "already_tagged": already_tagged
    }

@router.post("/{paper_id}/tags/suggest")
async def suggest_tags_for_paper(paper_id: str, request: Dict[str, Any] = Body({})) -> Dict[str, Any]:
    """Get AI-powered concept suggestions for a paper (POST endpoint with model selection)"""
    # Extract model from request body
    model = request.get('model', None)
    logger.info(f"Tag suggestion requested for paper {paper_id} with model: {model}")
    return await get_tag_suggestions(paper_id, model=model)
