"""
Ontology tools: statistics, graph visualization, export, and mapping rebuild.
"""
from typing import Dict
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timezone
from bson import ObjectId
import logging

from app.repositories import tag_ontology_tools_queries as queries
from app.repositories import ontology as ontology_repo

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/rebuild-mappings")
def rebuild_mappings():
    """Rebuild tag mappings - reprocess orphan tags"""

    # Get all unresolved instances
    orphans = list(queries.tag_instances_find__rebuild_mappings())

    # Build lookup maps - values are always ObjectIds (schema-consistent)
    concept_by_slug = {}
    concept_by_alias = {}
    custom_to_oid = {}

    for concept in queries.tag_concepts_v2_find__rebuild_mappings():
        oid = concept["_id"]
        concept_by_slug[concept["slug"]] = oid
        concept_by_slug[concept["display_name"].lower()] = oid
        custom_to_oid[str(oid)] = oid
        if concept.get("id"):
            custom_to_oid[concept["id"]] = oid

    for alias in queries.tag_aliases_v2_find__rebuild_mappings():
        cid = alias["concept_id"]
        oid = cid if isinstance(cid, ObjectId) else custom_to_oid.get(str(cid))
        if oid is not None:
            concept_by_alias[alias["alias_text"].lower()] = oid

    resolved_count = 0
    for orphan in orphans:
        # Orphan instances carry display_name (there is no tag_text field)
        display_name = orphan.get("display_name") or ""
        if not display_name:
            continue
        tag_lower = display_name.lower()

        # Try to resolve
        concept_id = None
        if tag_lower in concept_by_alias:
            concept_id = concept_by_alias[tag_lower]
        elif tag_lower.replace(" ", "_") in concept_by_slug:
            concept_id = concept_by_slug[tag_lower.replace(" ", "_")]
        elif tag_lower in concept_by_slug:
            concept_id = concept_by_slug[tag_lower]

        if concept_id:
            queries.tag_instances_update_one__rebuild_mappings(orphan, concept_id)
            resolved_count += 1

    return {
        "message": "Mappings rebuilt",
        "orphans_found": len(orphans),
        "resolved": resolved_count,
        "still_orphaned": len(orphans) - resolved_count
    }


@router.get("/stats")
def get_stats():
    """Get tag system statistics"""
    org = ontology_repo.organization_stats()

    return {
        "concepts": {
            "total": ontology_repo.count_concepts(),
            "active": queries.tag_concepts_v2_count_documents__get_stats_2(),
            # same definition as /api/concepts/organization/stats
            **{k: org[k] for k in ("organized_concepts", "unorganized_concepts")},
            "root": org["root_concepts"],
            "with_children": org["with_children"]
        },
        "aliases": {
            "total": queries.tag_aliases_v2_count_documents__get_stats(),
            "unique_concepts": len(queries.tag_aliases_v2_distinct__get_stats())
        },
        "instances": {
            "total": queries.tag_instances_count_documents__get_stats(),
            "tweets": queries.tag_instances_count_documents__get_stats_2(),
            "papers": queries.tag_instances_count_documents__get_stats_3(),
            "articles": queries.tag_instances_count_documents__get_stats_4(),
            "resolved": queries.tag_instances_count_documents__get_stats_5(),
            "orphaned": queries.tag_instances_count_documents__get_stats_6()
        }
    }


@router.get("/graph")
async def get_ontology_graph(include_synonyms: bool = False,
                             limit: int = Query(300, ge=0, le=5000, description="loose concepts, most used first")):
    """Concept hierarchy as graph data: every concept placed in the hierarchy plus
    the `limit` most used loose concepts. Links come from `parents` (the `children`
    lists are stale). Was: all 28k concepts as nodes, 9 MB, almost no links."""
    concepts = {str(c["_id"]): c for c in queries.find_all_concepts()}
    usage = ontology_repo.usage_counts()
    parents = {cid: [str(p) for p in c.get("parents") or [] if str(p) in concepts] for cid, c in concepts.items()}
    child_count: Dict[str, int] = {}
    for ps in parents.values():
        for p in ps:
            child_count[p] = child_count.get(p, 0) + 1

    placed = [cid for cid in concepts if parents[cid] or cid in child_count]
    loose = sorted((cid for cid in concepts if not parents[cid] and cid not in child_count),
                   key=lambda i: -usage.get(i, 0))[:limit]
    graph_ids = {cid: f"c_{idx}" for idx, cid in enumerate(placed + loose)}

    nodes = []
    for cid, simple_id in graph_ids.items():
        c = concepts[cid]
        nodes.append({
            "id": simple_id,
            "concept_id": cid,
            "name": c.get("display_name") or c.get("slug"),
            "display_name": c.get("display_name") or c.get("slug"),
            "slug": c.get("slug"),
            "hierarchy_level": 1 if parents[cid] else 0,
            "usage_count": usage.get(cid, 0),
            "entity_type": c.get("entity_type", "concept"),
            "description": c.get("description"),
            "verified": c.get("verified", False),
            "quality_score": c.get("quality_score", 0.5),
            "child_count": child_count.get(cid, 0),
            "descendant_count": child_count.get(cid, 0),
            "is_synonym": False,
        })
    links = [{"source": graph_ids[p], "target": graph_ids[cid], "strength": 1.0, "type": "parent-child"}
             for cid in graph_ids for p in parents[cid] if p in graph_ids]

    if include_synonyms:
        for idx, alias in enumerate(ontology_repo.find_all_aliases()):
            owner = graph_ids.get(str(alias.get("concept_id")))
            text = alias.get("alias_text")
            if not owner or not text:
                continue
            alias_id = f"a_{idx}"
            nodes.append({"id": alias_id, "name": text, "display_name": text,
                          "slug": text.lower().replace(" ", "-"), "hierarchy_level": 2, "usage_count": 0,
                          "entity_type": "synonym", "is_synonym": True, "parent_concept": owner})
            links.append({"source": owner, "target": alias_id, "strength": 0.5, "type": "synonym"})

    return {"nodes": nodes, "links": links, "total_concepts": len(concepts),
            "hidden_concepts": len(concepts) - len(graph_ids)}


@router.get("/export")
async def export_ontology():
    """Export the complete ontology structure"""
    try:

        # Get all concepts
        concepts = list(queries.find_all_concepts())

        # Convert ObjectIds to strings
        for concept in concepts:
            concept["_id"] = str(concept["_id"])
            if concept.get("parents"):
                concept["parents"] = [str(p) for p in concept["parents"]]
            if concept.get("children"):
                concept["children"] = [str(c) for c in concept["children"]]

        # Get all aliases
        aliases = list(ontology_repo.find_all_aliases())
        for alias in aliases:
            alias["_id"] = str(alias["_id"])
            alias["concept_id"] = str(alias["concept_id"])

        return {
            "version": "2.0",
            "export_date": datetime.now(timezone.utc).isoformat(),
            "concepts": concepts,
            "aliases": aliases,
            "stats": {
                "total_concepts": len(concepts),
                "total_aliases": len(aliases)
            }
        }
    except Exception as e:
        logger.error(f"Error exporting ontology: {e}")
        raise HTTPException(status_code=500, detail=str(e))
