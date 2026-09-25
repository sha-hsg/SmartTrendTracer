"""
Ontology tools: statistics, graph visualization, export, and mapping rebuild.
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from bson import ObjectId
import logging

from app.repositories import tag_ontology_tools_queries as queries

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

    return {
        "concepts": {
            "total": queries.tag_concepts_v2_count_documents__get_stats(),
            "active": queries.tag_concepts_v2_count_documents__get_stats_2(),
            "root": queries.tag_concepts_v2_count_documents__get_stats_3(),
            "with_children": queries.tag_concepts_v2_count_documents__get_stats_4()
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
async def get_ontology_graph(include_synonyms: bool = False):
    """Get concept hierarchy as graph data for visualization"""
    try:

        # Get all concepts
        concepts = list(queries.tag_concepts_v2_find__get_ontology_graph())

        # Usage counts in ONE aggregation (tag_instances stores concept_id as
        # ObjectId with a small legacy remainder as strings - merge by str key)
        usage_by_concept = {}
        for row in queries.tag_instances_aggregate__get_ontology_graph():
            key = str(row["_id"])
            usage_by_concept[key] = usage_by_concept.get(key, 0) + row["count"]

        # Build nodes
        nodes = []
        concept_id_map = {}  # Map MongoDB _id to simple numeric ID for graph

        for idx, concept in enumerate(concepts):
            concept_id = str(concept["_id"])
            simple_id = f"c_{idx}"
            concept_id_map[concept_id] = simple_id

            # Look up usage under both id representations
            usage_count = usage_by_concept.get(concept_id, 0)
            custom_id = concept.get("id")
            if custom_id and custom_id != concept_id:
                usage_count += usage_by_concept.get(custom_id, 0)

            # Determine hierarchy level
            hierarchy_level = 0
            if concept.get("parents"):
                hierarchy_level = 1
                # Could calculate deeper levels if needed

            node = {
                "id": simple_id,
                "name": concept["display_name"],
                "display_name": concept["display_name"],
                "slug": concept["slug"],
                "hierarchy_level": hierarchy_level,
                "usage_count": usage_count,
                "entity_type": concept.get("entity_type", "concept"),
                "description": concept.get("description"),
                "verified": concept.get("verified", False),
                "quality_score": concept.get("quality_score", 0.5),
                "child_count": len(concept.get("children", [])),
                "descendant_count": concept.get("descendant_count", 0),
                "is_synonym": False
            }
            nodes.append(node)

        # Add synonym nodes if requested
        if include_synonyms:
            aliases = list(queries.tag_aliases_v2_find__get_ontology_graph())
            for idx, alias in enumerate(aliases):
                alias_id = f"a_{idx}"
                concept_id = str(alias["concept_id"])
                if concept_id in concept_id_map:
                    node = {
                        "id": alias_id,
                        "name": alias["alias_text"],
                        "display_name": alias["alias_text"],
                        "slug": alias["alias_text"].lower().replace(" ", "-"),
                        "hierarchy_level": 2,
                        "usage_count": 0,
                        "entity_type": "synonym",
                        "is_synonym": True,
                        "parent_concept": concept_id_map[concept_id]
                    }
                    nodes.append(node)

        # Build links
        links = []

        # Parent-child relationships
        for concept in concepts:
            concept_id = str(concept["_id"])
            if concept_id not in concept_id_map:
                continue

            source_id = concept_id_map[concept_id]

            # Add links to children
            if concept.get("children"):
                for child_id in concept["children"]:
                    child_id_str = str(child_id)
                    if child_id_str in concept_id_map:
                        links.append({
                            "source": source_id,
                            "target": concept_id_map[child_id_str],
                            "strength": 1.0,
                            "type": "parent-child"
                        })

        # Synonym relationships if included
        if include_synonyms:
            for idx, alias in enumerate(aliases):
                alias_id = f"a_{idx}"
                concept_id = str(alias["concept_id"])
                if concept_id in concept_id_map:
                    links.append({
                        "source": concept_id_map[concept_id],
                        "target": alias_id,
                        "strength": 0.5,
                        "type": "synonym"
                    })

        return {
            "nodes": nodes,
            "links": links
        }
    except Exception as e:
        logger.error(f"Error generating graph data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export")
async def export_ontology():
    """Export the complete ontology structure"""
    try:

        # Get all concepts
        concepts = list(queries.tag_concepts_v2_find__export_ontology())

        # Convert ObjectIds to strings
        for concept in concepts:
            concept["_id"] = str(concept["_id"])
            if concept.get("parents"):
                concept["parents"] = [str(p) for p in concept["parents"]]
            if concept.get("children"):
                concept["children"] = [str(c) for c in concept["children"]]

        # Get all aliases
        aliases = list(queries.tag_aliases_v2_find__export_ontology())
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
