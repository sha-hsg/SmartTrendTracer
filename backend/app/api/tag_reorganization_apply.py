"""
API endpoint for applying tag reorganization recommendations
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List
import logging
from datetime import datetime
from app.services.concept_only_tag_service import ConceptOnlyTagService
from bson import ObjectId

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/apply")
async def apply_reorganization_recommendations(
    recommendations: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """
    Apply tag reorganization recommendations from GPT-5
    
    This endpoint:
    1. Creates new concepts from GPT-5 recommendations
    2. Sets up aliases for variations
    3. Establishes hierarchy relationships
    4. Maps existing tags to new concepts
    """
    try:
        logger.info("Starting to apply reorganization recommendations")
        
        # Initialize services
        concept_service = ConceptOnlyTagService()
        
        # Statistics tracking
        stats = {
            "concepts_created": 0,
            "aliases_created": 0,
            "hierarchy_links": 0,
            "tags_mapped": 0,
            "errors": []
        }
        
        # Extract data from recommendations
        concepts = recommendations.get("concepts", [])
        aliases = recommendations.get("aliases", [])
        root_categories = recommendations.get("root_categories", [])
        
        logger.info(f"Processing {len(concepts)} concepts and {len(aliases)} aliases")
        
        # Step 1: Create all concepts first
        concept_id_map = {}  # Map GPT-5 IDs to MongoDB ObjectIds
        
        for concept_data in concepts:
            try:
                # Prepare concept for creation
                concept = {
                    "id": concept_data.get("id", concept_data.get("slug")),
                    "slug": concept_data.get("slug"),
                    "display_name": concept_data.get("display_name"),
                    "description": concept_data.get("description", ""),
                    "status": "active",
                    "entity_type": concept_data.get("entity_type", "concept"),
                    "icon": concept_data.get("icon"),
                    "color": concept_data.get("color"),
                    "parents": [],  # Will set later
                    "children": [],
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "usage_count": 0
                }
                
                # Check if concept already exists
                existing = concept_service.tag_concepts.find_one({"slug": concept["slug"]})
                if existing:
                    concept_id_map[concept_data.get("id")] = str(existing["_id"])
                    logger.info(f"Concept {concept['slug']} already exists, skipping")
                else:
                    # Insert new concept
                    result = concept_service.tag_concepts.insert_one(concept)
                    concept_id_map[concept_data.get("id")] = str(result.inserted_id)
                    stats["concepts_created"] += 1
                    logger.info(f"Created concept: {concept['display_name']}")
                    
            except Exception as e:
                error_msg = f"Failed to create concept {concept_data.get('slug')}: {e}"
                logger.error(error_msg)
                stats["errors"].append(error_msg)
        
        # Step 2: Update parent-child relationships
        for concept_data in concepts:
            try:
                concept_id = concept_id_map.get(concept_data.get("id"))
                if not concept_id:
                    continue
                    
                parents = concept_data.get("parents", [])
                if parents:
                    parent_ids = []
                    for parent_ref in parents:
                        # Parent can be a string ID reference
                        if isinstance(parent_ref, str):
                            # Try to get from our ID mapping first
                            parent_id = concept_id_map.get(parent_ref)
                            if parent_id:
                                parent_ids.append(ObjectId(parent_id))
                            else:
                                # If parent_ref starts with 'c_', remove it to get the slug
                                slug_to_find = parent_ref
                                if parent_ref.startswith('c_'):
                                    slug_to_find = parent_ref[2:]  # Remove 'c_' prefix
                                
                                # Check if it's a slug reference
                                parent_concept = concept_service.tag_concepts.find_one({"slug": slug_to_find})
                                if parent_concept:
                                    parent_ids.append(parent_concept["_id"])
                                else:
                                    # Also check by id field
                                    parent_concept = concept_service.tag_concepts.find_one({"id": parent_ref})
                                    if parent_concept:
                                        parent_ids.append(parent_concept["_id"])
                                    else:
                                        logger.warning(f"Could not find parent {parent_ref} for {concept_data.get('slug')}")
                    
                    if parent_ids:
                        # Update this concept's parents
                        concept_service.tag_concepts.update_one(
                            {"_id": ObjectId(concept_id)},
                            {"$set": {"parents": parent_ids}}
                        )
                        
                        # Update parent's children
                        for parent_id in parent_ids:
                            concept_service.tag_concepts.update_one(
                                {"_id": parent_id},
                                {"$addToSet": {"children": ObjectId(concept_id)}}
                            )
                        
                        stats["hierarchy_links"] += len(parent_ids)
                        logger.info(f"Set {len(parent_ids)} parents for {concept_data.get('slug')}")
                        
            except Exception as e:
                error_msg = f"Failed to set hierarchy for {concept_data.get('slug')}: {e}"
                logger.error(error_msg)
                stats["errors"].append(error_msg)
        
        # Step 3: Create aliases
        for alias_data in aliases:
            try:
                concept_slug = alias_data.get("concept_slug")
                concept_id = None
                
                # Find the concept for this alias
                for c in concepts:
                    if c.get("slug") == concept_slug:
                        concept_id = concept_id_map.get(c.get("id"))
                        break
                
                if not concept_id:
                    logger.warning(f"Could not find concept for alias: {alias_data.get('alias_text')}")
                    continue
                
                # Create alias
                alias = {
                    "alias_text": alias_data.get("alias_text"),
                    "concept_id": ObjectId(concept_id),
                    "created_at": datetime.utcnow()
                }
                
                # Check if alias already exists
                existing = concept_service.tag_aliases.find_one({
                    "alias_text": alias["alias_text"]
                })
                
                if not existing:
                    concept_service.tag_aliases.insert_one(alias)
                    stats["aliases_created"] += 1
                    logger.info(f"Created alias: {alias['alias_text']} -> {concept_slug}")
                else:
                    logger.info(f"Alias {alias['alias_text']} already exists")
                    
            except Exception as e:
                error_msg = f"Failed to create alias {alias_data.get('alias_text')}: {e}"
                logger.error(error_msg)
                stats["errors"].append(error_msg)
        
        # Step 4: Map existing orphan tags to concepts
        # Find all orphan tags (tags without concept_id)
        orphan_tags = list(concept_service.tag_instances.find({"concept_id": None}))
        logger.info(f"Found {len(orphan_tags)} orphan tags to map")
        
        for tag in orphan_tags:
            tag_text = tag.get("tag_name", "").lower()
            
            # Try to find matching concept or alias
            matched_concept_id = None
            
            # Check exact concept slug match
            for concept in concepts:
                if concept.get("slug", "").lower() == tag_text:
                    matched_concept_id = concept_id_map.get(concept.get("id"))
                    break
            
            # Check alias match
            if not matched_concept_id:
                for alias in aliases:
                    if alias.get("alias_text", "").lower() == tag_text:
                        for c in concepts:
                            if c.get("slug") == alias.get("concept_slug"):
                                matched_concept_id = concept_id_map.get(c.get("id"))
                                break
                        if matched_concept_id:
                            break
            
            # Update tag with concept_id if found
            if matched_concept_id:
                concept_service.tag_instances.update_one(
                    {"_id": tag["_id"]},
                    {"$set": {"concept_id": ObjectId(matched_concept_id)}}
                )
                stats["tags_mapped"] += 1
                logger.info(f"Mapped tag '{tag_text}' to concept")
        
        # Return results
        response = {
            "success": True,
            "message": "Reorganization recommendations applied successfully",
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if stats["errors"]:
            response["warnings"] = f"Completed with {len(stats['errors'])} errors"
        
        logger.info(f"Applied recommendations: {stats}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to apply recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/preview")
async def preview_reorganization_application(task_id: str):
    """
    Preview what would happen if recommendations were applied
    (Shows dry-run of changes without applying them)
    """
    try:
        # This could load the recommendations from the task result
        # and show what would be created/changed
        
        return {
            "task_id": task_id,
            "preview": {
                "concepts_to_create": 0,
                "aliases_to_create": 0,
                "tags_to_map": 0,
                "hierarchy_changes": 0
            },
            "message": "Preview endpoint - to be implemented"
        }
        
    except Exception as e:
        logger.error(f"Failed to preview application: {e}")
        raise HTTPException(status_code=500, detail=str(e))