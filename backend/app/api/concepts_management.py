"""
API endpoints for concept management and organization
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.database.mongodb import get_database
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["concepts"]
)

# MongoDB connection helpers
def get_concepts_collection():
    """Get concepts collection"""
    return get_database().tag_concepts_v2


def get_instances_collection():
    """Get instances collection"""
    return get_database().tag_instances

@router.get("/unorganized")
async def get_unorganized_concepts():
    """Get concepts that haven't been organized into the hierarchy yet"""
    try:
        concepts_col = get_concepts_collection()
        instances_col = get_instances_collection()
        
        # Find concepts that are:
        # 1. Auto-generated
        # 2. Have no parents (root level but not intentionally)
        # 3. Not verified
        unorganized = list(concepts_col.find({
            "auto_generated": True,
            "parents": [],
            "verified": {"$ne": True},
            "entity_type": {"$in": [None, "concept", "topic"]}  # Exclude named entities
        }))
        
        result = []
        for concept in unorganized:
            # Count usage
            concept_id = str(concept["_id"])
            usage_count = instances_col.count_documents({"concept_id": concept_id})
            
            result.append({
                "_id": concept_id,
                "display_name": concept["display_name"],
                "slug": concept["slug"],
                "description": concept.get("description"),
                "usage_count": usage_count,
                "created_at": str(concept.get("created_at", ""))
            })
        
        # Sort by usage count (most used first)
        result.sort(key=lambda x: x["usage_count"], reverse=True)
        
        return result
    except Exception as e:
        logger.error(f"Error fetching unorganized concepts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/organization-stats")
async def get_organization_stats():
    """Get statistics about concept organization"""
    try:
        concepts_col = get_concepts_collection()
        
        # Total unorganized
        unorganized_count = concepts_col.count_documents({
            "auto_generated": True,
            "parents": [],
            "verified": {"$ne": True},
            "entity_type": {"$in": [None, "concept", "topic"]}
        })
        
        # Organized today
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        organized_today = concepts_col.count_documents({
            "verified": True,
            "updated_at": {"$gte": today}
        })
        
        # Organized this week
        week_ago = datetime.now() - timedelta(days=7)
        organized_this_week = concepts_col.count_documents({
            "verified": True,
            "updated_at": {"$gte": week_ago}
        })
        
        # Total organized (verified concepts)
        total_organized = concepts_col.count_documents({
            "verified": True
        })
        
        return {
            "unorganized_count": unorganized_count,
            "organized_today": organized_today,
            "organized_this_week": organized_this_week,
            "total_organized": total_organized
        }
    except Exception as e:
        logger.error(f"Error fetching organization stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/suggest-organization/{concept_id}")
