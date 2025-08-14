"""
API endpoints for tag reorganization using Gemini 2.5 Pro
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
import json
import logging
import time

from app.models import get_db
from app.services.tag_reorganization_service import (
    TagReorganizationService, 
    TaxonomyReorganization,
    TagNode
)

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


router = APIRouter()


class ReorganizationRequest(BaseModel):
    """Request model for reorganization"""
    include_context: bool = True
    max_samples_per_tag: int = 3
    confidence_threshold: float = 0.7


class ApprovalRequest(BaseModel):
    """Request model for applying reorganization changes"""
    proposal_id: str
    approved_changes: Dict[str, bool]
    modifications: Optional[Dict[str, Any]] = None


class TagNodeUpdate(BaseModel):
    """Model for updating a tag node"""
    display_name: Optional[str] = None
    description: Optional[str] = None
    parent: Optional[str] = None
    synonyms: Optional[List[str]] = None
    color: Optional[str] = None
    icon: Optional[str] = None


# Store proposals temporarily (in production, use Redis or database)
_proposals_cache = {}


@router.get("/current-structure")
async def get_current_tag_structure(db: Session = Depends(get_db)):
    """Get the current tag structure with all context"""
    service = TagReorganizationService(db)
    structure = service.get_all_tags_with_context()
    
    return {
        "tags": structure['tags'],
        "statistics": structure['statistics'],
        "total_tags": structure['statistics']['total_tags']
    }


@router.post("/generate-proposal")
async def generate_reorganization_proposal(
    request: ReorganizationRequest,
    db: Session = Depends(get_db)
):
    """Generate a comprehensive reorganization proposal using Gemini 2.5 Pro"""
    start_time = time.time()
    logger.info("=== API: Generate Proposal Request Received ===")
    logger.debug(f"Request params: include_context={request.include_context}, "
                f"max_samples={request.max_samples_per_tag}, "
                f"threshold={request.confidence_threshold}")
    
    try:
        logger.info("Creating TagReorganizationService...")
        service = TagReorganizationService(db)
        
        # Generate the proposal
        logger.info("Calling service to generate proposal...")
        proposal = service.generate_reorganization_proposal()
        
        # Store in cache for later approval
        proposal_id = f"prop_{proposal.created_at.replace(':', '-')}"
        _proposals_cache[proposal_id] = proposal
        logger.info(f"Proposal cached with ID: {proposal_id}")
        
        # Convert to dict for JSON response
        response = {
            "proposal_id": proposal_id,
            "version": proposal.version,
            "created_at": proposal.created_at,
            "model_used": proposal.model_used,
            "total_tags": proposal.total_tags,
            "confidence_score": proposal.confidence_score,
            "reasoning": proposal.reasoning,
            "statistics": proposal.statistics,
            "root_categories": proposal.root_categories,
            "hierarchy": {k: {
                "name": v.name,
                "display_name": v.display_name,
                "description": v.description,
                "level": v.level,
                "parent": v.parent,
                "children": v.children,
                "synonyms": v.synonyms,
                "usage_count": v.usage_count,
                "color": v.color,
                "icon": v.icon
            } for k, v in proposal.hierarchy.items()},
            "merge_proposals": proposal.merge_proposals,
            "deprecated_tags": proposal.deprecated_tags,
            "new_tags_suggested": [{
                "name": tag.name,
                "display_name": tag.display_name,
                "description": tag.description
            } for tag in proposal.new_tags_suggested]
        }
        
        total_duration = time.time() - start_time
        logger.info(f"=== API: Proposal Generated Successfully in {total_duration:.2f} seconds ===")
        logger.debug(f"Response contains {len(proposal.hierarchy)} hierarchy items")
        
        return response
        
    except Exception as e:
        error_duration = time.time() - start_time
        logger.error(f"=== API ERROR: Failed to generate proposal after {error_duration:.2f} seconds ===")
        logger.error(f"Error: {e}")
        
        import traceback
        logger.debug(f"Traceback:\n{traceback.format_exc()}")
        
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/proposal/{proposal_id}")
async def get_proposal(proposal_id: str):
    """Get a specific proposal by ID"""
    if proposal_id not in _proposals_cache:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    proposal = _proposals_cache[proposal_id]
    
    return {
        "proposal_id": proposal_id,
        "version": proposal.version,
        "created_at": proposal.created_at,
        "hierarchy": {k: {
            "name": v.name,
            "display_name": v.display_name,
            "description": v.description,
            "level": v.level,
            "parent": v.parent,
            "children": v.children,
            "synonyms": v.synonyms,
            "usage_count": v.usage_count,
            "color": v.color,
            "icon": v.icon
        } for k, v in proposal.hierarchy.items()},
        "statistics": proposal.statistics
    }


@router.put("/proposal/{proposal_id}/node/{node_name}")
async def update_proposal_node(
    proposal_id: str,
    node_name: str,
    update: TagNodeUpdate
):
    """Update a specific node in the proposal"""
    if proposal_id not in _proposals_cache:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    proposal = _proposals_cache[proposal_id]
    
    if node_name not in proposal.hierarchy:
        raise HTTPException(status_code=404, detail="Node not found in proposal")
    
    node = proposal.hierarchy[node_name]
    
    # Update fields if provided
    if update.display_name is not None:
        node.display_name = update.display_name
    if update.description is not None:
        node.description = update.description
    if update.parent is not None:
        # Update parent and adjust hierarchy
        old_parent = node.parent
        node.parent = update.parent
        
        # Update children lists
        if old_parent and old_parent in proposal.hierarchy:
            proposal.hierarchy[old_parent].children.remove(node_name)
        if update.parent and update.parent in proposal.hierarchy:
            proposal.hierarchy[update.parent].children.append(node_name)
    
    if update.synonyms is not None:
        node.synonyms = update.synonyms
    if update.color is not None:
        node.color = update.color
    if update.icon is not None:
        node.icon = update.icon
    
    return {"status": "updated", "node": {
        "name": node.name,
        "display_name": node.display_name,
        "description": node.description,
        "parent": node.parent,
        "synonyms": node.synonyms,
        "color": node.color,
        "icon": node.icon
    }}


@router.post("/proposal/{proposal_id}/apply")
async def apply_reorganization(
    proposal_id: str,
    approval: ApprovalRequest,
    db: Session = Depends(get_db)
):
    """Apply the approved reorganization changes"""
    start_time = time.time()
    logger.info(f"=== API: Apply Reorganization Request Received ===")
    logger.info(f"Proposal ID: {proposal_id}")
    
    if proposal_id not in _proposals_cache:
        logger.error(f"Proposal {proposal_id} not found in cache")
        logger.debug(f"Available proposals: {list(_proposals_cache.keys())}")
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    proposal = _proposals_cache[proposal_id]
    logger.info(f"Found proposal with {len(proposal.hierarchy)} hierarchy items")
    
    # Log approval details
    if approval.approved_changes:
        approved_count = sum(1 for v in approval.approved_changes.values() if v)
        logger.info(f"Approved changes: {approved_count} out of {len(approval.approved_changes)}")
    else:
        logger.info("No specific approvals provided, will apply all changes")
    
    service = TagReorganizationService(db)
    
    try:
        # Apply the changes
        logger.info("Calling service to apply reorganization...")
        results = service.apply_reorganization(proposal, approval.approved_changes)
        
        # Remove from cache after applying
        if results.get('success', False) and not results.get('errors'):
            del _proposals_cache[proposal_id]
            logger.info(f"Proposal {proposal_id} removed from cache after successful application")
        else:
            logger.warning(f"Keeping proposal {proposal_id} in cache due to errors or partial application")
        
        total_duration = time.time() - start_time
        logger.info(f"=== API: Apply completed in {total_duration:.2f} seconds ===")
        logger.info(f"Results: {results.get('message', 'No message')}")
        
        return {
            "status": "applied" if results.get('success', False) else "partial",
            "results": results
        }
        
    except Exception as e:
        error_duration = time.time() - start_time
        logger.error(f"=== API ERROR: Failed to apply reorganization after {error_duration:.2f} seconds ===")
        logger.error(f"Error: {e}")
        
        import traceback
        logger.debug(f"Traceback:\n{traceback.format_exc()}")
        
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/proposal/{proposal_id}/export")
async def export_proposal(
    proposal_id: str,
    format: str = Query("json", description="Export format: json, markdown, csv")
):
    """Export the proposal in various formats"""
    if proposal_id not in _proposals_cache:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    proposal = _proposals_cache[proposal_id]
    service = TagReorganizationService(None)  # No DB needed for export
    
    try:
        exported = service.export_taxonomy(proposal, format)
        
        if format == "json":
            return json.loads(exported)
        else:
            return {
                "format": format,
                "content": exported
            }
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/proposal/{proposal_id}")
async def delete_proposal(proposal_id: str):
    """Delete a proposal from cache"""
    if proposal_id not in _proposals_cache:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    del _proposals_cache[proposal_id]
    return {"status": "deleted", "proposal_id": proposal_id}


@router.get("/proposals")
async def list_proposals():
    """List all cached proposals"""
    proposals = []
    for prop_id, proposal in _proposals_cache.items():
        proposals.append({
            "proposal_id": prop_id,
            "created_at": proposal.created_at,
            "total_tags": proposal.total_tags,
            "confidence_score": proposal.confidence_score,
            "statistics": proposal.statistics
        })
    
    return {"proposals": proposals, "total": len(proposals)}


class ImportRequest(BaseModel):
    """Request model for importing a tag hierarchy"""
    hierarchy: Dict[str, Any]
    clear_existing: bool = False
    dry_run: bool = False
    merge_strategy: str = "replace"  # "replace", "merge", or "append"


@router.post("/import")
async def import_tag_hierarchy(
    import_request: ImportRequest,
    db: Session = Depends(get_db)
):
    """
    Import a tag hierarchy to replace or merge with the current ontology
    
    Parameters:
    - hierarchy: The tag hierarchy in the same format as export
    - clear_existing: Whether to clear all existing tags before import
    - dry_run: If true, validate and return what would be changed without applying
    - merge_strategy: How to handle existing tags
        - "replace": Replace existing tags with new definitions
        - "merge": Merge new definitions with existing ones
        - "append": Only add new tags, skip existing ones
    """
    start_time = time.time()
    logger.info(f"=== API: Import Tag Hierarchy Request Received ===")
    logger.info(f"Import strategy: {import_request.merge_strategy}, Clear existing: {import_request.clear_existing}, Dry run: {import_request.dry_run}")
    
    try:
        service = TagReorganizationService(db)
        
        # Convert imported hierarchy to TagNode objects
        imported_hierarchy = {}
        for tag_name, tag_data in import_request.hierarchy.items():
            imported_hierarchy[tag_name] = TagNode(
                name=tag_name,
                display_name=tag_data.get("display_name", tag_name),
                description=tag_data.get("description"),
                level=tag_data.get("level", 0),
                parent=tag_data.get("parent"),
                children=tag_data.get("children", []),
                synonyms=tag_data.get("synonyms", []),
                usage_count=tag_data.get("usage_count", 0),
                color=tag_data.get("color"),
                icon=tag_data.get("icon")
            )
        
        # Create a TaxonomyReorganization object from the import
        import_proposal = TaxonomyReorganization(
            version="imported",
            created_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
            model_used="imported",
            total_tags=len(imported_hierarchy),
            hierarchy=imported_hierarchy,
            root_categories=[k for k, v in imported_hierarchy.items() if not v.parent],
            deprecated_tags=[],
            merge_proposals=[],
            new_tags_suggested=[],
            confidence_score=1.0,
            reasoning="Imported hierarchy",
            statistics={
                "imported_tags": len(imported_hierarchy),
                "root_categories": len([k for k, v in imported_hierarchy.items() if not v.parent])
            }
        )
        
        if import_request.dry_run:
            # Just validate and return what would be changed
            current_structure = service.get_all_tags_with_context()
            
            changes = {
                "would_add": [],
                "would_update": [],
                "would_skip": [],
                "would_clear": import_request.clear_existing
            }
            
            for tag_name in imported_hierarchy:
                if tag_name in current_structure['tags']:
                    if import_request.merge_strategy == "replace" or import_request.merge_strategy == "merge":
                        changes["would_update"].append(tag_name)
                    else:  # append
                        changes["would_skip"].append(tag_name)
                else:
                    changes["would_add"].append(tag_name)
            
            duration = time.time() - start_time
            logger.info(f"=== API: Dry run completed in {duration:.2f} seconds ===")
            
            return {
                "status": "dry_run",
                "changes": changes,
                "total_tags": len(imported_hierarchy),
                "duration": duration
            }
        
        else:
            # Actually apply the import
            if import_request.clear_existing:
                # Clear existing tag concepts (be careful with this!)
                from app.models.tag_ontology import TagConcept, TagSynonym
                db.query(TagSynonym).delete()
                db.query(TagConcept).delete()
                db.commit()
                logger.info("Cleared existing tag ontology")
            
            # Apply the import based on merge strategy
            if import_request.merge_strategy == "append":
                # Only add new tags
                current_structure = service.get_all_tags_with_context()
                filtered_hierarchy = {
                    k: v for k, v in imported_hierarchy.items()
                    if k not in current_structure['tags']
                }
                import_proposal.hierarchy = filtered_hierarchy
            
            # Apply the imported hierarchy
            results = service.apply_reorganization(import_proposal, None)
            
            duration = time.time() - start_time
            logger.info(f"=== API: Import completed in {duration:.2f} seconds ===")
            
            return {
                "status": "imported" if results.get('success', False) else "failed",
                "results": results,
                "duration": duration
            }
    
    except Exception as e:
        error_duration = time.time() - start_time
        logger.error(f"=== API ERROR: Import failed after {error_duration:.2f} seconds ===")
        logger.error(f"Error: {e}")
        
        import traceback
        logger.debug(f"Traceback:\n{traceback.format_exc()}")
        
        raise HTTPException(status_code=500, detail=str(e))