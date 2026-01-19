"""
Service for applying GPT-5 tag reorganization results to MongoDB
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List
from bson import ObjectId
from app.services.concept_only_tag_service import ConceptOnlyTagService

logger = logging.getLogger(__name__)

class TagReorganizationApplyService:
    """Service to apply GPT-5 reorganization results to the database"""
    
    def __init__(self):
        self.concept_service = ConceptOnlyTagService()
        
    def apply_gpt5_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply the GPT-5 reorganization result to the database
        
        Args:
            result: The GPT-5 reorganization result containing concepts, aliases, etc.
            
        Returns:
            Dictionary with application statistics and results
        """
        try:
            logger.info("Starting to apply GPT-5 reorganization results")
            
            # Statistics tracking
            stats = {
                "concepts_created": 0,
                "concepts_updated": 0,
                "aliases_created": 0,
                "hierarchy_links": 0,
                "tags_mapped": 0,
                "errors": []
            }
            
            # Extract data from result
            concepts = result.get("concepts", [])
            aliases = result.get("aliases", [])
            
            logger.info(f"Processing {len(concepts)} concepts and {len(aliases)} aliases")
            
            # Step 1: Create or update all concepts first
            concept_id_map = {}  # Map GPT-5 IDs to MongoDB ObjectIds
            
            for concept_data in concepts:
                try:
                    # Prepare concept for creation/update
                    concept = {
                        "slug": concept_data.get("slug"),
                        "display_name": concept_data.get("display_name"),
                        "description": concept_data.get("description", ""),
                        "status": concept_data.get("status", "active"),
                        "entity_type": concept_data.get("entity_type", "concept"),
                        "icon": concept_data.get("icon"),
                        "color": concept_data.get("color"),
                        "parents": [],  # Will set later
                        "children": [],
                        "updated_at": datetime.now(timezone.utc),
                        "usage_count": concept_data.get("usage_count", 0)
                    }
                    
                    # Check if concept already exists (by slug OR by the GPT ID)
                    existing = self.concept_service.tag_concepts.find_one({
                        "$or": [
                            {"slug": concept["slug"]},
                            {"_id": concept_data.get("id")}  # Check for GPT ID as _id
                        ]
                    })
                    if existing:
                        # Update existing concept, but preserve MongoDB ObjectId if it exists
                        # If the existing concept has a string _id (GPT ID), we need to replace it
                        if isinstance(existing["_id"], str):
                            # Remove old document and create new one with proper ObjectId
                            self.concept_service.tag_concepts.delete_one({"_id": existing["_id"]})
                            concept["created_at"] = existing.get("created_at", datetime.now(timezone.utc))
                            result_doc = self.concept_service.tag_concepts.insert_one(concept)
                            concept_id_map[concept_data.get("id")] = str(result_doc.inserted_id)
                            stats["concepts_created"] += 1
                            logger.info(f"Recreated concept with proper ObjectId: {concept['display_name']}")
                        else:
                            # Update existing concept with proper ObjectId
                            self.concept_service.tag_concepts.update_one(
                                {"_id": existing["_id"]},
                                {"$set": concept}
                            )
                            concept_id_map[concept_data.get("id")] = str(existing["_id"])
                            stats["concepts_updated"] += 1
                            logger.info(f"Updated concept: {concept['display_name']}")
                    else:
                        # Insert new concept with proper MongoDB ObjectId
                        concept["created_at"] = datetime.now(timezone.utc)
                        result_doc = self.concept_service.tag_concepts.insert_one(concept)
                        concept_id_map[concept_data.get("id")] = str(result_doc.inserted_id)
                        stats["concepts_created"] += 1
                        logger.info(f"Created concept: {concept['display_name']}")
                        
                except Exception as e:
                    error_msg = f"Failed to create/update concept {concept_data.get('slug')}: {e}"
                    logger.error(error_msg)
                    stats["errors"].append(error_msg)
            
            # Step 2: Update parent-child relationships
            # First pass: create a map of all concept IDs/slugs to ObjectIds
            all_concept_map = {}
            for concept_data in concepts:
                concept_id = concept_id_map.get(concept_data.get("id"))
                if concept_id:
                    all_concept_map[concept_data.get("id")] = concept_id
                    all_concept_map[concept_data.get("slug")] = concept_id
            
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
                                # Try to get from our concept mapping first
                                parent_id = all_concept_map.get(parent_ref)
                                if parent_id:
                                    parent_ids.append(ObjectId(parent_id))
                                else:
                                    # If parent_ref starts with 'c_', try to find by slug
                                    if parent_ref.startswith('c_'):
                                        # Convert GPT ID to slug format (remove c_ prefix, replace _ with -)
                                        slug_candidates = [
                                            parent_ref[2:].replace('_', '-'),  # c_fundamentals -> fundamentals
                                            parent_ref[2:],  # c_fundamentals -> fundamentals
                                            parent_ref  # keep original
                                        ]
                                        
                                        found = False
                                        for slug_candidate in slug_candidates:
                                            parent_concept = self.concept_service.tag_concepts.find_one({"slug": slug_candidate})
                                            if parent_concept:
                                                parent_ids.append(parent_concept["_id"])
                                                found = True
                                                break
                                        
                                        if not found:
                                            logger.warning(f"Could not find parent {parent_ref} for {concept_data.get('slug')}")
                                    else:
                                        # Check if it's a slug reference
                                        parent_concept = self.concept_service.tag_concepts.find_one({"slug": parent_ref})
                                        if parent_concept:
                                            parent_ids.append(parent_concept["_id"])
                                        else:
                                            logger.warning(f"Could not find parent {parent_ref} for {concept_data.get('slug')}")
                        
                        if parent_ids:
                            # Update this concept's parents
                            self.concept_service.tag_concepts.update_one(
                                {"_id": ObjectId(concept_id)},
                                {"$set": {"parents": parent_ids}}
                            )
                            
                            # Update parent's children
                            for parent_id in parent_ids:
                                self.concept_service.tag_concepts.update_one(
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
                        "created_at": datetime.now(timezone.utc)
                    }
                    
                    # Check if alias already exists
                    existing = self.concept_service.tag_aliases.find_one({
                        "alias_text": alias["alias_text"]
                    })
                    
                    if not existing:
                        self.concept_service.tag_aliases.insert_one(alias)
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
            orphan_tags = list(self.concept_service.tag_instances.find({"concept_id": None}))
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
                    self.concept_service.tag_instances.update_one(
                        {"_id": tag["_id"]},
                        {"$set": {"concept_id": ObjectId(matched_concept_id)}}
                    )
                    stats["tags_mapped"] += 1
                    logger.info(f"Mapped tag '{tag_text}' to concept")
            
            # Return results
            response = {
                "success": True,
                "message": "GPT-5 reorganization results applied successfully",
                "stats": stats,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            if stats["errors"]:
                response["warnings"] = f"Completed with {len(stats['errors'])} errors"
            
            logger.info(f"Applied GPT-5 results: {stats}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to apply GPT-5 results: {e}")
            raise e
    
    def preview_gpt5_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preview what would happen if GPT-5 results were applied
        (Dry-run without making changes)
        
        Args:
            result: The GPT-5 reorganization result
            
        Returns:
            Dictionary with preview statistics
        """
        try:
            concepts = result.get("concepts", [])
            aliases = result.get("aliases", [])
            
            # Count existing vs new concepts
            concepts_to_create = 0
            concepts_to_update = 0
            
            for concept_data in concepts:
                existing = self.concept_service.tag_concepts.find_one({"slug": concept_data.get("slug")})
                if existing:
                    concepts_to_update += 1
                else:
                    concepts_to_create += 1
            
            # Count existing vs new aliases
            aliases_to_create = 0
            for alias_data in aliases:
                existing = self.concept_service.tag_aliases.find_one({
                    "alias_text": alias_data.get("alias_text")
                })
                if not existing:
                    aliases_to_create += 1
            
            # Count orphan tags that could be mapped
            orphan_tags = list(self.concept_service.tag_instances.find({"concept_id": None}))
            tags_to_map = 0
            
            for tag in orphan_tags:
                tag_text = tag.get("tag_name", "").lower()
                
                # Check if this tag would match a concept or alias
                found_match = False
                
                # Check concept matches
                for concept in concepts:
                    if concept.get("slug", "").lower() == tag_text:
                        found_match = True
                        break
                
                # Check alias matches
                if not found_match:
                    for alias in aliases:
                        if alias.get("alias_text", "").lower() == tag_text:
                            found_match = True
                            break
                
                if found_match:
                    tags_to_map += 1
            
            # Count hierarchy changes
            hierarchy_changes = sum(1 for c in concepts if c.get("parents"))
            
            return {
                "preview": {
                    "concepts_to_create": concepts_to_create,
                    "concepts_to_update": concepts_to_update,
                    "aliases_to_create": aliases_to_create,
                    "tags_to_map": tags_to_map,
                    "hierarchy_changes": hierarchy_changes,
                    "total_orphan_tags": len(orphan_tags)
                },
                "summary": {
                    "total_concepts": len(concepts),
                    "total_aliases": len(aliases),
                    "will_create_new": concepts_to_create > 0 or aliases_to_create > 0,
                    "will_update_existing": concepts_to_update > 0,
                    "will_map_orphans": tags_to_map > 0
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to preview GPT-5 results: {e}")
            raise e