async def suggest_organization(concept_id: str):
    """Get AI suggestion for organizing a concept using the LLM service"""
    try:
        # Import the concept organization service
        from app.services.concept_organization_service import ConceptOrganizationService
        
        # Use the existing service which has proper LLM integration
        service = ConceptOrganizationService()
        result = await service.organize_concept(concept_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to organize concept"))
        
        # Format the response to match what the frontend expects
        org = result.get("organization", {})
        
        # Find the parent concept details if it exists
        parent_concept_name = None
        parent_concept_id = None
        
        if org.get("parent_concepts") and len(org["parent_concepts"]) > 0:
            parent_id = org["parent_concepts"][0]
            concepts_col = get_concepts_collection()
            
            # Try to find parent concept
            try:
                if len(parent_id) == 24:
                    parent = concepts_col.find_one({"_id": ObjectId(parent_id)})
                else:
                    parent = concepts_col.find_one({"id": parent_id})
                    
                if parent:
                    parent_concept_name = parent.get("display_name")
                    parent_concept_id = str(parent.get("_id", parent.get("id")))
            except:
                parent_concept_name = parent_id  # Use ID as fallback
                parent_concept_id = parent_id
        
        suggestion = {
            "is_alias": org.get("is_alias", False),
            "parent_concept": parent_concept_id,
            "parent_concept_name": parent_concept_name or org.get("alias_of"),
            "confidence": 0.85,  # Default confidence
            "reasoning": org.get("reasoning", ""),
            "entity_type": org.get("entity_type"),
            "description": org.get("description")
        }
        
        return suggestion
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error suggesting organization: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/apply-organization/{concept_id}")
async def apply_organization(concept_id: str, suggestion: Dict[str, Any]):
    """Apply the organization suggestion to a concept"""
    try:
        from app.services.concept_organization_service import ConceptOrganizationService
        
        # Get the suggestion data from the request body
        suggestion_data = suggestion.get("suggestion", suggestion)
        
        # Create the organization structure expected by the service
        organization = {
            "is_alias": suggestion_data.get("is_alias", False),
            "alias_of": suggestion_data.get("parent_concept_name") if suggestion_data.get("is_alias") else None,
            "parent_concepts": [suggestion_data.get("parent_concept")] if suggestion_data.get("parent_concept") else [],
            "entity_type": suggestion_data.get("entity_type"),
            "description": suggestion_data.get("description"),
            "reasoning": suggestion_data.get("reasoning")
        }
        
        # Use the service to apply the organization
        service = ConceptOrganizationService()
        success = await service.apply_organization(concept_id, organization)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to apply organization")
        
        # Also mark the concept as organized
        concepts_col = get_concepts_collection()
        try:
            oid = ObjectId(concept_id)
        except:
            oid = concept_id
        
        concepts_col.update_one(
            {"_id": oid},
            {"$set": {
                "is_organized": True,
                "verified": True,
                "needs_review": False,
                "organization_updated_at": datetime.now()
            }}
        )
        
        return {"success": True, "message": "Concept organized successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying organization: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/concepts")
async def create_concept(concept_data: Dict[str, Any]):
    """Create a new concept"""
    try:
        concepts_col = get_concepts_collection()
        
        # Prepare concept document
        new_concept = {
            "slug": concept_data.get("slug"),
            "display_name": concept_data.get("display_name"),
            "description": concept_data.get("description"),
            "entity_type": concept_data.get("entity_type", "concept"),
            "parents": concept_data.get("parents", []),
            "children": [],
            "created_at": datetime.now(),
            "created_by": "user",
            "auto_generated": False,
            "verified": True
        }
        
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
        
        return {"success": True, "id": str(result.inserted_id)}
    except Exception as e:
        logger.error(f"Error creating concept: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/concepts/{concept_id}")
async def update_concept(concept_id: str, concept_data: Dict[str, Any]):
    """Update an existing concept"""
    try:
        concepts_col = get_concepts_collection()
        
        try:
            oid = ObjectId(concept_id)
        except:
            oid = concept_id
        
        # Update the concept
        update_data = {
            "display_name": concept_data.get("display_name"),
            "description": concept_data.get("description"),
            "entity_type": concept_data.get("entity_type"),
            "updated_at": datetime.now()
        }
        
        # Remove None values
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
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
async def delete_concept(concept_id: str):
    """Delete a concept"""
    try:
        concepts_col = get_concepts_collection()
        
        try:
            oid = ObjectId(concept_id)
        except:
            oid = concept_id
        
        # Remove from any parent's children
        concept = concepts_col.find_one({"_id": oid})
        if concept and concept.get("parents"):
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

@router.post("/batch-reorganize")
async def batch_reorganize_concepts(limit: int = 10, auto_apply: bool = False):
    """
    Batch reorganize multiple unorganized concepts using LLM
    
    Args:
        limit: Number of concepts to process (default 10, max 50)
        auto_apply: Whether to automatically apply suggestions
    """
    try:
        from app.services.concept_organization_service import ConceptOrganizationService
        
        # Limit to prevent excessive API calls
        limit = min(limit, 50)
        
        service = ConceptOrganizationService()
        
        # Get unorganized concepts
        unorganized = service.get_unorganized_concepts(limit)
        
        results = []
        success_count = 0
        error_count = 0
        
        for concept in unorganized:
            concept_id = concept["_id"]
            
            try:
                # Get organization suggestion
                result = await service.organize_concept(concept_id)
                
                if result.get("success"):
                    org = result.get("organization", {})
                    
                    # Apply if requested
                    if auto_apply:
                        applied = await service.apply_organization(concept_id, org)
                        result["applied"] = applied
                        if applied:
                            # Mark as organized
                            concepts_col = get_concepts_collection()
                            concepts_col.update_one(
                                {"_id": ObjectId(concept_id)},
                                {"$set": {
                                    "is_organized": True,
                                    "verified": True,
                                    "needs_review": False,
                                    "organization_updated_at": datetime.now()
                                }}
                            )
                    
                    results.append({
                        "concept_id": concept_id,
                        "concept_name": concept["display_name"],
                        "success": True,
                        "organization": org,
                        "applied": result.get("applied", False)
                    })
                    success_count += 1
                else:
                    results.append({
                        "concept_id": concept_id,
                        "concept_name": concept["display_name"],
                        "success": False,
                        "error": result.get("error", "Unknown error")
                    })
                    error_count += 1
                    
            except Exception as e:
                logger.error(f"Error processing concept {concept_id}: {e}")
                results.append({
                    "concept_id": concept_id,
                    "concept_name": concept.get("display_name", "Unknown"),
                    "success": False,
                    "error": str(e)
                })
                error_count += 1
        
        return {
            "success": True,
            "processed": len(results),
            "success_count": success_count,
            "error_count": error_count,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error in batch reorganization: {e}")
        raise HTTPException(status_code=500, detail=str(e))
