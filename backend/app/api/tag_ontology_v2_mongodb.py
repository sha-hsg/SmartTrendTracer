"""
Tag Ontology v2 API - MongoDB Implementation
Handles all tag concept operations using MongoDB
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Dict, Any, Optional
from pymongo import ASCENDING, TEXT
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from datetime import datetime
import os
from bson import ObjectId
import json
import logging
import re

logger = logging.getLogger(__name__)

from app.database.mongodb import get_client, get_database

router = APIRouter()

def get_mongo_client():
    """Get or create MongoDB client singleton"""
    try:
        client = get_client()
        client.admin.command('ping')
        return client
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise HTTPException(status_code=503, detail="MongoDB connection failed")

def get_mongo_db():
    """Get MongoDB database connection"""
    return get_database()

def get_concepts_collection():
    """Get concepts collection with error handling"""
    try:
        db = get_mongo_db()
        return db.tag_concepts_v2
    except Exception as e:
        logger.error(f"Error accessing concepts collection: {e}")
        raise HTTPException(status_code=503, detail="Database unavailable")

def get_aliases_collection():
    """Get aliases collection with error handling"""
    try:
        db = get_mongo_db()
        return db.tag_aliases_v2
    except Exception as e:
        logger.error(f"Error accessing aliases collection: {e}")
        raise HTTPException(status_code=503, detail="Database unavailable")

def get_instances_collection():
    """Get tag instances collection with error handling"""
    try:
        db = get_mongo_db()
        return db.tag_instances
    except Exception as e:
        logger.error(f"Error accessing instances collection: {e}")
        raise HTTPException(status_code=503, detail="Database unavailable")

@router.get("/tree")
def get_tree():
    """Get the complete tag tree - returns array for frontend compatibility"""
    try:
        concepts_col = get_concepts_collection()
        aliases_col = get_aliases_collection()
        
        # Get all concepts
        all_concepts = list(concepts_col.find({"status": {"$ne": "deprecated"}}))
        
        # Get all aliases in one query
        all_aliases = list(aliases_col.find({}))
        aliases_by_concept = {}
        for alias in all_aliases:
            # Convert ObjectId to string if necessary
            concept_id = alias.get("concept_id")
            if isinstance(concept_id, ObjectId):
                concept_id = str(concept_id)
            if concept_id not in aliases_by_concept:
                aliases_by_concept[concept_id] = []
            aliases_by_concept[concept_id].append(alias["alias_text"])
        
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
                "synonyms": aliases_by_concept.get(concept_id, [])  # Use pre-fetched aliases
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

@router.get("/hierarchy")
def get_hierarchy():
    """Get the complete tag hierarchy from MongoDB"""
    concepts_col = get_concepts_collection()
    
    # Get all concepts
    all_concepts = list(concepts_col.find({"status": {"$ne": "deprecated"}}))
    
    # Find root concepts
    root_concepts = [c for c in all_concepts if not c.get("parents") or len(c["parents"]) == 0]
    
    # Build hierarchy
    def add_children_to_concept(concept, all_concepts_map):
        """Add children recursively to concept"""
        if concept.get("children"):
            concept["children_concepts"] = []
            for child_id in concept["children"]:
                # Convert ObjectId to string for lookup
                child_id_str = str(child_id)
                if child_id_str in all_concepts_map:
                    child = all_concepts_map[child_id_str].copy()
                    add_children_to_concept(child, all_concepts_map)
                    concept["children_concepts"].append(child)
        return concept
    
    # Create concept map - use _id or convert to string id
    concept_map = {str(c["_id"]): c for c in all_concepts}
    
    # Build hierarchy for each root
    for root in root_concepts:
        add_children_to_concept(root, concept_map)
    
    return {
        "total_concepts": len(all_concepts),
        "root_concepts": root_concepts,
        "all_concepts": all_concepts
    }

@router.get("/concepts")
def get_all_concepts(include_aliases: bool = Query(False)):
    """Get all concepts from MongoDB"""
    concepts_col = get_concepts_collection()
    aliases_col = get_aliases_collection()
    
    # Get all active concepts
    concepts = list(concepts_col.find({"status": {"$ne": "deprecated"}}))
    
    # Process each concept
    result = []
    for concept in concepts:
        # Get concept_id before removing _id
        concept_id = concept.get("_id")
        
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
        
        # Get synonyms
        # Use the concept_id we saved earlier
        aliases = list(aliases_col.find({"concept_id": concept_id}))
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
        except:
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
                except:
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
                except:
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
    
    # Get aliases - use the original ObjectId we saved
    aliases = list(aliases_col.find({"concept_id": original_id}))
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
    
    # Get usage statistics - convert ObjectId to string for comparison
    # tag_instances stores concept_id as string, not ObjectId
    concept_id_str = str(original_id)
    tweet_count = instances_col.count_documents({
        "content_type": "tweet",
        "concept_id": concept_id_str
    })
    paper_count = instances_col.count_documents({
        "content_type": "paper",
        "concept_id": concept_id_str
    })
    article_count = instances_col.count_documents({
        "content_type": "article",
        "concept_id": concept_id_str
    })
    
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
    
    # Generate concept ID
    count = concepts_col.count_documents({})
    new_id = f"c_{count + 1:04d}"
    
    # Prepare concept document
    concept = {
        "id": new_id,
        "_id": new_id,  # Use as MongoDB _id too
        "slug": concept_data.get("tag", "").lower().replace(" ", "_"),
        "display_name": concept_data.get("display_name"),
        "description": concept_data.get("description"),
        "entity_type": concept_data.get("entity_type", "concept"),
        "parents": [concept_data["parent_id"]] if concept_data.get("parent_id") else [],
        "children": [],
        "level": 0,
        "icon": concept_data.get("icon"),
        "color": concept_data.get("color"),
        "usage_count": 0,
        "status": "active",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    # Calculate level based on parent
    if concept["parents"]:
        parent = concepts_col.find_one({"id": concept["parents"][0]})
        if parent:
            concept["level"] = parent.get("level", 0) + 1
            
            # Update parent's children
            concepts_col.update_one(
                {"id": parent["id"]},
                {"$push": {"children": new_id}}
            )
    
    # Insert concept
    concepts_col.insert_one(concept)
    
    return {"message": "Concept created successfully", "id": new_id}

@router.put("/concept/{concept_id}")
def update_concept(concept_id: str, update_data: dict):
    """Update a concept in MongoDB"""
    concepts_col = get_concepts_collection()
    
    # Prepare update
    update = {
        "$set": {
            "display_name": update_data.get("display_name"),
            "description": update_data.get("description"),
            "updated_at": datetime.utcnow()
        }
    }
    
    # Update concept
    result = concepts_col.update_one({"id": concept_id}, update)
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Concept not found")
    
    return {"message": "Concept updated successfully"}

@router.delete("/concept/{concept_id}")
def delete_concept(concept_id: str):
    """Delete a concept (soft delete)"""
    concepts_col = get_concepts_collection()
    
    # Soft delete by setting status
    result = concepts_col.update_one(
        {"id": concept_id},
        {
            "$set": {
                "status": "deprecated",
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Concept not found")
    
    # Remove from parent's children
    concept = concepts_col.find_one({"id": concept_id})
    if concept and concept.get("parents"):
        for parent_id in concept["parents"]:
            concepts_col.update_one(
                {"id": parent_id},
                {"$pull": {"children": concept_id}}
            )
    
    return {"message": "Concept deleted successfully"}

@router.post("/concept/{concept_id}/alias")
def add_alias(concept_id: str, alias_data: dict):
    """Add an alias to a concept"""
    aliases_col = get_aliases_collection()
    
    # Check if concept exists
    concepts_col = get_concepts_collection()
    if not concepts_col.find_one({"id": concept_id}):
        raise HTTPException(status_code=404, detail="Concept not found")
    
    # Create alias
    alias = {
        "alias_text": alias_data.get("alias_text"),
        "concept_id": concept_id,
        "alias_type": alias_data.get("alias_type", "synonym"),
        "confidence": alias_data.get("confidence", 1.0),
        "created_at": datetime.utcnow()
    }
    
    # Insert alias
    try:
        aliases_col.insert_one(alias)
        return {"message": "Alias added successfully"}
    except Exception as e:
        if "duplicate key" in str(e):
            raise HTTPException(status_code=400, detail="Alias already exists for this concept")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/alias/{alias_text}")
def delete_alias(alias_text: str, concept_id: str = Query(...)):
    """Delete an alias"""
    aliases_col = get_aliases_collection()
    
    result = aliases_col.delete_one({
        "alias_text": alias_text,
        "concept_id": concept_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Alias not found")
    
    return {"message": "Alias deleted successfully"}

@router.get("/search")
def search_concepts(
    query: str = Query(..., min_length=1),
    include_aliases: bool = Query(True)
):
    """Search for concepts by name or alias"""
    concepts_col = get_concepts_collection()
    aliases_col = get_aliases_collection()
    
    results = []
    seen_ids = set()
    
    # Search in concepts using text search
    concept_results = concepts_col.find({
        "$text": {"$search": query},
        "status": {"$ne": "deprecated"}
    }).limit(20)
    
    for concept in concept_results:
        concept_id = concept.get("id", concept.get("_id"))
        if concept_id not in seen_ids:
            # Get synonyms
            aliases = list(aliases_col.find({"concept_id": concept_id}))
            
            result = {
                "id": concept_id,
                "tag": concept["slug"],
                "slug": concept["slug"],
                "display_name": concept["display_name"],
                "description": concept.get("description"),
                "entity_type": concept.get("entity_type"),
                "icon": concept.get("icon"),
                "color": concept.get("color"),
                "usage_count": concept.get("usage_count", 0),
                "match_type": "concept",
                "synonyms": [a["alias_text"] for a in aliases]
            }
            results.append(result)
            seen_ids.add(concept_id)
    
    # Search in aliases if requested
    if include_aliases:
        alias_results = aliases_col.find({
            "alias_text": {"$regex": query, "$options": "i"}
        }).limit(20)
        
        for alias in alias_results:
            concept = concepts_col.find_one({"id": alias["concept_id"]})
            if concept:
                concept_id = concept.get("id", concept.get("_id"))
                if concept_id not in seen_ids:
                    # Get all synonyms
                    all_aliases = list(aliases_col.find({"concept_id": concept_id}))
                
                    result = {
                        "id": concept_id,
                    "tag": concept["slug"],
                    "slug": concept["slug"],
                    "display_name": concept["display_name"],
                    "description": concept.get("description"),
                    "entity_type": concept.get("entity_type"),
                    "icon": concept.get("icon"),
                    "color": concept.get("color"),
                    "usage_count": concept.get("usage_count", 0),
                    "match_type": "alias",
                    "matched_alias": alias["alias_text"],
                    "synonyms": [a["alias_text"] for a in all_aliases]
                }
                results.append(result)
                seen_ids.add(concept_id)
    
    return results

@router.post("/rebuild-mappings")
def rebuild_mappings():
    """Rebuild tag mappings - reprocess orphan tags"""
    instances_col = get_instances_collection()
    concepts_col = get_concepts_collection()
    aliases_col = get_aliases_collection()
    
    # Get all unresolved instances
    orphans = list(instances_col.find({"concept_id": None}))
    
    # Build lookup maps
    concept_by_slug = {}
    concept_by_alias = {}
    
    for concept in concepts_col.find():
        concept_id = concept.get("id", concept.get("_id"))
        concept_by_slug[concept["slug"]] = concept_id
        concept_by_slug[concept["display_name"].lower()] = concept_id
    
    for alias in aliases_col.find():
        concept_by_alias[alias["alias_text"].lower()] = alias["concept_id"]
    
    resolved_count = 0
    for orphan in orphans:
        tag_lower = orphan["tag_text"].lower()
        
        # Try to resolve
        concept_id = None
        if tag_lower in concept_by_alias:
            concept_id = concept_by_alias[tag_lower]
        elif tag_lower.replace(" ", "_") in concept_by_slug:
            concept_id = concept_by_slug[tag_lower.replace(" ", "_")]
        elif tag_lower in concept_by_slug:
            concept_id = concept_by_slug[tag_lower]
        
        if concept_id:
            instances_col.update_one(
                {"_id": orphan["_id"]},
                {"$set": {"concept_id": concept_id}}
            )
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
    concepts_col = get_concepts_collection()
    aliases_col = get_aliases_collection()
    instances_col = get_instances_collection()
    
    return {
        "concepts": {
            "total": concepts_col.count_documents({}),
            "active": concepts_col.count_documents({"status": "active"}),
            "root": concepts_col.count_documents({"parents": []}),
            "with_children": concepts_col.count_documents({"children": {"$ne": []}})
        },
        "aliases": {
            "total": aliases_col.count_documents({}),
            "unique_concepts": len(aliases_col.distinct("concept_id"))
        },
        "instances": {
            "total": instances_col.count_documents({}),
            "tweets": instances_col.count_documents({"content_type": "tweet"}),
            "papers": instances_col.count_documents({"content_type": "paper"}),
            "articles": instances_col.count_documents({"content_type": "article"}),
            "resolved": instances_col.count_documents({"concept_id": {"$ne": None}}),
            "orphaned": instances_col.count_documents({"concept_id": None})
        }
    }

@router.get("/graph")
async def get_ontology_graph(include_synonyms: bool = False):
    """Get concept hierarchy as graph data for visualization"""
    try:
        concepts_col = get_concepts_collection()
        aliases_col = get_aliases_collection()
        instances_col = get_instances_collection()
        
        # Get all concepts
        concepts = list(concepts_col.find({}))
        
        # Build nodes
        nodes = []
        concept_id_map = {}  # Map MongoDB _id to simple numeric ID for graph
        
        for idx, concept in enumerate(concepts):
            concept_id = str(concept["_id"])
            simple_id = f"c_{idx}"
            concept_id_map[concept_id] = simple_id
            
            # Count usage
            usage_count = instances_col.count_documents({"concept_id": concept_id})
            
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
            aliases = list(aliases_col.find({}))
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

@router.post("/concepts")
async def create_concept_ontology(concept_data: Dict[str, Any]):
    """Create a new concept in the ontology"""
    try:
        concepts_col = get_concepts_collection()
        
        # Prepare concept document
        new_concept = {
            "slug": concept_data.get("slug"),
            "display_name": concept_data.get("display_name"),
            "description": concept_data.get("description", ""),
            "entity_type": concept_data.get("entity_type", "concept"),
            "parents": [],
            "children": [],
            "created_at": datetime.now(),
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
            except:
                new_concept["parents"] = [concept_data["parent_id"]]
        
        # Insert the concept
        result = concepts_col.insert_one(new_concept)
        
        # Update parent's children if parent exists
        if concept_data.get("parent_id"):
            try:
                parent_oid = ObjectId(concept_data["parent_id"])
            except:
                parent_oid = concept_data["parent_id"]
            
            concepts_col.update_one(
                {"_id": parent_oid},
                {"$push": {"children": result.inserted_id}}
            )
        
        # Generate ID for the concept
        new_concept["id"] = f"c_{concepts_col.count_documents({})}"
        concepts_col.update_one(
            {"_id": result.inserted_id},
            {"$set": {"id": new_concept["id"]}}
        )
        
        return {"success": True, "id": str(result.inserted_id), "concept_id": new_concept["id"]}
    except Exception as e:
        logger.error(f"Error creating concept: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/concepts/{concept_id}")
async def update_concept_ontology(concept_id: str, concept_data: Dict[str, Any]):
    """Update an existing concept in the ontology"""
    try:
        concepts_col = get_concepts_collection()
        
        # Try to parse as ObjectId first
        try:
            if len(concept_id) == 24:
                oid = ObjectId(concept_id)
            else:
                # It might be a custom ID like c_1234
                concept = concepts_col.find_one({"id": concept_id})
                if concept:
                    oid = concept["_id"]
                else:
                    raise HTTPException(status_code=404, detail="Concept not found")
        except:
            # Try to find by custom ID
            concept = concepts_col.find_one({"id": concept_id})
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
        
        update_data["updated_at"] = datetime.now()
        
        result = concepts_col.update_one(
            {"_id": oid},
            {"$set": update_data}
        )
        
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
        concepts_col = get_concepts_collection()
        
        # Try to parse as ObjectId first
        try:
            if len(concept_id) == 24:
                oid = ObjectId(concept_id)
            else:
                # It might be a custom ID like c_1234
                concept = concepts_col.find_one({"id": concept_id})
                if concept:
                    oid = concept["_id"]
                else:
                    raise HTTPException(status_code=404, detail="Concept not found")
        except:
            # Try to find by custom ID
            concept = concepts_col.find_one({"id": concept_id})
            if concept:
                oid = concept["_id"]
            else:
                raise HTTPException(status_code=404, detail="Concept not found")
        
        # Get the concept to find its parents
        concept = concepts_col.find_one({"_id": oid})
        if not concept:
            raise HTTPException(status_code=404, detail="Concept not found")
        
        # Remove from any parent's children
        if concept.get("parents"):
            for parent_id in concept["parents"]:
                concepts_col.update_one(
                    {"_id": parent_id},
                    {"$pull": {"children": oid}}
                )
        
        # Delete the concept
        result = concepts_col.delete_one({"_id": oid})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Concept not found")
        
        return {"success": True, "message": "Concept deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting concept: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/find-by-name/{tag_name}")
async def find_concept_by_name(tag_name: str):
    """Find a concept by its name, slug, or display_name"""
    try:
        concepts_col = get_concepts_collection()
        
        # Try to find by slug, name, or display_name
        concept = concepts_col.find_one({
            "$or": [
                {"slug": tag_name.lower()},
                {"name": tag_name},
                {"display_name": tag_name},
                {"slug": tag_name.lower().replace(" ", "-")},
                {"name": {"$regex": f"^{re.escape(tag_name)}$", "$options": "i"}}
            ]
        })
        
        if not concept:
            # Try to find in aliases
            aliases_col = get_aliases_collection()
            alias = aliases_col.find_one({"alias": tag_name})
            if alias:
                concept = concepts_col.find_one({"_id": alias["concept_id"]})
        
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

@router.get("/export")
async def export_ontology():
    """Export the complete ontology structure"""
    try:
        concepts_col = get_concepts_collection()
        aliases_col = get_aliases_collection()
        
        # Get all concepts
        concepts = list(concepts_col.find({}))
        
        # Convert ObjectIds to strings
        for concept in concepts:
            concept["_id"] = str(concept["_id"])
            if concept.get("parents"):
                concept["parents"] = [str(p) for p in concept["parents"]]
            if concept.get("children"):
                concept["children"] = [str(c) for c in concept["children"]]
        
        # Get all aliases
        aliases = list(aliases_col.find({}))
        for alias in aliases:
            alias["_id"] = str(alias["_id"])
            alias["concept_id"] = str(alias["concept_id"])
        
        return {
            "version": "2.0",
            "export_date": datetime.now().isoformat(),
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
