"""
Comprehensive tag reorganization that actually reorganizes ALL tags
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Set
import logging
from datetime import datetime
from app.services.concept_only_tag_service import ConceptOnlyTagService
from bson import ObjectId
import re

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/apply-comprehensive")
async def apply_comprehensive_reorganization(recommendations: Dict[str, Any]):
    """
    Comprehensively apply GPT-5 reorganization to ALL tags in the system
    
    This does a COMPLETE reorganization:
    1. Clears existing concepts and creates new ones
    2. Processes all merge proposals
    3. Maps ALL existing tags to new concepts
    4. Sets up complete hierarchy
    """
    try:
        logger.info("Starting COMPREHENSIVE tag reorganization")
        
        # Initialize service
        service = ConceptOnlyTagService()
        
        # Statistics
        stats = {
            "concepts_created": 0,
            "aliases_created": 0,
            "hierarchy_links": 0,
            "tags_remapped": 0,
            "merges_processed": 0,
            "concepts_cleared": 0,
            "errors": []
        }
        
        # Step 1: Clear existing concepts (optional - for clean slate)
        if recommendations.get("clear_existing", False):
            logger.info("Clearing existing concepts for clean reorganization")
            stats["concepts_cleared"] = service.tag_concepts.count_documents({})
            service.tag_concepts.delete_many({})
            service.tag_aliases.delete_many({})
        
        # Step 2: Create ID mapping for GPT-5's concept IDs
        gpt5_id_to_mongo_id = {}
        gpt5_id_to_slug = {}
        
        # Extract concepts and build mappings
        concepts = recommendations.get("concepts", [])
        aliases = recommendations.get("aliases", [])
        merge_proposals = recommendations.get("merge_proposals", [])
        
        # Build GPT-5 ID to slug mapping
        for concept in concepts:
            gpt5_id = concept.get("id")
            slug = concept.get("slug")
            if gpt5_id and slug:
                gpt5_id_to_slug[gpt5_id] = slug
        
        logger.info(f"Processing {len(concepts)} concepts")
        
        # Step 3: Create all concepts
        for concept_data in concepts:
            try:
                gpt5_id = concept_data.get("id")
                slug = concept_data.get("slug")
                
                # Check if concept exists
                existing = service.tag_concepts.find_one({"slug": slug})
                
                if existing:
                    gpt5_id_to_mongo_id[gpt5_id] = str(existing["_id"])
                    logger.info(f"Concept {slug} already exists")
                else:
                    # Create new concept
                    new_concept = {
                        "id": gpt5_id,
                        "slug": slug,
                        "display_name": concept_data.get("display_name", slug),
                        "description": concept_data.get("description", ""),
                        "status": "active",
                        "entity_type": concept_data.get("entity_type", "concept"),
                        "icon": concept_data.get("icon"),
                        "color": concept_data.get("color"),
                        "parents": [],  # Will set later
                        "children": [],
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                        "usage_count": concept_data.get("usage_count", 0)
                    }
                    
                    result = service.tag_concepts.insert_one(new_concept)
                    gpt5_id_to_mongo_id[gpt5_id] = str(result.inserted_id)
                    stats["concepts_created"] += 1
                    logger.info(f"Created concept: {slug}")
                    
            except Exception as e:
                error_msg = f"Failed to create concept {concept_data.get('slug')}: {e}"
                logger.error(error_msg)
                stats["errors"].append(error_msg)
        
        # Step 4: Set up hierarchy
        logger.info("Setting up concept hierarchy")
        for concept_data in concepts:
            try:
                gpt5_id = concept_data.get("id")
                mongo_id = gpt5_id_to_mongo_id.get(gpt5_id)
                
                if not mongo_id:
                    continue
                
                parents = concept_data.get("parents", [])
                if parents:
                    parent_mongo_ids = []
                    
                    for parent_ref in parents:
                        # Convert GPT-5 ID to MongoDB ID
                        parent_slug = gpt5_id_to_slug.get(parent_ref, parent_ref)
                        
                        # Remove c_ prefix if present
                        if parent_slug.startswith("c_"):
                            parent_slug = parent_slug[2:]
                        
                        # Find parent concept
                        parent_concept = service.tag_concepts.find_one({"slug": parent_slug})
                        if parent_concept:
                            parent_mongo_ids.append(parent_concept["_id"])
                        else:
                            # Try to find by GPT-5 ID
                            parent_mongo_id = gpt5_id_to_mongo_id.get(parent_ref)
                            if parent_mongo_id:
                                parent_mongo_ids.append(ObjectId(parent_mongo_id))
                    
                    if parent_mongo_ids:
                        # Update concept's parents
                        service.tag_concepts.update_one(
                            {"_id": ObjectId(mongo_id)},
                            {"$set": {"parents": parent_mongo_ids}}
                        )
                        
                        # Update parents' children
                        for parent_id in parent_mongo_ids:
                            service.tag_concepts.update_one(
                                {"_id": parent_id},
                                {"$addToSet": {"children": ObjectId(mongo_id)}}
                            )
                        
                        stats["hierarchy_links"] += len(parent_mongo_ids)
                        
            except Exception as e:
                error_msg = f"Failed to set hierarchy: {e}"
                logger.error(error_msg)
                stats["errors"].append(error_msg)
        
        # Step 5: Create aliases with proper concept references
        logger.info(f"Creating {len(aliases)} aliases")
        for alias_data in aliases:
            try:
                alias_text = alias_data.get("alias_text")
                alias_of = alias_data.get("alias_of")  # This is a GPT-5 ID like c_0001
                
                # Convert GPT-5 ID to concept slug
                concept_slug = gpt5_id_to_slug.get(alias_of)
                if not concept_slug:
                    # Try removing c_ prefix
                    if alias_of and alias_of.startswith("c_"):
                        concept_slug = alias_of[2:]
                    else:
                        logger.warning(f"Could not find concept for alias {alias_text} -> {alias_of}")
                        continue
                
                # Find the concept
                concept = service.tag_concepts.find_one({"slug": concept_slug})
                if not concept:
                    # Try by GPT-5 ID
                    mongo_id = gpt5_id_to_mongo_id.get(alias_of)
                    if mongo_id:
                        concept = service.tag_concepts.find_one({"_id": ObjectId(mongo_id)})
                
                if concept:
                    # Check if alias exists
                    existing = service.tag_aliases.find_one({
                        "alias_text": alias_text
                    })
                    
                    if not existing:
                        service.tag_aliases.insert_one({
                            "alias_text": alias_text,
                            "concept_id": concept["_id"],
                            "created_at": datetime.utcnow()
                        })
                        stats["aliases_created"] += 1
                        logger.info(f"Created alias: {alias_text} -> {concept_slug}")
                else:
                    logger.warning(f"Could not find concept {concept_slug} for alias {alias_text}")
                    
            except Exception as e:
                error_msg = f"Failed to create alias {alias_data.get('alias_text')}: {e}"
                logger.error(error_msg)
                stats["errors"].append(error_msg)
        
        # Step 6: Process merge proposals
        logger.info(f"Processing {len(merge_proposals)} merge proposals")
        for proposal in merge_proposals:
            try:
                primary = proposal.get("primary")
                merge_into = proposal.get("merge_into", [])
                
                # Find primary concept
                primary_concept = service.tag_concepts.find_one({"slug": primary})
                if not primary_concept:
                    logger.warning(f"Could not find primary concept {primary}")
                    continue
                
                # Create aliases for all merge candidates
                for variant in merge_into:
                    # Check if this variant already exists as an alias
                    existing = service.tag_aliases.find_one({
                        "alias_text": variant
                    })
                    
                    if not existing:
                        service.tag_aliases.insert_one({
                            "alias_text": variant,
                            "concept_id": primary_concept["_id"],
                            "created_at": datetime.utcnow()
                        })
                        stats["aliases_created"] += 1
                        logger.info(f"Merged {variant} -> {primary}")
                
                stats["merges_processed"] += 1
                
            except Exception as e:
                error_msg = f"Failed to process merge proposal: {e}"
                logger.error(error_msg)
                stats["errors"].append(error_msg)
        
        # Step 7: Remap ALL existing tag instances to new concepts
        logger.info("Remapping all tag instances to new concepts")
        
        # Get all unique tag names from the system
        all_tags = service.tag_instances.distinct("tag_name")
        logger.info(f"Found {len(all_tags)} unique tag names to remap")
        
        # Build a mapping from tag text to concept
        tag_to_concept = {}
        
        # First, add all concept slugs
        for concept in service.tag_concepts.find():
            slug = concept.get("slug")
            if slug:
                tag_to_concept[slug.lower()] = concept["_id"]
                # Also add display name
                display_name = concept.get("display_name")
                if display_name:
                    tag_to_concept[display_name.lower()] = concept["_id"]
        
        # Then add all aliases
        for alias in service.tag_aliases.find():
            alias_text = alias.get("alias_text")
            if alias_text:
                tag_to_concept[alias_text.lower()] = alias["concept_id"]
        
        # Now remap all tag instances
        for tag_name in all_tags:
            if not tag_name:
                continue
                
            # Try to find matching concept
            tag_lower = tag_name.lower()
            concept_id = tag_to_concept.get(tag_lower)
            
            if not concept_id:
                # Try various transformations
                # Remove hyphens and underscores
                normalized = tag_lower.replace("-", "").replace("_", "")
                concept_id = tag_to_concept.get(normalized)
                
                if not concept_id:
                    # Try with spaces
                    with_spaces = tag_lower.replace("-", " ").replace("_", " ")
                    concept_id = tag_to_concept.get(with_spaces)
            
            if concept_id:
                # Update all instances with this tag name
                result = service.tag_instances.update_many(
                    {"tag_name": tag_name},
                    {"$set": {"concept_id": concept_id}}
                )
                if result.modified_count > 0:
                    stats["tags_remapped"] += result.modified_count
                    logger.info(f"Remapped {result.modified_count} instances of '{tag_name}'")
            else:
                logger.warning(f"No concept found for tag '{tag_name}'")
        
        # Return comprehensive results
        response = {
            "success": True,
            "message": "Comprehensive reorganization completed",
            "stats": stats,
            "summary": {
                "total_concepts": service.tag_concepts.count_documents({}),
                "total_aliases": service.tag_aliases.count_documents({}),
                "total_tags": service.tag_instances.count_documents({}),
                "mapped_tags": service.tag_instances.count_documents({"concept_id": {"$ne": None}}),
                "unmapped_tags": service.tag_instances.count_documents({"concept_id": None})
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Comprehensive reorganization complete: {stats}")
        return response
        
    except Exception as e:
        logger.error(f"Failed comprehensive reorganization: {e}")
        raise HTTPException(status_code=500, detail=str(e))