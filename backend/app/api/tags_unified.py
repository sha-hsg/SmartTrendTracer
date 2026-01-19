"""
Unified Tag API - Centralized endpoints for all tag operations using the new concept structure
This replaces all previous tag endpoints and provides a consistent interface
"""
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from app.services.tag_concept_service import get_tag_concept_service

logger = logging.getLogger(__name__)
router = APIRouter()

# ============= Request/Response Models =============

class TagRequest(BaseModel):
    """Request to add a tag to content"""
    tag_text: str
    tag_type: str = 'manual'

class BulkTagRequest(BaseModel):
    """Request to add multiple tags"""
    tags: List[str]
    tag_type: str = 'manual'

class ConceptResponse(BaseModel):
    """Response with concept information"""
    id: str
    slug: str
    display_name: str
    description: Optional[str]
    entity_type: Optional[str]
    icon: Optional[str]
    color: Optional[str]
    parents: List[str]
    children: List[str]
    usage_count: int

class TagResponse(BaseModel):
    """Response for a tag with concept info"""
    original_text: str
    concept_id: Optional[str]
    slug: str
    display_name: str
    entity_type: Optional[str]
    icon: Optional[str]
    color: Optional[str]
    tag_type: str

# ============= Core Tag Endpoints =============

@router.get("/resolve/{tag_text}")
async def resolve_tag(
    tag_text: str,
) -> Optional[ConceptResponse]:
    """
    Resolve any tag text to its canonical concept.
    This is the primary endpoint for tag resolution.
    """
    service = get_tag_concept_service(db)
    concept = service.resolve_tag_to_concept(tag_text)
    
    if not concept:
        return None
    
    return ConceptResponse(
        id=concept['id'],
        slug=concept['slug'],
        display_name=concept['display_name'],
        description=concept.get('description'),
        entity_type=concept.get('entity_type'),
        icon=concept.get('icon'),
        color=concept.get('color'),
        parents=concept.get('parents', []),
        children=concept.get('children', []),
        usage_count=concept.get('usage_count', 0)
    )

@router.post("/create")
async def create_tag_concept(
    tag_text: str,
    entity_type: str = 'concept',
) -> ConceptResponse:
    """Create a new tag concept"""
    service = get_tag_concept_service(db)
    
    # Check if already exists
    existing = service.resolve_tag_to_concept(tag_text)
    if existing:
        raise HTTPException(status_code=400, detail="Tag already exists")
    
    # Create new concept
    concept = service.create_concept_from_tag(tag_text, entity_type)
    if not concept:
        raise HTTPException(status_code=500, detail="Failed to create concept")
    
    return ConceptResponse(
        id=concept['id'],
        slug=concept['slug'],
        display_name=concept['display_name'],
        description=concept.get('description'),
        entity_type=concept.get('entity_type'),
        icon=concept.get('icon'),
        color=concept.get('color'),
        parents=concept.get('parents', []),
        children=concept.get('children', []),
        usage_count=0
    )

# ============= Content Tagging Endpoints =============

