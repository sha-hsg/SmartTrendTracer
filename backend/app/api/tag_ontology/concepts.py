"""
Concept CRUD operations and hierarchy views.
Tree, list, detail, create, update, delete endpoints.
"""
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timezone
from bson import ObjectId
import logging

from .utils import (
    get_concepts_collection,
    get_aliases_collection,
    get_instances_collection,
    find_concept_by_any_id,
    concept_id_variants,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/tree")
def get_tree():
    """Get the complete tag tree - returns array for frontend compatibility"""
    try:
        concepts_col = get_concepts_collection()
        aliases_col = get_aliases_collection()

        # Get all concepts
        all_concepts = list(concepts_col.find({"status": {"$ne": "deprecated"}}))

        # Get all aliases in one query, keyed by the string form of concept_id
        # (aliases store concept_id as ObjectId; legacy rows may hold "c_..." strings)
        all_aliases = list(aliases_col.find({}))
        aliases_by_concept = {}
        for alias in all_aliases:
            key = str(alias.get("concept_id"))
            aliases_by_concept.setdefault(key, []).append(alias["alias_text"])

        # Build concept map - handle both id and _id fields
        concept_map = {}
        for c in all_concepts:
            # Use 'id' if it exists, otherwise use '_id' converted to string
            concept_id = c.get("id") or str(c["_id"])
            c["id"] = concept_id  # Ensure concept has an 'id' field
            concept_map[concept_id] = c
            # Also map by ObjectId string representation for child lookups
            if "_id" in c:
                concept_map[str(c["_id"])] = c
            # Merge synonyms stored under either key (ObjectId string or custom id)
            oid_str = str(c.get("_id"))
            synonyms = list(aliases_by_concept.get(oid_str, []))
            if concept_id != oid_str:
                synonyms += aliases_by_concept.get(concept_id, [])
            c["_synonyms"] = list(dict.fromkeys(synonyms))

        # Find root concepts (no parents)
        root_concepts = []
        for concept in all_concepts:
            if not concept.get("parents") or len(concept["parents"]) == 0:
                root_concepts.append(concept)

        # Build hierarchy recursively
        def build_hierarchy(concept):
            """Build hierarchy node with children"""
            concept_id = concept.get("id", concept.get("_id"))
            node = {
                "id": concept_id,
                "tag": concept["slug"],  # Frontend expects 'tag'
                "slug": concept["slug"],
                "display_name": concept["display_name"],
                "description": concept.get("description"),
                "entity_type": concept.get("entity_type"),
                "icon": concept.get("icon"),
                "color": concept.get("color"),
                "child_count": len(concept.get("children", [])),
                "descendant_count": len(concept.get("children", [])),  # Simplified
                "synonyms": concept.get("_synonyms", [])  # Pre-fetched, both id keys merged
            }

            # Add children recursively
            if concept.get("children"):
                node["children"] = []
                for child_id in concept["children"]:
                    # Convert ObjectId to string for lookup
                    child_id_str = str(child_id) if isinstance(child_id, ObjectId) else child_id
                    if child_id_str in concept_map:
                        child_node = build_hierarchy(concept_map[child_id_str])
                        node["children"].append(child_node)

            return node

        # Build tree from roots - sort by priority first, then by display_name
        tree = [build_hierarchy(root) for root in sorted(root_concepts, key=lambda x: (x.get("priority", 999), x["display_name"]))]

        return tree

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_tree: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching tree: {str(e)}")


@router.get("/concepts")
def get_all_concepts(include_aliases: bool = Query(False)):
    """Get all concepts from MongoDB"""
    concepts_col = get_concepts_collection()
    aliases_col = get_aliases_collection()

    # Get all active concepts
    concepts = list(concepts_col.find({"status": {"$ne": "deprecated"}}))

    # Fetch all aliases in ONE query and group them by the string form of
    # concept_id (aliases store ObjectId; legacy rows may hold custom "c_..." ids)
    aliases_by_concept = {}
    for alias in aliases_col.find({}):
        key = str(alias.get("concept_id"))
        aliases_by_concept.setdefault(key, []).append(alias)

    # Process each concept
    result = []
    for concept in concepts:
        # Get concept_id before removing _id
        concept_id = concept.get("_id")
        custom_id = concept.get("id")

        # Convert _id to string id
        if "_id" in concept:
            concept["id"] = str(concept["_id"])
            concept.pop("_id", None)

        concept.pop("metadata", None)

        # Convert ObjectIds in parents and children to strings
        if concept.get("parents"):
            concept["parents"] = [str(p) for p in concept["parents"]]
        if concept.get("children"):
            concept["children"] = [str(c) for c in concept["children"]]

        # Add frontend compatibility fields
        concept["tag"] = concept["slug"]

        # Get synonyms from the pre-fetched alias map (both id keys)
        aliases = list(aliases_by_concept.get(str(concept_id), []))
        if custom_id and custom_id != str(concept_id):
            aliases += aliases_by_concept.get(custom_id, [])
        concept["synonyms"] = [a["alias_text"] for a in aliases]

        if include_aliases:
            concept["aliases"] = [
                {
                    "text": a["alias_text"],
                    "type": a.get("alias_type", "synonym"),
                    "confidence": a.get("confidence", 1.0)
                }
                for a in aliases
            ]

        result.append(concept)

    return sorted(result, key=lambda x: x["display_name"])


@router.get("/concept/{concept_id}")
def get_concept_detail(concept_id: str):
    """Get detailed information about a specific concept"""
    concepts_col = get_concepts_collection()
    aliases_col = get_aliases_collection()
    instances_col = get_instances_collection()

    # Get concept - try both id field and _id (ObjectId)
    concept = concepts_col.find_one({"id": concept_id})
    if not concept:
        # Try with ObjectId if it looks like one
        try:
            if len(concept_id) == 24:  # ObjectId is 24 hex chars
                concept = concepts_col.find_one({"_id": ObjectId(concept_id)})
        except Exception:
            pass

    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")

    # Ensure concept has an id field and save the ObjectId for later
    original_id = concept.get("_id")
    if "id" not in concept:
        concept["id"] = str(concept["_id"])

    # Remove MongoDB internals (but we saved original_id)
    concept.pop("_id", None)
    concept.pop("metadata", None)

    # Add frontend compatibility fields
    concept["tag"] = concept["slug"]
    concept["child_count"] = len(concept.get("children", []))
    concept["descendant_count"] = len(concept.get("children", []))  # Simplified

    # Convert parent IDs to strings and set parent_id
    if concept.get("parents"):
        concept["parents"] = [str(p) for p in concept["parents"]]
        concept["parent_id"] = concept["parents"][0]
    else:
        concept["parent_id"] = None

    # Get parent details
    if concept.get("parents"):
        # Convert parent IDs to ObjectIds if needed
        parent_ids = []
        for pid in concept["parents"]:
            if isinstance(pid, str) and len(pid) == 24:
                try:
                    parent_ids.append(ObjectId(pid))
                except Exception:
                    parent_ids.append(pid)
            else:
                parent_ids.append(pid)

        parent_concepts = list(concepts_col.find({"_id": {"$in": parent_ids}}))

        # Ensure parents have id field
        for p in parent_concepts:
            if "id" not in p:
                p["id"] = str(p["_id"])

        concept["parent_details"] = [
            {
                "id": p.get("id", str(p["_id"])),
                "tag": p["slug"],
                "slug": p["slug"],
                "display_name": p["display_name"],
                "icon": p.get("icon"),
                "color": p.get("color")
            }
            for p in parent_concepts
        ]

        # Set single parent for frontend (first parent)
        if parent_concepts:
            first_parent = parent_concepts[0]
            concept["parent"] = {
                "id": first_parent.get("id", str(first_parent["_id"])),
                "tag": first_parent["slug"],
                "display_name": first_parent["display_name"]
            }
    else:
        concept["parent_details"] = []
        concept["parent"] = None

    # Get children details
    if concept.get("children"):
        # First convert all children IDs to strings in the concept
        concept["children"] = [str(c) for c in concept["children"]]

        # Convert child IDs to ObjectIds for query
        child_ids = []
        for cid in concept["children"]:
            if isinstance(cid, str) and len(cid) == 24:
                try:
                    child_ids.append(ObjectId(cid))
                except Exception:
                    child_ids.append(cid)
            else:
                child_ids.append(cid)

        child_concepts = list(concepts_col.find({"_id": {"$in": child_ids}}))

        # Ensure children have id field
        for c in child_concepts:
            if "id" not in c:
                c["id"] = str(c["_id"])

        children_list = [
            {
                "id": c.get("id", str(c["_id"])),
                "tag": c["slug"],
                "slug": c["slug"],
                "display_name": c["display_name"],
                "icon": c.get("icon"),
                "color": c.get("color"),
                "usage_count": c.get("usage_count", 0),
                "child_count": len(c.get("children", []))
            }
            for c in child_concepts
        ]
        concept["children_details"] = children_list
        concept["children"] = children_list  # Frontend expects this
    else:
        concept["children_details"] = []
        concept["children"] = []

    # All id representations under which references may be stored
    id_variants = [original_id, str(original_id)]
    if concept.get("id") and concept["id"] not in id_variants:
        id_variants.append(concept["id"])

    # Get aliases (stored as ObjectId; legacy rows may hold custom "c_..." ids)
    aliases = list(aliases_col.find({"concept_id": {"$in": id_variants}}))
    concept["aliases"] = [
        {
            "text": a["alias_text"],
            "type": a.get("alias_type", "synonym"),
            "confidence": a.get("confidence", 1.0),
            "created_at": str(a.get("created_at", ""))
        }
        for a in aliases
    ]

    # Add synonyms as string array
    concept["synonyms"] = [a["alias_text"] for a in aliases]

    # Get usage statistics in ONE aggregation.
    # tag_instances stores concept_id as ObjectId (with a small legacy
    # remainder as strings), so match both representations.
    usage_by_type = {}
    for row in instances_col.aggregate([
        {"$match": {"concept_id": {"$in": id_variants}}},
        {"$group": {"_id": "$content_type", "count": {"$sum": 1}}}
    ]):
        usage_by_type[row["_id"]] = row["count"]
    tweet_count = usage_by_type.get("tweet", 0)
    paper_count = usage_by_type.get("paper", 0)
    article_count = usage_by_type.get("article", 0)

    concept["usage_stats"] = {
        "tweet_count": tweet_count,
        "article_count": article_count,
        "paper_count": paper_count,
        "total_count": tweet_count + article_count + paper_count
    }

    return concept


@router.post("/concept")
def create_concept(concept_data: dict):
    """Create a new concept in MongoDB"""
    concepts_col = get_concepts_collection()

    # Collision-free, schema-compliant IDs: ObjectId as _id,
    # custom id derived from it ("c_" + ObjectId string)
    new_oid = ObjectId()
    new_id = f"c_{new_oid}"

    # Prepare concept document
    concept = {
        "_id": new_oid,
        "id": new_id,
        "slug": concept_data.get("tag", "").lower().replace(" ", "_"),
        "display_name": concept_data.get("display_name"),
        "description": concept_data.get("description"),
        "entity_type": concept_data.get("entity_type", "concept"),
        "parents": [],
        "children": [],
        "level": 0,
        "icon": concept_data.get("icon"),
        "color": concept_data.get("color"),
        "usage_count": 0,
        "status": "active",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }

    # Resolve parent (custom id or ObjectId string) and calculate level
    parent = None
    if concept_data.get("parent_id"):
        parent = find_concept_by_any_id(concepts_col, str(concept_data["parent_id"]))
        if parent:
            concept["parents"] = [parent["_id"]]
            concept["level"] = parent.get("level", 0) + 1

    # Insert concept
    concepts_col.insert_one(concept)

    # Update parent's children (ObjectId reference, schema-consistent)
    if parent:
        concepts_col.update_one(
            {"_id": parent["_id"]},
            {"$push": {"children": new_oid}}
        )

    return {"message": "Concept created successfully", "id": new_id}


@router.put("/concept/{concept_id}")
def update_concept(concept_id: str, update_data: dict):
    """Update a concept in MongoDB - only explicitly provided fields are set"""
    concepts_col = get_concepts_collection()

    # Lookup via custom id field or ObjectId fallback
    concept = find_concept_by_any_id(concepts_col, concept_id)
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")

    # Only set fields that were explicitly provided (no None overwrites)
    fields = {
        field: update_data[field]
        for field in ("display_name", "description", "entity_type", "icon", "color", "slug")
        if field in update_data
    }
    fields["updated_at"] = datetime.now(timezone.utc)

    concepts_col.update_one({"_id": concept["_id"]}, {"$set": fields})

    return {"message": "Concept updated successfully"}


@router.delete("/concept/{concept_id}")
def delete_concept(concept_id: str):
    """Delete a concept (soft delete) and clean up all references"""
    concepts_col = get_concepts_collection()
    instances_col = get_instances_collection()

    # Lookup via custom id field or ObjectId fallback
    concept = find_concept_by_any_id(concepts_col, concept_id)
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")

    id_variants = concept_id_variants(concept)

    # Soft delete by setting status
    concepts_col.update_one(
        {"_id": concept["_id"]},
        {
            "$set": {
                "status": "deprecated",
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )

    # Remove from parents' children arrays (refs may be ObjectId or legacy string)
    concepts_col.update_many(
        {"children": {"$in": id_variants}},
        {"$pull": {"children": {"$in": id_variants}}}
    )

    # Remove this concept from its children's parents arrays
    concepts_col.update_many(
        {"parents": {"$in": id_variants}},
        {"$pull": {"parents": {"$in": id_variants}}}
    )

    # Delete tag instances referencing this concept
    instances_col.delete_many({"concept_id": {"$in": id_variants}})

    return {"message": "Concept deleted successfully"}
