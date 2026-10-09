"""
Concept CRUD operations and hierarchy views.
Tree, list, detail, create, update, delete endpoints.
"""
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timezone
from bson import ObjectId
import logging

from .utils import (
    concept_id_variants,
)
from app.repositories import tag_ontology_concepts_queries as queries
from app.repositories import ontology as ontology_repo

logger = logging.getLogger(__name__)

router = APIRouter()


TREE_LOOSE_LIMIT = 500   # parentless, childless concepts shown without a search (of ~26k)


@router.get("/tree")
def get_tree(q: Optional[str] = Query(None, description="Name/slug/alias search over all concepts"),
             limit: int = Query(TREE_LOOSE_LIMIT, ge=1, le=5000)):
    """Concept tree, built from `parents` (the `children` lists are stale).

    Without q: every concept placed in the hierarchy plus the `limit` most used
    loose concepts (was: all 28k concepts, 7.8 MB, and the ~2000 concepts with a
    parent were missing). With q: the matching concepts (most used first, up to
    `limit`) and their ancestors."""
    concepts = {str(c["_id"]): c for c in queries.find_active_concepts()}
    usage = ontology_repo.usage_counts()
    synonyms: Dict[str, list] = {}
    for alias in ontology_repo.find_all_aliases():
        if alias.get("alias_text"):
            synonyms.setdefault(str(alias.get("concept_id")), []).append(alias["alias_text"])

    parents = {cid: [str(p) for p in c.get("parents") or [] if str(p) in concepts] for cid, c in concepts.items()}
    children: Dict[str, list] = {}
    for cid, ps in parents.items():
        for p in ps:
            children.setdefault(p, []).append(cid)

    def by_usage(ids):
        return sorted(ids, key=lambda i: (-usage.get(i, 0), (concepts[i].get("display_name") or "").lower()))

    if q:
        needle = q.strip().lower()
        matches = [cid for cid, c in concepts.items()
                   if needle in (c.get("display_name") or "").lower() or needle in (c.get("slug") or "").lower()
                   or any(needle in a.lower() for a in synonyms.get(cid, []))]
        keep, stack = set(), by_usage(matches)[:limit]
        while stack:                                   # matches plus all their ancestors
            cid = stack.pop()
            if cid not in keep:
                keep.add(cid)
                stack.extend(parents[cid])
    else:
        placed = {cid for cid in concepts if parents[cid] or cid in children}
        loose = [cid for cid in concepts if cid not in placed]
        keep = placed | set(by_usage(loose)[:limit])

    def node(cid, path=()):
        c = concepts[cid]
        kids = [k for k in by_usage(children.get(cid, [])) if k in keep and k not in path]
        n = {
            "id": cid,
            "tag": c.get("slug"),  # frontend expects 'tag'
            "slug": c.get("slug"),
            "display_name": c.get("display_name") or c.get("slug"),
            "description": c.get("description"),
            "entity_type": c.get("entity_type"),
            "icon": c.get("icon"),
            "color": c.get("color"),
            "usage_count": usage.get(cid, 0),
            "child_count": len(children.get(cid, [])),
            "descendant_count": len(children.get(cid, [])),
            "synonyms": list(dict.fromkeys(synonyms.get(cid, []))),
        }
        if kids:
            n["children"] = [node(k, path + (cid,)) for k in kids]
        return n

    roots = [cid for cid in keep if not any(p in keep for p in parents[cid])]
    # hierarchy roots first (by priority, name), then loose concepts by usage
    roots.sort(key=lambda i: (i not in children, concepts[i].get("priority", 999) if i in children else 0,
                              -usage.get(i, 0), (concepts[i].get("display_name") or "").lower()))
    return [node(r) for r in roots]


@router.get("/concepts")
def get_all_concepts(include_aliases: bool = Query(False)):
    """Get all concepts from MongoDB"""

    # Get all active concepts
    concepts = list(queries.find_active_concepts())

    # Fetch all aliases in ONE query and group them by the string form of
    # concept_id (aliases store ObjectId; legacy rows may hold custom "c_..." ids)
    aliases_by_concept = {}
    for alias in ontology_repo.find_all_aliases():
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

    # Get concept - try both id field and _id (ObjectId)
    concept = ontology_repo.find_concept_by_any_id(concept_id)

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

        parent_concepts = list(queries.tag_concepts_v2_find__get_concept_detail(parent_ids))

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

        child_concepts = list(queries.tag_concepts_v2_find__get_concept_detail_2(child_ids))

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
    aliases = list(queries.tag_aliases_v2_find__get_concept_detail(id_variants))
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
    for row in queries.tag_instances_aggregate__get_concept_detail(id_variants):
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

    from app.repositories.concepts import concept_slug
    new_oid = ObjectId()

    # Prepare concept document
    concept = {
        "_id": new_oid,
        "slug": concept_slug(concept_data.get("tag", "")),
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
        parent = ontology_repo.find_concept_by_any_id(str(concept_data["parent_id"]))
        if parent:
            concept["parents"] = [parent["_id"]]
            concept["level"] = parent.get("level", 0) + 1

    # Insert concept
    queries.tag_concepts_v2_insert_one__create_concept(concept)

    # Update parent's children (ObjectId reference, schema-consistent)
    if parent:
        queries.tag_concepts_v2_update_one__create_concept(parent, new_oid)

    return {"message": "Concept created successfully", "id": str(new_oid)}


@router.put("/concept/{concept_id}")
def update_concept(concept_id: str, update_data: dict):
    """Update a concept in MongoDB - only explicitly provided fields are set"""

    # Lookup via custom id field or ObjectId fallback
    concept = ontology_repo.find_concept_by_any_id(concept_id)
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")

    # Only set fields that were explicitly provided (no None overwrites)
    fields = {
        field: update_data[field]
        for field in ("display_name", "description", "entity_type", "icon", "color", "slug")
        if field in update_data
    }
    fields["updated_at"] = datetime.now(timezone.utc)

    queries.tag_concepts_v2_update_one__update_concept(fields, concept)

    return {"message": "Concept updated successfully"}


@router.delete("/concept/{concept_id}")
def delete_concept(concept_id: str):
    """Delete a concept (soft delete) and clean up all references"""

    # Lookup via custom id field or ObjectId fallback
    concept = ontology_repo.find_concept_by_any_id(concept_id)
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")

    id_variants = concept_id_variants(concept)

    # Soft delete by setting status
    queries.tag_concepts_v2_update_one__delete_concept(concept)

    # Remove from parents' children arrays (refs may be ObjectId or legacy string)
    ontology_repo.remove_from_children(id_variants)

    # Remove this concept from its children's parents arrays
    ontology_repo.remove_from_parents(id_variants)

    # Delete tag instances referencing this concept
    ontology_repo.delete_concept_instances(id_variants)

    return {"message": "Concept deleted successfully"}
