"""
Ontology Graph API - Provides graph data for visualization
MongoDB version
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
import logging
from app.database.mongodb import get_database
from bson import ObjectId

logger = logging.getLogger(__name__)

# MongoDB connection
db = get_database()

router = APIRouter()


@router.get("/data")
def get_graph_data(
    include_orphans: bool = Query(True),
    min_usage: int = Query(0)
):
    """
    Get ontology graph data in format suitable for force-directed graph.
    
    Returns:
        nodes: List of concepts with metadata
        links: List of parent-child relationships
    """
    try:
        # Get all concepts from MongoDB
        concepts = list(db.tag_concepts_v2.find())
        
        # Build nodes
        nodes = []
        concept_map = {}
        links = []
        
        # First pass: create nodes
        for concept in concepts:
            concept_id = str(concept["_id"])
            
            # Get usage count from tag_instances
            usage_count = db.tag_instances.count_documents({
                "concept_id": concept_id
            })
            
            # Skip if below minimum usage
            if usage_count < min_usage:
                continue
            
            # Check if orphan
            has_parents = len(concept.get("parents", [])) > 0
            has_children = len(concept.get("children", [])) > 0
            is_orphan = not has_parents and not has_children
            
            # Skip orphans if requested
            if not include_orphans and is_orphan and usage_count == 0:
                continue
            
            # Determine level based on parent hierarchy
            level = 0
            if has_parents:
                # Simple level calculation - could be enhanced
                level = 1
                if concept.get("entity_type") in ["person", "organisation", "location"]:
                    level = 2
            
            # Determine node size based on usage and children
            child_count = len(concept.get("children", []))
            size = 5 + min(usage_count * 2 + child_count * 3, 50)  # Min 5, max 55
            
            # Determine color based on entity type and level
            colors = {
                "person": "#FF6B6B",  # Red for people
                "organisation": "#4ECDC4",  # Teal for orgs
                "location": "#45B7D1",  # Blue for locations
                "technology": "#96CEB4",  # Green for tech
                "concept": "#FECA57",  # Yellow for concepts
                "category": "#A29BFE",  # Purple for categories
                "other": "#DFE6E9"  # Gray for others
            }
            entity_type = concept.get("entity_type", "other")
            color = colors.get(entity_type, colors["other"])
            
            # If no entity type, use level-based coloring
            if not entity_type or entity_type == "other":
                level_colors = {
                    0: "#FF6B6B",  # Root - Red
                    1: "#4ECDC4",  # Level 1 - Teal
                    2: "#45B7D1",  # Level 2 - Blue
                    3: "#96CEB4",  # Level 3 - Green
                    4: "#FECA57",  # Level 4 - Yellow
                }
                color = level_colors.get(level, "#DFE6E9")
            
            node = {
                "id": concept_id,
                "name": concept.get("display_name", concept.get("slug", "")),
                "slug": concept.get("slug", ""),
                "level": level,
                "usage": usage_count,
                "size": size,
                "color": color,
                "description": concept.get("description", ""),
                "entity_type": entity_type,
                "is_orphan": is_orphan,
                "child_count": child_count,
                "parent_count": len(concept.get("parents", []))
            }
            
            nodes.append(node)
            concept_map[concept_id] = node
        
        # Second pass: create links based on parent-child relationships
        for concept in concepts:
            concept_id = str(concept["_id"])
            
            # Skip if this concept is not in our map (filtered out)
            if concept_id not in concept_map:
                continue
            
            # Add links for each parent
            for parent_id in concept.get("parents", []):
                parent_id_str = str(parent_id)
                if parent_id_str in concept_map:
                    # Calculate link strength based on usage
                    source_usage = concept_map[parent_id_str]["usage"]
                    target_usage = concept_map[concept_id]["usage"]
                    strength = min(1.0, (source_usage + target_usage) / 100)
                    
                    links.append({
                        "source": parent_id_str,
                        "target": concept_id,
                        "strength": strength,
                        "type": "parent-child"
                    })
        
        # Add alias/synonym links
        aliases = list(db.tag_aliases_v2.find())
        for alias in aliases:
            concept_id = str(alias.get("concept_id"))
            if concept_id in concept_map:
                # Create a virtual node for the alias
                alias_id = f"alias_{str(alias['_id'])}"
                alias_node = {
                    "id": alias_id,
                    "name": alias.get("alias", alias.get("alias_text", "")),
                    "slug": alias.get("alias", "").lower().replace(" ", "-"),
                    "level": concept_map[concept_id]["level"] + 1,
                    "usage": 0,
                    "size": 3,
                    "color": "#B2BEC3",  # Gray for aliases
                    "description": f"Alias of {concept_map[concept_id]['name']}",
                    "entity_type": "alias",
                    "is_alias": True,
                    "child_count": 0,
                    "parent_count": 1
                }
                nodes.append(alias_node)
                
                # Link alias to concept
                links.append({
                    "source": concept_id,
                    "target": alias_id,
                    "strength": 0.3,
                    "type": "alias"
                })
        
        # Calculate graph statistics
        stats = {
            "total_nodes": len(nodes),
            "total_links": len(links),
            "root_nodes": len([n for n in nodes if n["parent_count"] == 0]),
            "leaf_nodes": len([n for n in nodes if n["child_count"] == 0]),
            "max_depth": max([n["level"] for n in nodes]) if nodes else 0,
            "total_usage": sum([n["usage"] for n in nodes]),
            "orphan_count": len([n for n in nodes if n.get("is_orphan", False)]),
            "alias_count": len([n for n in nodes if n.get("is_alias", False)])
        }
        
        return {
            "nodes": nodes,
            "links": links,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error fetching graph data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
def search_concepts(
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, description="Maximum results")
):
    """Search for concepts in the graph"""
    try:
        # Search in MongoDB using text search or regex
        search_results = list(db.tag_concepts_v2.find(
            {"$or": [
                {"display_name": {"$regex": query, "$options": "i"}},
                {"slug": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}}
            ]}
        ).limit(limit))
        
        results = []
        for concept in search_results:
            usage_count = db.tag_instances.count_documents({
                "concept_id": str(concept["_id"])
            })
            
            results.append({
                "id": str(concept["_id"]),
                "name": concept.get("display_name", ""),
                "slug": concept.get("slug", ""),
                "description": concept.get("description", ""),
                "usage": usage_count,
                "entity_type": concept.get("entity_type", "other")
            })
        
        return results
        
    except Exception as e:
        logger.error(f"Error searching concepts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/neighbors/{concept_id}")
def get_concept_neighbors(concept_id: str):
    """Get immediate neighbors of a concept (parents and children)"""
    try:
        # Convert to ObjectId if needed
        try:
            obj_id = ObjectId(concept_id)
            concept = db.tag_concepts_v2.find_one({"_id": obj_id})
        except:
            concept = db.tag_concepts_v2.find_one({"_id": concept_id})
        
        if not concept:
            raise HTTPException(status_code=404, detail="Concept not found")
        
        neighbors = {
            "concept": {
                "id": str(concept["_id"]),
                "name": concept.get("display_name", ""),
                "description": concept.get("description", "")
            },
            "parents": [],
            "children": [],
            "aliases": []
        }
        
        # Get parents
        for parent_id in concept.get("parents", []):
            parent = db.tag_concepts_v2.find_one({"_id": parent_id})
            if parent:
                neighbors["parents"].append({
                    "id": str(parent["_id"]),
                    "name": parent.get("display_name", "")
                })
        
        # Get children
        for child_id in concept.get("children", []):
            child = db.tag_concepts_v2.find_one({"_id": child_id})
            if child:
                neighbors["children"].append({
                    "id": str(child["_id"]),
                    "name": child.get("display_name", "")
                })
        
        # Get aliases
        aliases = list(db.tag_aliases_v2.find({"concept_id": str(concept["_id"])}))
        for alias in aliases:
            neighbors["aliases"].append({
                "id": str(alias["_id"]),
                "name": alias.get("alias", alias.get("alias_text", ""))
            })
        
        return neighbors
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting neighbors: {e}")
        raise HTTPException(status_code=500, detail=str(e))
