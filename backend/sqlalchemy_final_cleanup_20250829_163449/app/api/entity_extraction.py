"""
API endpoints for entity extraction and annotation management
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from datetime import datetime

from app.models import get_db, SubstackArticle, Tweet
from app.services.entity_extraction_service import EntityExtractionService, EntityExtraction

router = APIRouter()


class ExtractEntitiesRequest(BaseModel):
    text: Optional[str] = None
    article_id: Optional[int] = None
    tweet_id: Optional[str] = None
    use_fast_model: bool = False


class EntitySuggestion(BaseModel):
    id: str
    text: str
    type: str
    confidence: float
    context: str
    normalized: str
    metadata: Dict


class EntityReviewRequest(BaseModel):
    entity_id: str
    action: str  # "accept", "reject", "modify"
    new_type: Optional[str] = None
    new_text: Optional[str] = None


class BulkEntityActionRequest(BaseModel):
    entity_ids: List[str]
    action: str  # "accept_all", "reject_all"
    article_id: Optional[int] = None  # Article ID for context
    entities: Optional[List[Dict]] = None  # Full entity data for processing


class EntityExtractionResponse(BaseModel):
    entities: List[EntitySuggestion]
    stats: Dict[str, Any]
    source: str
    model: str


@router.post("/extract", response_model=EntityExtractionResponse)
def extract_entities(
    request: ExtractEntitiesRequest,
    db: Session = Depends(get_db)
):
    """
    Extract entities from text, article, or tweet
    """
    # Get text based on source
    text = request.text
    source = "direct"
    
    if request.article_id:
        article = db.query(SubstackArticle).filter(
            SubstackArticle.id == request.article_id
        ).first()
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        text = f"{article.title}\n\n{article.content_markdown[:5000]}"  # Limit length
        source = f"article_{article.id}"
    
    elif request.tweet_id:
        tweet = db.query(Tweet).filter(
            Tweet.id == request.tweet_id
        ).first()
        if not tweet:
            raise HTTPException(status_code=404, detail="Tweet not found")
        text = tweet.text
        source = f"tweet_{tweet.id}"
    
    if not text:
        raise HTTPException(status_code=400, detail="No text provided for extraction")
    
    # Initialize service
    service = EntityExtractionService(use_fast_model=request.use_fast_model)
    
    # Extract entities
    entities = service.extract_entities(
        text=text,
        article_id=request.article_id
    )
    
    # Convert to response format
    entity_suggestions = [
        EntitySuggestion(
            id=entity.id,
            text=entity.text,
            type=entity.entity_type,
            confidence=entity.confidence,
            context=entity.context,
            normalized=entity.normalized,
            metadata=entity.metadata
        )
        for entity in entities
    ]
    
    # Calculate statistics
    stats = {
        "total": len(entities),
        "by_type": {},
        "avg_confidence": sum(e.confidence for e in entities) / len(entities) if entities else 0
    }
    
    for entity in entities:
        if entity.entity_type not in stats["by_type"]:
            stats["by_type"][entity.entity_type] = 0
        stats["by_type"][entity.entity_type] += 1
    
    return EntityExtractionResponse(
        entities=entity_suggestions,
        stats=stats,
        source=source,
        model=service.model_name
    )


@router.get("/suggestions/{article_id}")
def get_entity_suggestions(
    article_id: int,
    db: Session = Depends(get_db)
):
    """
    Get cached entity suggestions for an article
    """
    # This would retrieve cached suggestions from database
    # For now, we'll extract them fresh
    article = db.query(SubstackArticle).filter(
        SubstackArticle.id == article_id
    ).first()
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    service = EntityExtractionService(use_fast_model=False)
    entities = service.extract_entities(
        text=f"{article.title}\n\n{article.content_markdown[:5000]}",
        article_id=article_id
    )
    
    return {
        "article_id": article_id,
        "entities": [e.to_dict() for e in entities],
        "extracted_at": datetime.utcnow().isoformat()
    }


@router.post("/review")
def review_entity(
    request: EntityReviewRequest,
    db: Session = Depends(get_db),
    user: str = Query(default="user")
):
    """
    Review and accept/reject/modify an entity suggestion
    """
    # In a real implementation, this would:
    # 1. Find the entity suggestion in a cache/staging table
    # 2. Apply the requested action
    # 3. If accepted, save to ontology
    # 4. Log the action for audit
    
    if request.action == "accept":
        # Create mock entity for demonstration
        entity = EntityExtraction(
            text=request.new_text or "Entity Text",
            entity_type=request.new_type or "person",
            confidence=0.9,
            context="Accepted by user"
        )
        
        service = EntityExtractionService()
        parent_type = request.new_type or "person"
        concept = service.save_entity_to_ontology(db, entity, parent_type, user)
        
        if concept:
            return {
                "status": "accepted",
                "entity_id": request.entity_id,
                "concept_id": concept.id,
                "message": f"Entity saved to ontology under {parent_type}"
            }
        else:
            return {
                "status": "failed",
                "entity_id": request.entity_id,
                "message": "Failed to save entity to ontology"
            }
    
    elif request.action == "reject":
        return {
            "status": "rejected",
            "entity_id": request.entity_id,
            "message": "Entity suggestion rejected"
        }
    
    elif request.action == "modify":
        return {
            "status": "modified",
            "entity_id": request.entity_id,
            "new_type": request.new_type,
            "new_text": request.new_text,
            "message": "Entity suggestion modified"
        }
    
    else:
        raise HTTPException(status_code=400, detail=f"Invalid action: {request.action}")


@router.post("/bulk-action")
def bulk_entity_action(
    request: BulkEntityActionRequest,
    db: Session = Depends(get_db),
    user: str = Query(default="user")
):
    """
    Apply bulk actions to multiple entity suggestions
    """
    results = {
        "total": len(request.entity_ids),
        "processed": 0,
        "failed": 0,
        "action": request.action
    }
    
    if request.action == "accept_all":
        # Process each entity and save to ontology
        service = EntityExtractionService()
        processed_count = 0
        failed_count = 0
        
        # Use article_id from request if provided
        article_id = request.article_id
        
        # If entities data is provided, use it; otherwise try to look up by ID
        if request.entities:
            # Process full entity data
            for entity_data in request.entities:
                try:
                    # Extract entity details
                    entity_text = entity_data.get('text', '')
                    entity_type = entity_data.get('type', '')
                    confidence = entity_data.get('confidence', 0.9)
                    context = entity_data.get('context', '')
                    
                    # Create entity object
                    entity = EntityExtraction(
                        text=entity_text,
                        entity_type=entity_type,
                        confidence=confidence,
                        context=context
                    )
                    
                    # Save entity to ontology as a tag concept
                    concept = service.save_entity_to_ontology(db, entity, entity_type, user)
                    print(f"Created concept: {concept.tag if concept else 'None'} for entity: {entity_text}")
                    
                    if concept and article_id:
                        # Add as tag to the article
                        from app.models import ArticleTag, SubstackArticle
                        
                        # Check if article exists
                        article = db.query(SubstackArticle).filter(
                            SubstackArticle.id == article_id
                        ).first()
                        
                        if article:
                            # Check if tag already exists for this article (case-insensitive)
                            existing_tag = db.query(ArticleTag).filter(
                                ArticleTag.article_id == article_id,
                                func.lower(ArticleTag.tag) == func.lower(concept.tag)
                            ).first()
                            
                            if not existing_tag:
                                # Add the tag to the article
                                new_tag = ArticleTag(
                                    article_id=article_id,
                                    tag=concept.tag,
                                    tag_type="entity"  # Mark as entity-extracted tag
                                )
                                db.add(new_tag)
                                print(f"Added tag '{concept.tag}' to article {article_id}")
                                processed_count += 1
                            else:
                                print(f"Tag '{concept.tag}' already exists on article {article_id}")
                                processed_count += 1  # Already exists, count as processed
                        else:
                            failed_count += 1
                    else:
                        # Just save to ontology without article association
                        if concept:
                            processed_count += 1
                        else:
                            failed_count += 1
                except Exception as e:
                    print(f"Error processing entity: {str(e)}")
                    failed_count += 1
        else:
            # Fallback: just count as processed for now
            processed_count = len(request.entity_ids)
        
        # Commit all changes
        try:
            db.commit()
            results["processed"] = processed_count
            results["failed"] = failed_count
            results["message"] = f"Accepted {processed_count} entities, {failed_count} failed"
        except Exception as e:
            db.rollback()
            results["processed"] = 0
            results["failed"] = len(request.entity_ids)
            results["message"] = f"Failed to save entities: {str(e)}"
    
    elif request.action == "reject_all":
        results["processed"] = len(request.entity_ids)
        results["message"] = f"Rejected {len(request.entity_ids)} entities"
    
    else:
        raise HTTPException(status_code=400, detail=f"Invalid bulk action: {request.action}")
    
    return results


@router.get("/schema")
def get_entity_schema():
    """
    Get the current entity type schema from top_level.json
    """
    import json
    with open('top_level.json', 'r') as f:
        schema = json.load(f)
    
    return {
        "version": schema.get("version"),
        "entity_types": schema.get("entity_types"),
        "extraction_config": schema.get("extraction_config")
    }


@router.post("/validate/{entity_id}")
def validate_entity(
    entity_id: str,
    entity_type: str = Query(...),
    entity_text: str = Query(...),
    context: str = Query(default=""),
    db: Session = Depends(get_db)
):
    """
    Validate an entity extraction using AI
    """
    entity = EntityExtraction(
        text=entity_text,
        entity_type=entity_type,
        confidence=0.8,
        context=context
    )
    
    service = EntityExtractionService()
    is_valid, suggested_type, reasoning = service.validate_entity(entity, context)
    
    return {
        "entity_id": entity_id,
        "valid": is_valid,
        "suggested_type": suggested_type,
        "reasoning": reasoning,
        "original_type": entity_type
    }


@router.get("/stats")
def get_extraction_stats(
    db: Session = Depends(get_db),
    days: int = Query(default=7)
):
    """
    Get statistics about entity extractions
    """
    # This would query actual extraction logs
    # For now, return mock stats
    return {
        "period_days": days,
        "total_extractions": 156,
        "total_entities": 1432,
        "by_type": {
            "person": 234,
            "organisation": 189,
            "model": 156,
            "method": 123,
            "dataset": 89,
            "benchmark": 67,
            "location": 45,
            "event": 34,
            "research-topic": 234,
            "metric": 89
        },
        "by_source": {
            "articles": 892,
            "tweets": 540
        },
        "avg_confidence": 0.82,
        "acceptance_rate": 0.75
    }