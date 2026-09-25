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
from app.repositories import papers_concepts as repo

logger = logging.getLogger("app.api.papers")

router = APIRouter()


@router.post("/{paper_id}/apply-concepts")
def apply_concepts_to_paper(paper_id: str, concepts: List[Dict[str, str]]):
    """Batch-apply selected concepts to a paper.
    Expects array of objects with display_name and slug."""
    return repo.apply_concepts_to_paper(paper_id=paper_id, concepts=concepts)


@router.post("/{paper_id}/concepts")
def add_concept_to_paper(
    paper_id: str,
    text: str = Query(..., description="Text to create/find concept from")
) -> Dict[str, Any]:
    """Add a concept to a paper"""
    return repo.add_concept_to_paper(paper_id=paper_id, text=text)

@router.delete("/{paper_id}/concepts/{concept_id}")
def remove_concept_from_paper(paper_id: str, concept_id: str) -> Dict[str, str]:
    """Remove a concept from a paper"""
    return repo.remove_concept_from_paper(paper_id=paper_id, concept_id=concept_id)

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
