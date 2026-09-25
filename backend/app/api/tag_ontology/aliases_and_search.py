"""
Alias management and concept search endpoints.
Add/delete aliases, find concept by name.
"""
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timezone
from bson import ObjectId
import logging

from .utils import (
    concept_id_variants,
)
from app.repositories.tag_ontology_utils_queries import find_concept_by_any_id
from app.repositories import tag_ontology_aliases_and_search_queries as queries

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/concept/{concept_id}/alias")
def add_alias(concept_id: str, alias_data: dict):
    """Add an alias to a concept"""

    # Check if concept exists (custom id or ObjectId string)
    concept = find_concept_by_any_id(concept_id)
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")

    # Create alias - store concept_id as ObjectId (consistent with existing data)
    alias = {
        "alias_text": alias_data.get("alias_text"),
        "concept_id": concept["_id"],
        "alias_type": alias_data.get("alias_type", "synonym"),
        "confidence": alias_data.get("confidence", 1.0),
        "created_at": datetime.now(timezone.utc)
    }

    # Insert alias
    try:
        queries.tag_aliases_v2_insert_one__add_alias(alias)
        return {"message": "Alias added successfully"}
    except Exception as e:
        if "duplicate key" in str(e):
            raise HTTPException(status_code=400, detail="Alias already exists for this concept")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/alias/{alias_text}")
def delete_alias(alias_text: str, concept_id: str = Query(...)):
    """Delete an alias"""

    # Aliases store concept_id as ObjectId (legacy rows may hold strings) -
    # resolve the passed id to all representations
    concept_ids = [concept_id]
    if ObjectId.is_valid(concept_id):
        concept_ids.append(ObjectId(concept_id))
    concept = find_concept_by_any_id(concept_id)
    if concept:
        for variant in concept_id_variants(concept):
            if variant not in concept_ids:
                concept_ids.append(variant)

    result = queries.tag_aliases_v2_delete_one__delete_alias(alias_text, concept_ids)

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Alias not found")

    return {"message": "Alias deleted successfully"}


@router.get("/find-by-name/{tag_name}")
async def find_concept_by_name(tag_name: str):
    """Find a concept by its name, slug, or display_name"""
    try:

        # Try to find by slug, name, or display_name
        concept = queries.tag_concepts_v2_find_one__find_concept_by_name(tag_name)

        if not concept:
            # Try to find in aliases (field is alias_text, not alias)
            alias = queries.tag_aliases_v2_find_one__find_concept_by_name(tag_name)
            if alias:
                cid = alias["concept_id"]
                if isinstance(cid, ObjectId):
                    concept = queries.tag_concepts_v2_find_one__find_concept_by_name_2(cid)
                else:
                    # Legacy rows may store the custom "c_..." id as string
                    concept = find_concept_by_any_id(str(cid))

        if not concept:
            raise HTTPException(status_code=404, detail=f"Concept not found for tag: {tag_name}")

        # Convert ObjectId to string
        concept["_id"] = str(concept["_id"])
        if concept.get("parents"):
            concept["parents"] = [str(p) for p in concept["parents"]]
        if concept.get("children"):
            concept["children"] = [str(c) for c in concept["children"]]

        return concept
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding concept by name: {e}")
        raise HTTPException(status_code=500, detail=str(e))
