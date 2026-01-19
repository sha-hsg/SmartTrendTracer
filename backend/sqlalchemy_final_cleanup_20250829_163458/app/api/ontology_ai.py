"""
API endpoints for AI-powered ontology management
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List, Optional
from pydantic import BaseModel

from app.services.ontology_ai_service import OntologyProposalService

router = APIRouter()

class ProposalRequest(BaseModel):
    tag: str

class BulkProposalRequest(BaseModel):
    limit: int = 100  # Increased default from 20 to 100
    max_limit: int = 200  # Maximum allowed limit

class ApplyProposalRequest(BaseModel):
    proposal: Dict

@router.post("/suggest/tag")
def suggest_for_tag(
    request: ProposalRequest,
):
    """
    Generate AI-powered ontology suggestions for a specific tag
    """
    try:
        service = OntologyProposalService(db)
        proposals = service.generate_proposals_for_tag(request.tag)
        
        # Validate the response
        if not proposals or 'proposals' not in proposals:
            return {
                "tag": request.tag,
                "proposals": [],
                "reasoning": "No suggestions generated - tag may already be well-organized"
            }
        
        return proposals
    except Exception as e:
        import traceback
        print(f"Error in suggest_for_tag: {str(e)}")
        print(traceback.format_exc())
        
        # Return a valid but empty response instead of error
        return {
            "tag": request.tag,
            "proposals": [],
            "reasoning": f"AI analysis temporarily unavailable. Please try again."
        }

@router.post("/suggest/bulk")
def suggest_bulk_organization(
    request: BulkProposalRequest,
):
    """
    Generate AI suggestions for organizing multiple uncategorized tags.
    Default: 100 tags, Maximum: 200 tags
    """
    try:
        # Validate limit
        actual_limit = min(request.limit, 200)  # Cap at 200 for safety
        if actual_limit != request.limit:
            print(f"Requested limit {request.limit} capped at 200")
        
        service = OntologyProposalService(db)
        proposals = service.generate_bulk_proposals(actual_limit)
        return proposals
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate bulk proposals: {str(e)}")

@router.post("/apply")
def apply_proposal(
    request: ApplyProposalRequest,
):
    """
    Apply a specific AI-generated proposal to the ontology
    """
    try:
        service = OntologyProposalService(db)
        result = service.apply_proposal(request.proposal)
        
        if result["success"]:
            # Rebuild mappings after changes
            from app.models import TagMapping
            TagMapping.rebuild_mappings(db)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to apply proposal: {str(e)}")

@router.post("/reset-processed")
def reset_processed_tags():
    """
    Reset the list of processed tags to allow re-processing
    """
    import os
    processed_file = 'data/processed_bulk_tags.json'
    
    try:
        if os.path.exists(processed_file):
            os.remove(processed_file)
            return {"success": True, "message": "Processed tags list has been reset"}
        else:
            return {"success": True, "message": "No processed tags list to reset"}
    except Exception as e:
        return {"success": False, "message": f"Failed to reset: {str(e)}"}

@router.get("/uncategorized")
def get_uncategorized_tags(
    limit: int = 50,
    exclude_processed: bool = True,
):
    """
    Get list of uncategorized tags that need organization
    Can optionally exclude already processed tags
    """
    import os
    import json
    from datetime import datetime, timedelta
    from app.models import TagConcept
    from sqlalchemy import func
    
    # Load processed tags if excluding them
    processed_tags = set()
    if exclude_processed:
        processed_file = 'data/processed_bulk_tags.json'
        if os.path.exists(processed_file):
            try:
                with open(processed_file, 'r') as f:
                    processed_data = json.load(f)
                    if 'timestamp' in processed_data:
                        timestamp = datetime.fromisoformat(processed_data['timestamp'])
                        if datetime.now() - timestamp < timedelta(hours=24):
                            processed_tags = set(processed_data.get('tags', []))
            except:
                pass
    
    query = db.query(TagConcept).filter(
        TagConcept.parent_id.is_(None),
        TagConcept.description == "Auto-imported from existing tags"
    )
    
    if processed_tags:
        query = query.filter(~TagConcept.tag.in_(processed_tags))
    
    # Use random order to show different tags
    uncategorized = query.order_by(func.random()).limit(limit).all()
    
    return {
        "total": len(uncategorized),
        "tags": [
            {
                "id": c.id,
                "tag": c.tag,
                "display_name": c.display_name
            }
            for c in uncategorized
        ]
    }

@router.post("/validate")
def validate_relationship(
    relationship_type: str,
    source: str,
    target: str,
):
    """
    Validate if a proposed relationship makes semantic sense
    """
    try:
        from app.services.ontology_ai_service import OntologyAIService
        service = OntologyAIService()
        result = service.validate_relationship(db, relationship_type, source, target)
        return result
    except Exception as e:
        return {
            "valid": False,
            "confidence": 0,
            "reasoning": f"Validation failed: {str(e)}",
            "alternative": None
        }