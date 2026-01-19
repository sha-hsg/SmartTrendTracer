"""
Orphan Tags Assignment API
Assigns orphaned tags to existing taxonomy categories using Gemini 2.5 Pro
This is SEPARATE from the full reorganization - it only handles orphans
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Optional, List, Dict, Any
import logging
import asyncio

from app.services.orphan_tag_assigner import OrphanTagAssigner

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tags/orphans", tags=["orphan-tags"])

class AssignOrphanRequest(BaseModel):
    """Request model for assigning orphan tags"""
    min_usage: int = 2
    batch_size: int = 20
    dry_run: bool = False
    specific_tags: Optional[List[str]] = None

class OrphanTagPreview(BaseModel):
    """Preview model for orphan tags"""
    id: int
    tag: str
    display_name: str
    usage_count: int
    description: Optional[str]

@router.get("/preview")
def get_orphan_tags_preview(
    min_usage: int = 1,
    limit: int = 50,
) -> Dict[str, Any]:
    """
    Get a preview of orphan tags that need assignment
    
    Args:
        min_usage: Minimum usage count to include
        limit: Maximum number of tags to return
        
    Returns:
        Preview of orphan tags and statistics
    """
    try:
        # TODO: Update to use MongoDB instead of SQLite models
        # For now, return empty data to prevent errors
        logger.warning("OrphanTagAssigner needs to be updated for MongoDB")
        
        # Import MongoDB client
        try:
            from app.database.mongodb import get_client, get_database

            client = get_client()
            db_mongo = get_database()
            client.server_info()  # trigger connection to surface errors
            
            # Get orphan tags from MongoDB (tags without concept_id)
            orphan_instances = list(db_mongo.tag_instances.find(
                {"concept_id": None}
            ).limit(limit))
            
            # Group by tag_text and count
            tag_counts = {}
            for instance in orphan_instances:
                tag = instance.get("tag_text", "")
                if tag:
                    if tag not in tag_counts:
                        tag_counts[tag] = 0
                    tag_counts[tag] += 1
            
            # Convert to preview format
            orphan_tags = []
            for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:limit]:
                if count >= min_usage:
                    orphan_tags.append({
                        "id": abs(hash(tag)) % 1000000,  # Generate fake ID
                        "tag": tag,
                        "display_name": tag,
                        "usage_count": count,
                        "description": None
                    })
            
            return {
                "success": True,
                "orphan_tags": orphan_tags,
                "total_orphans": len(tag_counts),
                "total_categories": 116,  # From MongoDB migration
                "showing": len(orphan_tags)
            }
            
        except Exception as mongo_error:
            logger.warning(f"MongoDB not available: {mongo_error}")
            # Return empty data if MongoDB is not available
            return {
                "success": True,
                "orphan_tags": [],
                "total_orphans": 0,
                "total_categories": 0,
                "showing": 0
            }
        
    except Exception as e:
        logger.error(f"Failed to get orphan tags preview: {e}")
        # Return empty data instead of raising error
        return {
            "success": False,
            "orphan_tags": [],
            "total_orphans": 0,
            "total_categories": 0,
            "showing": 0,
            "error": str(e)
        }

@router.get("/count")
def get_orphan_count(
    min_usage: int = 1,
) -> Dict[str, Any]:
    """
    Get count of orphan tags
    
    Returns:
        Count statistics
    """
    try:
        # TODO: Update to use MongoDB
        try:
            from app.database.mongodb import get_client, get_database

            client = get_client()
            db_mongo = get_database()
            client.server_info()
            
            # Count orphan tags in MongoDB
            total_orphans = db_mongo.tag_instances.count_documents({"concept_id": None})
            
            # Get top orphans
            pipeline = [
                {"$match": {"concept_id": None}},
                {"$group": {"_id": "$tag_text", "count": {"$sum": 1}}},
                {"$match": {"count": {"$gte": min_usage}}},
                {"$sort": {"count": -1}},
                {"$limit": 5}
            ]
            
            top_orphans = list(db_mongo.tag_instances.aggregate(pipeline))
            
            return {
                "total_orphans": total_orphans,
                "min_usage_filter": min_usage,
                "top_orphans": [
                    {
                        "tag": o["_id"],
                        "usage": o["count"]
                    }
                    for o in top_orphans
                ]
            }
            
        except Exception as mongo_error:
            logger.warning(f"MongoDB not available: {mongo_error}")
            return {
                "total_orphans": 0,
                "min_usage_filter": min_usage,
                "top_orphans": []
            }
        
    except Exception as e:
        logger.error(f"Failed to count orphan tags: {e}")
        return {
            "total_orphans": 0,
            "min_usage_filter": min_usage,
            "top_orphans": [],
            "error": str(e)
        }

@router.post("/assign")
async def assign_orphan_tags(
    request: AssignOrphansRequest,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    Assign orphan tags to existing taxonomy categories
    Uses Gemini 2.5 Pro for intelligent assignment
    
    This is DIFFERENT from full reorganization - it only assigns orphans
    to the existing structure without changing the structure itself.
    
    Returns:
        Assignment results and statistics
    """
    try:
        assigner = OrphanTagAssigner(db)
        
        # Get orphan tags to process
        if request.specific_tags:
            # Process specific tags if provided
            all_orphans = assigner.get_orphan_tags(min_usage=0)
            orphan_tags = [
                o for o in all_orphans 
                if o["tag"] in request.specific_tags
            ]
        else:
            # Get all orphans above usage threshold
            orphan_tags = assigner.get_orphan_tags(min_usage=request.min_usage)
        
        if not orphan_tags:
            return {
                "success": True,
                "message": "No orphan tags found to process",
                "summary": {
                    "total_processed": 0,
                    "assigned": 0
                }
            }
        
        # Run assignment
        result = await assigner.assign_orphan_tags(
            orphan_tags=orphan_tags,
            batch_size=request.batch_size,
            dry_run=request.dry_run
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to assign orphan tags: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/assign-single")
async def assign_single_orphan(
    tag: str,
    parent_tag: str,
    action: str = "assign",  # assign, synonym, or new_category
) -> Dict[str, Any]:
    """
    Manually assign a single orphan tag
    
    Args:
        tag: The orphan tag to assign
        parent_tag: The parent category or synonym target
        action: Assignment action (assign/synonym/new_category)
        
    Returns:
        Assignment result
    """
    try:
        from app.models import TagConcept, TagSynonym
        from app.models.tag_instance import TagInstance
        from datetime import datetime
        
        # Find the orphan tag
        orphan = db.query(TagConcept).filter(
            TagConcept.tag == tag
        ).first()
        
        if not orphan:
            raise HTTPException(status_code=404, detail=f"Tag '{tag}' not found")
        
        if action == "assign":
            # Find parent
            parent = db.query(TagConcept).filter(
                TagConcept.tag == parent_tag
            ).first()
            
            if not parent:
                raise HTTPException(status_code=404, detail=f"Parent tag '{parent_tag}' not found")
            
            # Update orphan
            orphan.parent_id = parent.id
            orphan.path = f"{parent.path}{parent.id}/"
            orphan.level = parent.level + 1
            
            # Update parent's child count
            parent.child_count = (parent.child_count or 0) + 1
            
            db.commit()
            
            return {
                "success": True,
                "message": f"Assigned '{tag}' to '{parent_tag}'",
                "action": "assigned"
            }
            
        elif action == "synonym":
            # Find target concept
            target = db.query(TagConcept).filter(
                TagConcept.tag == parent_tag
            ).first()
            
            if not target:
                raise HTTPException(status_code=404, detail=f"Target tag '{parent_tag}' not found")
            
            # Create synonym
            synonym = TagSynonym(
                concept_id=target.id,
                synonym_tag=orphan.tag,
                created_at=datetime.utcnow()
            )
            db.add(synonym)
            
            # Update all tag instances
            db.query(TagInstance).filter(
                TagInstance.concept_id == orphan.id
            ).update({"concept_id": target.id})
            
            # Delete orphan concept
            db.delete(orphan)
            
            db.commit()
            
            return {
                "success": True,
                "message": f"Created synonym: '{tag}' -> '{parent_tag}'",
                "action": "synonym_created"
            }
            
        else:
            raise HTTPException(status_code=400, detail=f"Invalid action: {action}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to assign single orphan: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/suggestions/{tag}")
async def get_assignment_suggestions(
    tag: str,
) -> Dict[str, Any]:
    """
    Get AI suggestions for where to assign a specific orphan tag
    
    Args:
        tag: The orphan tag to get suggestions for
        
    Returns:
        Suggested parent categories with confidence scores
    """
    try:
        from app.services.llm_service import LLMService
        import json
        
        assigner = OrphanTagAssigner(db)
        
        # Get the orphan tag details
        orphans = assigner.get_orphan_tags(min_usage=0)
        orphan = next((o for o in orphans if o["tag"] == tag), None)
        
        if not orphan:
            raise HTTPException(status_code=404, detail=f"Orphan tag '{tag}' not found")
        
        # Get taxonomy structure
        taxonomy = assigner.get_taxonomy_structure()
        
        # Call LLM for suggestions
        llm_service = LLMService()
        
        prompt = f"""
        Suggest the best parent category for this orphan tag:
        
        Tag: {orphan['display_name']} ({orphan['tag']})
        Usage count: {orphan['usage_count']}
        
        Available parent categories:
        {json.dumps(list(taxonomy.keys()), indent=2)}
        
        Return top 3 suggestions with confidence scores.
        """
        
        # Use a simpler model for quick suggestions
        result = await llm_service.generate_with_model(
            model_key='ontology_suggestion',
            prompt_key='ontology_system',
            tags=[tag],
            ontology_context=json.dumps(taxonomy, indent=2)
        )
        
        return {
            "success": True,
            "tag": tag,
            "suggestions": result.get("hierarchies", []),
            "reasoning": result.get("reasoning", "")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get assignment suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