@router.post("/tweets/{tweet_id}/tags")
async def add_tag_to_tweet(
    tweet_id: str,
    request: TagRequest,
) -> Dict[str, Any]:
    """Add a tag to a tweet"""
    service = get_tag_concept_service(db)
    
    success = service.add_tag_to_content(
        'tweet', tweet_id, request.tag_text, request.tag_type
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to add tag")
    
    return {"success": True, "message": "Tag added successfully"}

@router.post("/papers/{paper_id}/tags")
async def add_tag_to_paper(
    paper_id: str,
    request: TagRequest,
) -> Dict[str, Any]:
    """Add a tag to a paper"""
    service = get_tag_concept_service(db)
    
    success = service.add_tag_to_content(
        'paper', paper_id, request.tag_text, request.tag_type
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to add tag")
    
    return {"success": True, "message": "Tag added successfully"}

@router.post("/articles/{article_id}/tags")
async def add_tag_to_article(
    article_id: str,
    request: TagRequest,
) -> Dict[str, Any]:
    """Add a tag to an article"""
    service = get_tag_concept_service(db)
    
    success = service.add_tag_to_content(
        'article', article_id, request.tag_text, request.tag_type
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to add tag")
    
    return {"success": True, "message": "Tag added successfully"}

@router.post("/tweets/{tweet_id}/tags/bulk")
async def add_bulk_tags_to_tweet(
    tweet_id: str,
    request: BulkTagRequest,
) -> Dict[str, Any]:
    """Add multiple tags to a tweet"""
    service = get_tag_concept_service(db)
    
    added = 0
    failed = 0
    
    for tag_text in request.tags:
        success = service.add_tag_to_content(
            'tweet', tweet_id, tag_text, request.tag_type
        )
        if success:
            added += 1
        else:
            failed += 1
    
    return {
        "success": True,
        "added": added,
        "failed": failed,
        "message": f"Added {added} tags, {failed} failed"
    }

# ============= Tag Retrieval Endpoints =============

@router.get("/tweets/{tweet_id}/tags")
async def get_tweet_tags(
    tweet_id: str,
) -> List[TagResponse]:
    """Get all tags for a tweet with concept information"""
    service = get_tag_concept_service(db)
    tags = service.get_content_tags('tweet', tweet_id)
    
    return [
        TagResponse(
            original_text=tag['original_text'],
            concept_id=tag.get('concept_id'),
            slug=tag['slug'],
            display_name=tag['display_name'],
            entity_type=tag.get('entity_type'),
            icon=tag.get('icon'),
            color=tag.get('color'),
            tag_type=tag.get('tag_type', 'manual')
        )
        for tag in tags
    ]

@router.get("/papers/{paper_id}/tags")
async def get_paper_tags(
    paper_id: str,
) -> List[TagResponse]:
    """Get all tags for a paper with concept information"""
    service = get_tag_concept_service(db)
    tags = service.get_content_tags('paper', paper_id)
    
    return [
        TagResponse(
            original_text=tag['original_text'],
            concept_id=tag.get('concept_id'),
            slug=tag['slug'],
            display_name=tag['display_name'],
            entity_type=tag.get('entity_type'),
            icon=tag.get('icon'),
            color=tag.get('color'),
            tag_type=tag.get('tag_type', 'manual')
        )
        for tag in tags
    ]

@router.get("/articles/{article_id}/tags")
async def get_article_tags(
    article_id: str,
) -> List[TagResponse]:
    """Get all tags for an article with concept information"""
    service = get_tag_concept_service(db)
    tags = service.get_content_tags('article', article_id)
    
    return [
        TagResponse(
            original_text=tag['original_text'],
            concept_id=tag.get('concept_id'),
            slug=tag['slug'],
            display_name=tag['display_name'],
            entity_type=tag.get('entity_type'),
            icon=tag.get('icon'),
            color=tag.get('color'),
            tag_type=tag.get('tag_type', 'manual')
        )
        for tag in tags
    ]

# ============= Filtering Endpoints =============

@router.get("/filter/tweets")
async def filter_tweets_by_tag(
    tag: str,
    include_descendants: bool = True,
) -> List[str]:
    """Get all tweet IDs that have a specific tag"""
    service = get_tag_concept_service(db)
    return service.filter_content_by_tag('tweet', tag, include_descendants)

@router.get("/filter/papers")
async def filter_papers_by_tag(
    tag: str,
    include_descendants: bool = True,
) -> List[str]:
    """Get all paper IDs that have a specific tag"""
    service = get_tag_concept_service(db)
    return service.filter_content_by_tag('paper', tag, include_descendants)

@router.get("/filter/articles")
async def filter_articles_by_tag(
    tag: str,
    include_descendants: bool = True,
) -> List[str]:
    """Get all article IDs that have a specific tag"""
    service = get_tag_concept_service(db)
    return service.filter_content_by_tag('article', tag, include_descendants)

# ============= Hierarchy Endpoints =============

@router.get("/hierarchy")
async def get_tag_hierarchy(
) -> Dict[str, Any]:
    """Get the complete tag concept hierarchy"""
    service = get_tag_concept_service(db)
    return service.get_concept_hierarchy()

@router.get("/concepts")
async def get_all_concepts(
    entity_type: Optional[str] = None,
    limit: int = Query(100, le=1000),
) -> List[ConceptResponse]:
    """Get all tag concepts, optionally filtered by entity type"""
    service = get_tag_concept_service(db)
    
    # This would need to be implemented in the service
    # For now, return from cache
    concepts = []
    for concept in service._concept_cache.values():
        if isinstance(concept, dict):  # Skip duplicate entries
            if entity_type and concept.get('entity_type') != entity_type:
                continue
            
            concepts.append(ConceptResponse(
                id=concept['id'],
                slug=concept['slug'],
                display_name=concept['display_name'],
                description=concept.get('description'),
                entity_type=concept.get('entity_type'),
                icon=concept.get('icon'),
                color=concept.get('color'),
                parents=concept.get('parents', []),
                children=concept.get('children', []),
                usage_count=concept.get('usage_count', 0)
            ))
            
            if len(concepts) >= limit:
                break
    
    return concepts

@router.get("/concepts/{concept_id}")
async def get_concept_details(
    concept_id: str,
) -> ConceptResponse:
    """Get detailed information about a specific concept"""
    service = get_tag_concept_service(db)
    
    concept = service._concept_cache.get(concept_id)
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")
    
    return ConceptResponse(
        id=concept['id'],
        slug=concept['slug'],
        display_name=concept['display_name'],
        description=concept.get('description'),
        entity_type=concept.get('entity_type'),
        icon=concept.get('icon'),
        color=concept.get('color'),
        parents=concept.get('parents', []),
        children=concept.get('children', []),
        usage_count=concept.get('usage_count', 0)
    )

# ============= Statistics Endpoints =============

@router.get("/statistics")
async def get_tag_statistics(
) -> Dict[str, Any]:
    """Get comprehensive tag statistics"""
    service = get_tag_concept_service(db)
    return service.get_tag_statistics()

# ============= Migration Endpoints =============

@router.post("/migrate")
async def migrate_legacy_tags(
) -> Dict[str, int]:
    """Migrate all legacy tags to the new concept structure"""
    service = get_tag_concept_service(db)
    return service.migrate_legacy_tags()

# ============= Search Endpoints =============

@router.get("/search")
async def search_tags(
    q: str,
    limit: int = Query(10, le=50),
) -> List[ConceptResponse]:
    """Search for tag concepts by text"""
    service = get_tag_concept_service(db)
    
    # Simple search in cache
    results = []
    search_lower = q.lower()
    
    for concept in service._concept_cache.values():
        if isinstance(concept, dict):
            if (search_lower in concept['slug'].lower() or 
                search_lower in concept['display_name'].lower() or
                (concept.get('description') and search_lower in concept['description'].lower())):
                
                results.append(ConceptResponse(
                    id=concept['id'],
                    slug=concept['slug'],
                    display_name=concept['display_name'],
                    description=concept.get('description'),
                    entity_type=concept.get('entity_type'),
                    icon=concept.get('icon'),
                    color=concept.get('color'),
                    parents=concept.get('parents', []),
                    children=concept.get('children', []),
                    usage_count=concept.get('usage_count', 0)
                ))
                
                if len(results) >= limit:
                    break
    
    return results