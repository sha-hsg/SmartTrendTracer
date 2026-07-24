"""
Paper concept and tag route handlers.

Covers: add/remove concepts, add/remove tags (legacy endpoints).
"""

import logging
import re
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query

from .utils import (
    db,
    concept_service,
    find_paper_by_id,
)

logger = logging.getLogger("app.api.papers")

router = APIRouter()


@router.post("/{paper_id}/apply-concepts")
def apply_concepts_to_paper(paper_id: str, concepts: List[Dict[str, str]]):
    """Batch-apply selected concepts to a paper.
    Expects array of objects with display_name and slug."""
    paper = find_paper_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    success_count = 0
    fail_count = 0

    for concept_data in concepts:
        try:
            text = concept_data.get('display_name', concept_data.get('tag', ''))
            if not text:
                fail_count += 1
                continue
            success, concept_id = concept_service.add_tag(
                content_type='paper',
                content_id=str(paper['_id']),
                text=text,
                preserve_display_name=True
            )
            if success:
                success_count += 1
                db.papers.update_one(
                    {'_id': paper['_id']},
                    {'$addToSet': {'concept_ids': concept_id}}
                )
            else:
                fail_count += 1
        except Exception as e:
            logger.error(f"Error applying concept {concept_data}: {e}")
            fail_count += 1

    return {
        "success_count": success_count,
        "fail_count": fail_count,
        "total_applied": success_count,
        "message": f"Applied {success_count} concepts to paper"
    }


@router.post("/{paper_id}/concepts")
def add_concept_to_paper(
    paper_id: str,
    text: str = Query(..., description="Text to create/find concept from")
) -> Dict[str, Any]:
    """Add a concept to a paper"""
    paper = find_paper_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Add concept using the service
    success, concept_id = concept_service.add_tag('paper', str(paper['_id']), text)

    if not success:
        raise HTTPException(status_code=400, detail="Failed to add concept")

    # Update paper's concept_ids in MongoDB
    db.papers.update_one(
        {'_id': paper['_id']},
        {'$addToSet': {'concept_ids': concept_id}}
    )

    # Get concept details
    concept = concept_service.get_concept_by_id(concept_id)

    return {
        "message": "Concept added successfully",
        "concept": {
            "concept_id": concept_id,
            "slug": concept.get('slug', ''),
            "display_name": concept.get('display_name', '')
        }
    }

@router.delete("/{paper_id}/concepts/{concept_id}")
def remove_concept_from_paper(paper_id: str, concept_id: str) -> Dict[str, str]:
    """Remove a concept from a paper"""
    paper = find_paper_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Remove from concept service
    success = concept_service.remove_tag('paper', str(paper['_id']), concept_id)

    if not success:
        raise HTTPException(status_code=404, detail="Concept not found on this paper")

    # Update paper's concept_ids in MongoDB
    db.papers.update_one(
        {'_id': paper['_id']},
        {'$pull': {'concept_ids': concept_id}}
    )

    return {"message": "Concept removed successfully"}

@router.post("/{paper_id}/tags")
def add_tags_to_paper(paper_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """Add tags to a paper (legacy endpoint, redirects to concepts)"""

    # Extract tag from body
    tag = body.get('tag', '')
    if not tag:
        raise HTTPException(status_code=400, detail="Tag is required")

    # Redirect to concepts endpoint
    return add_concept_to_paper(paper_id, text=tag)

@router.delete("/{paper_id}/tags/{tag}")
def remove_tag_from_paper(paper_id: str, tag: str) -> Dict[str, str]:
    """Remove a tag from a paper (legacy endpoint).

    Resolves the tag text to a concept (slug/alias via the concept service,
    then case-insensitive display name) and delegates to the concept removal.
    """
    paper = find_paper_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Resolve tag text to a concept: slug/alias first, then display name
    concept = concept_service._find_concept_by_slug_or_alias(tag)
    if not concept:
        concept = db.tag_concepts_v2.find_one({
            'display_name': {'$regex': f'^{re.escape(tag)}$', '$options': 'i'}
        })

    if not concept:
        raise HTTPException(status_code=404, detail=f"Concept '{tag}' not found")

    # Delegate to the existing concept removal logic
    return remove_concept_from_paper(paper_id, str(concept['_id']))
