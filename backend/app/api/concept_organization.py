"""
Concept Organization API
Organizes unorganized concepts into the hierarchy or identifies them as aliases
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List, Optional
from pydantic import BaseModel
import logging

from app.services.concept_organization_service import ConceptOrganizationService

logger = logging.getLogger(__name__)
router = APIRouter()


class OrganizeConceptRequest(BaseModel):
    """Request model for organizing a concept"""
    concept_id: str
    auto_apply: bool = False


class OrganizeBatchRequest(BaseModel):
    """Request model for organizing multiple concepts"""
    limit: int = 10
    auto_apply: bool = False


class ConceptOrganizationResponse(BaseModel):
    """Response model for concept organization"""
    concept_id: str
    concept_name: str
    is_alias: Optional[bool] = None
    alias_of: Optional[str] = None
    parent_concepts: Optional[List[str]] = None
    entity_type: Optional[str] = None
    description: Optional[str] = None
    reasoning: Optional[str] = None
    applied: Optional[bool] = None
    success: bool
    error: Optional[str] = None


@router.get("/unorganized")
async def get_unorganized_concepts(limit: int = 50) -> Dict:
    """
    Get concepts that need organization
    
    Returns concepts that are:
    - Marked as not organized
    - Need review
    - Root concepts not created by the reorganizer
    """
    try:
        service = ConceptOrganizationService()
        concepts = service.get_unorganized_concepts(limit)
        
        # Add usage count for each concept
        for concept in concepts:
            usage_count = service.db.tag_instances.count_documents(
                {"concept_id": concept["_id"]}
            )
            concept["usage_count"] = usage_count
        
        return {
            "success": True,
            "count": len(concepts),
            "concepts": concepts
        }
    except Exception as e:
        logger.error(f"Error getting unorganized concepts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/organize")
async def organize_concept(request: OrganizeConceptRequest) -> ConceptOrganizationResponse:
    """
    Organize a single concept
    
    Analyzes the concept and determines:
    1. If it's an alias of an existing concept
    2. Where it should be placed in the hierarchy
    3. What entity type it represents
    """
    try:
        service = ConceptOrganizationService()
        result = await service.organize_concept(request.concept_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        # Apply if requested
        if request.auto_apply:
            applied = await service.apply_organization(
                request.concept_id,
                result["organization"]
            )
            result["applied"] = applied
        
        # Format response
        org = result.get("organization", {})
        return ConceptOrganizationResponse(
            concept_id=result["concept_id"],
            concept_name=result["concept_name"],
            is_alias=org.get("is_alias"),
            alias_of=org.get("alias_of"),
            parent_concepts=org.get("parent_concepts"),
            entity_type=org.get("entity_type"),
            description=org.get("description"),
            reasoning=org.get("reasoning"),
            applied=result.get("applied"),
            success=result["success"],
            error=result.get("error")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error organizing concept: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/organize-batch")
async def organize_batch(
    request: OrganizeBatchRequest,
    background_tasks: BackgroundTasks
) -> Dict:
    """
    Organize multiple concepts in a batch
    
    Can be run in the background for larger batches
    """
    try:
        service = ConceptOrganizationService()
        
        # For small batches, process immediately
        if request.limit <= 5:
            results = await service.organize_batch(
                limit=request.limit,
                auto_apply=request.auto_apply
            )
            
            return {
                "success": True,
                "processed": len(results),
                "results": results
            }
        
        # For larger batches, run in background
        background_tasks.add_task(
            service.organize_batch,
            limit=request.limit,
            auto_apply=request.auto_apply
        )
        
        return {
            "success": True,
            "message": f"Organizing {request.limit} concepts in background",
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Error organizing batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/apply-organization/{concept_id}")
async def apply_organization(concept_id: str, organization: Dict) -> Dict:
    """
    Apply an organization decision to a concept
    
    This can be used to manually apply organization after review
    """
    try:
        service = ConceptOrganizationService()
        success = await service.apply_organization(concept_id, organization)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to apply organization")
        
        return {
            "success": True,
            "message": f"Organization applied to concept {concept_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying organization: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_organization_stats() -> Dict:
    """Get statistics about concept organization"""
    try:
        service = ConceptOrganizationService()
        
        # Count different states
        total = service.db.tag_concepts_v2.count_documents({})
        organized = service.db.tag_concepts_v2.count_documents({"is_organized": True})
        unorganized = service.db.tag_concepts_v2.count_documents(
            {"$or": [
                {"is_organized": False},
                {"needs_review": True}
            ]}
        )
        
        # Count aliases
        aliases = service.db.tag_aliases_v2.count_documents({})
        
        # Count orphan tags (instances without concepts)
        orphans = service.db.tag_instances.count_documents({"concept_id": None})
        
        return {
            "success": True,
            "stats": {
                "total_concepts": total,
                "organized_concepts": organized,
                "unorganized_concepts": unorganized,
                "aliases": aliases,
                "orphan_tags": orphans,
                "organization_percentage": (organized / total * 100) if total > 0 else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))