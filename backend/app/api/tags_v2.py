"""
Tags API v2 - Using the new unified tag system
This replaces the old tag endpoints with clean, consistent API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import logging

from app.services.tag_instance_service import TagInstanceService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/tags", tags=["tags-v2"])

# ==================== Request/Response Models ====================

class AddTagRequest(BaseModel):
    """Request model for adding a tag"""
    content_type: str  # 'tweet', 'article', 'paper'
    content_id: str
    tag: str
    tag_type: str = 'manual'
    confidence: float = 1.0
    created_by: Optional[str] = None

class RemoveTagRequest(BaseModel):
    """Request model for removing a tag"""
    content_type: str
    content_id: str
    tag: str

class TagResponse(BaseModel):
    """Response model for a tag"""
    id: int
    tag: str
    concept_id: int
    raw_tag: str
    tag_type: str
    confidence: float
    created_at: Optional[str]
    created_by: Optional[str]

class TagStatsResponse(BaseModel):
    """Response model for tag statistics"""
    tag: str
    concept_id: Optional[int]
    found: bool
    total: int
    by_type: Dict[str, int]
    quality_score: Optional[float]
    last_used: Optional[str]

class TagCloudItem(BaseModel):
    """Response model for tag cloud item"""
    tag: str
    concept_id: int
    count: int

class TagSuggestion(BaseModel):
    """Response model for tag suggestion"""
    tag: str
    concept_id: Optional[int]
    type: str  # 'existing' or 'new'
    score: Optional[float]
    usage_count: Optional[int]

# ==================== Tag Management Endpoints ====================

@router.post("/add", response_model=TagResponse)
def add_tag(
    request: AddTagRequest,
):
    """Add a tag to content using the new unified system"""
    try:
        service = TagInstanceService(db)
        
        # Convert string to enum
        content_type = ContentType(request.content_type)
        tag_type = TagType(request.tag_type)
        
        # Add the tag
        instance = service.add_tag(
            content_type=content_type,
            content_id=request.content_id,
            tag_text=request.tag,
            tag_type=tag_type,
            confidence=request.confidence,
            created_by=request.created_by
        )
        
        db.commit()
        
        return TagResponse(
            id=instance.id,
            tag=instance.display_tag,
            concept_id=instance.concept_id,
            raw_tag=instance.raw_tag,
            tag_type=instance.tag_type.value,
            confidence=instance.confidence,
            created_at=instance.created_at.isoformat() if instance.created_at else None,
            created_by=instance.created_by
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to add tag: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to add tag")

@router.delete("/remove")
def remove_tag(
    request: RemoveTagRequest,
):
    """Remove a tag from content"""
    try:
        service = TagInstanceService(db)
        
        # Convert string to enum
        content_type = ContentType(request.content_type)
        
        # Remove the tag
        success = service.remove_tag(
            content_type=content_type,
            content_id=request.content_id,
            tag_text=request.tag
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Tag not found")
        
        db.commit()
        
        return {"message": "Tag removed successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove tag: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to remove tag")

@router.get("/content/{content_type}/{content_id}", response_model=List[TagResponse])
def get_content_tags(
    content_type: str,
    content_id: str,
    include_deleted: bool = Query(False),
):
    """Get all tags for a specific piece of content"""
    try:
        service = TagInstanceService(db)
        
        # Convert string to enum
        content_type_enum = ContentType(content_type)
        
        # Get tags
        tags = service.get_tags(
            content_type=content_type_enum,
            content_id=content_id,
            include_deleted=include_deleted
        )
        
        return [
            TagResponse(
                id=tag['id'],
                tag=tag['tag'],
                concept_id=tag['concept_id'],
                raw_tag=tag['raw_tag'],
                tag_type=tag['tag_type'],
                confidence=tag['confidence'],
                created_at=tag['created_at'],
                created_by=tag['created_by']
            )
            for tag in tags
        ]
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get tags: {e}")
        raise HTTPException(status_code=500, detail="Failed to get tags")

# ==================== Tag Statistics Endpoints ====================

@router.get("/stats", response_model=TagStatsResponse)
def get_tag_statistics(
    tag: Optional[str] = Query(None),
):
    """Get tag statistics"""
    try:
        service = TagInstanceService(db)
        stats = service.get_tag_statistics(tag)
        
        return TagStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Failed to get tag statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")

@router.get("/cloud", response_model=List[TagCloudItem])
def get_tag_cloud(
    content_type: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
):
    """Get tag cloud data"""
    try:
        service = TagInstanceService(db)
        
        # Convert string to enum if provided
        content_type_enum = ContentType(content_type) if content_type else None
        
        # Get tag cloud
        cloud = service.get_tag_cloud(
            content_type=content_type_enum,
            limit=limit
        )
        
        return [
            TagCloudItem(
                tag=item['tag'],
                concept_id=item['concept_id'],
                count=item['count']
            )
            for item in cloud
        ]
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get tag cloud: {e}")
        raise HTTPException(status_code=500, detail="Failed to get tag cloud")

# ==================== Tag Suggestion Endpoints ====================

@router.post("/suggest", response_model=List[TagSuggestion])
def suggest_tags(
    text: str,
    content_type: str,
    limit: int = Query(10, le=50),
):
    """Suggest tags for content"""
    try:
        service = TagInstanceService(db)
        
        # Convert string to enum
        content_type_enum = ContentType(content_type)
        
        # Get suggestions
        suggestions = service.suggest_tags(
            text=text,
            content_type=content_type_enum,
            limit=limit
        )
        
        return [
            TagSuggestion(
                tag=s['tag'],
                concept_id=s.get('concept_id'),
                type=s['type'],
                score=s.get('score'),
                usage_count=s.get('usage_count')
            )
            for s in suggestions
        ]
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to suggest tags: {e}")
        raise HTTPException(status_code=500, detail="Failed to suggest tags")

# ==================== Migration Support Endpoints ====================

@router.get("/migration/status")
    """Get the status of tag migration"""
    try:
        # Check if new tables exist
        result = db.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='tag_instances'
        """))
        has_new_tables = result.scalar() is not None
        
        if not has_new_tables:
            return {
                "status": "not_started",
                "message": "Migration has not been run yet"
            }
        
        # Get migration statistics
        stats = db.execute(text("""
            SELECT 
                COUNT(DISTINCT ti.id) as total_migrated,
                COUNT(DISTINCT CASE WHEN ti.content_type = 'tweet' THEN ti.id END) as tweets_migrated,
                COUNT(DISTINCT CASE WHEN ti.content_type = 'article' THEN ti.id END) as articles_migrated,
                COUNT(DISTINCT CASE WHEN ti.content_type = 'paper' THEN ti.id END) as papers_migrated,
                COUNT(DISTINCT ti.concept_id) as concepts_used
            FROM tag_instances ti
            WHERE ti.deleted = 0
        """)).first()
        
        # Get original counts
        old_stats = db.execute(text("""
            SELECT 
                (SELECT COUNT(*) FROM tags) as old_tweets,
                (SELECT COUNT(*) FROM article_tags) as old_articles,
                (SELECT COUNT(*) FROM paper_tags) as old_papers
        """)).first()
        
        return {
            "status": "completed" if stats.total_migrated > 0 else "ready",
            "new_system": {
                "total_tags": stats.total_migrated,
                "tweets": stats.tweets_migrated,
                "articles": stats.articles_migrated,
                "papers": stats.papers_migrated,
                "concepts": stats.concepts_used
            },
            "old_system": {
                "tweets": old_stats.old_tweets,
                "articles": old_stats.old_articles,
                "papers": old_stats.old_papers
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get migration status: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

@router.post("/migration/verify")
    """Verify that migration was successful"""
    try:
        issues = []
        
        # Check for orphaned tags (tags without concepts)
        orphaned = db.execute(text("""
            SELECT COUNT(*) FROM tag_instances ti
            LEFT JOIN tag_concepts tc ON ti.concept_id = tc.id
            WHERE tc.id IS NULL
        """)).scalar()
        
        if orphaned > 0:
            issues.append(f"Found {orphaned} orphaned tag instances without concepts")
        
        # Check for duplicate tags on same content
        duplicates = db.execute(text("""
            SELECT content_type, content_id, concept_id, COUNT(*) as cnt
            FROM tag_instances
            WHERE deleted = 0
            GROUP BY content_type, content_id, concept_id
            HAVING cnt > 1
        """)).fetchall()
        
        if duplicates:
            issues.append(f"Found {len(duplicates)} duplicate tag assignments")
        
        # Check usage count accuracy
        inaccurate = db.execute(text("""
            SELECT tce.concept_id, tce.usage_count, COUNT(ti.id) as actual_count
            FROM tag_concept_extended tce
            LEFT JOIN tag_instances ti ON ti.concept_id = tce.concept_id AND ti.deleted = 0
            GROUP BY tce.concept_id, tce.usage_count
            HAVING tce.usage_count != COUNT(ti.id)
        """)).fetchall()
        
        if inaccurate:
            issues.append(f"Found {len(inaccurate)} concepts with inaccurate usage counts")
        
        if issues:
            return {
                "status": "issues_found",
                "issues": issues
            }
        else:
            return {
                "status": "verified",
                "message": "Migration verified successfully"
            }
        
    except Exception as e:
        logger.error(f"Failed to verify migration: {e}")
        return {
            "status": "error",
            "message": str(e)
        }