"""
Ontology-style concept CRUD operations.
Create, update, and delete concepts using ObjectId-based lookups.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime, timezone
from bson import ObjectId
import logging

from .utils import (
    concept_id_variants,
)
from app.repositories import tag_ontology_concepts_ontology_queries as queries

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/concepts")
async def create_concept_ontology(concept_data: Dict[str, Any]):
    """Create a new concept in the ontology"""
    try:

        # Prepare concept document
        new_concept = {
            "slug": concept_data.get("slug"),
            "display_name": concept_data.get("display_name"),
            "description": concept_data.get("description", ""),
            "entity_type": concept_data.get("entity_type", "concept"),
            "parents": [],
            "children": [],
            "created_at": datetime.now(timezone.utc),
            "created_by": "user",
            "auto_generated": False,
            "verified": True,
            "usage_count": 0,
            "child_count": 0,
            "descendant_count": 0
        }

        # Add parent if specified
        if concept_data.get("parent_id"):
            try:
                parent_oid = ObjectId(concept_data["parent_id"])
                new_concept["parents"] = [parent_oid]
            except Exception:
                new_concept["parents"] = [concept_data["parent_id"]]

        # Collision-free, schema-compliant IDs: ObjectId as _id,
        # custom id derived from it ("c_" + ObjectId string)
        new_oid = ObjectId()
        new_concept["_id"] = new_oid
        new_concept["id"] = f"c_{new_oid}"

        # Insert the concept
        result = queries.tag_concepts_v2_insert_one__create_concept_ontology(new_concept)

        # Update parent's children if parent exists
        if concept_data.get("parent_id"):
            try:
                parent_oid = ObjectId(concept_data["parent_id"])
            except Exception:
                parent_oid = concept_data["parent_id"]

            queries.tag_concepts_v2_update_one__create_concept_ontology(parent_oid, result)

        return {"success": True, "id": str(result.inserted_id), "concept_id": new_concept["id"]}
    except Exception as e:
        logger.error(f"Error creating concept: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/concepts/{concept_id}")
async def update_concept_ontology(concept_id: str, concept_data: Dict[str, Any]):
    """Update an existing concept in the ontology"""
    try:

        # Try to parse as ObjectId first
        try:
            if len(concept_id) == 24:
                oid = ObjectId(concept_id)
            else:
                # It might be a custom ID like c_1234
                concept = queries.tag_concepts_v2_find_one__update_concept_ontology(concept_id)
                if concept:
                    oid = concept["_id"]
                else:
                    raise HTTPException(status_code=404, detail="Concept not found")
        except Exception:
            # Try to find by custom ID
            concept = queries.tag_concepts_v2_find_one__update_concept_ontology_2(concept_id)
            if concept:
                oid = concept["_id"]
            else:
                raise HTTPException(status_code=404, detail="Concept not found")

        # Update the concept
        update_data = {}
        if "slug" in concept_data:
            update_data["slug"] = concept_data["slug"]
        if "name" in concept_data:
            update_data["name"] = concept_data["name"]
        if "display_name" in concept_data:
            update_data["display_name"] = concept_data["display_name"]
        if "description" in concept_data:
            update_data["description"] = concept_data["description"]
        if "entity_type" in concept_data:
            update_data["entity_type"] = concept_data["entity_type"]

        update_data["updated_at"] = datetime.now(timezone.utc)

        result = queries.tag_concepts_v2_update_one__update_concept_ontology(oid, update_data)

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Concept not found")

        return {"success": True, "message": "Concept updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating concept: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/concepts/{concept_id}")
async def delete_concept_ontology(concept_id: str):
    """Delete a concept from the ontology"""
    try:

        # Try to parse as ObjectId first
        try:
            if len(concept_id) == 24:
                oid = ObjectId(concept_id)
            else:
                # It might be a custom ID like c_1234
                concept = queries.tag_concepts_v2_find_one__delete_concept_ontology_2(concept_id)
                if concept:
                    oid = concept["_id"]
                else:
                    raise HTTPException(status_code=404, detail="Concept not found")
        except Exception:
            # Try to find by custom ID
            concept = queries.tag_concepts_v2_find_one__delete_concept_ontology_3(concept_id)
            if concept:
                oid = concept["_id"]
            else:
                raise HTTPException(status_code=404, detail="Concept not found")

        # Get the concept to find its parents
        concept = queries.tag_concepts_v2_find_one__delete_concept_ontology(oid)
        if not concept:
            raise HTTPException(status_code=404, detail="Concept not found")

        id_variants = concept_id_variants(concept)

        # Remove from parents' children arrays (refs may be ObjectId or legacy string)
        queries.tag_concepts_v2_update_many__delete_concept_ontology(id_variants)

        # Remove this concept from its children's parents arrays
        queries.tag_concepts_v2_update_many__delete_concept_ontology_2(id_variants)

        # Delete tag instances referencing this concept
        queries.tag_instances_delete_many__delete_concept_ontology(id_variants)

        # Delete the concept
        result = queries.tag_concepts_v2_delete_one__delete_concept_ontology(oid)

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Concept not found")

        return {"success": True, "message": "Concept deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting concept: {e}")
        raise HTTPException(status_code=500, detail=str(e))
