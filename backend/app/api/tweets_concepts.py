"""
Updated tweets API using concept-only tag system.
Returns concept IDs and metadata instead of raw tag text.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict
from datetime import datetime
import json
import logging
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models import Tweet, TweetMedia
from app.database import get_db
from app.schemas.tweet import TweetResponse, TweetWithMedia
from app.services.concept_only_tag_service import ConceptOnlyTagService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize concept service
concept_service = ConceptOnlyTagService()

@router.get("/", response_model=List[Dict])
def get_tweets(
    limit: int = Query(50, ge=1, le=500),
    skip: int = Query(0, ge=0),
    with_media_only: bool = False,
    concept_id: Optional[str] = Query(None, description="Filter by concept ID"),
    include_concepts: bool = Query(True, description="Include full concept details"),
    db: Session = Depends(get_db)
):
    """Get recent tweets with concept-based tags"""
    query = db.query(Tweet).options(
        joinedload(Tweet.media)
    )
    
    # Filter by concept if provided
    if concept_id:
        logger.info(f"Filtering tweets by concept: '{concept_id}'")
        
        # Get tweet IDs that have this concept
        instances = concept_service.tag_instances.find({
            'content_type': 'tweet',
            'concept_id': concept_id
        })
        tweet_ids = [inst['content_id'] for inst in instances]
        
        if tweet_ids:
            query = query.filter(Tweet.id.in_(tweet_ids))
        else:
            return []
    
    if with_media_only:
        query = query.join(TweetMedia).distinct()
    
    # Execute query
    try:
        tweets = query.order_by(Tweet.created_at.desc()).offset(skip).limit(limit).all()
    except Exception as e:
        logger.error(f"Error executing tweet query: {e}")
        tweets = []
    
    # Convert to response model with concepts
    result = []
    for tweet in tweets:
        # Get concepts for this tweet
        concepts = concept_service.get_tags_for_content('tweet', tweet.id)
        
        tweet_dict = {
            "id": tweet.id,
            "text": tweet.text,
            "author_id": tweet.author_id,
            "author_username": tweet.author_username,
            "created_at": tweet.created_at.isoformat() if tweet.created_at else None,
            "metrics": {
                "likes": tweet.like_count,
                "retweets": tweet.retweet_count,
                "replies": tweet.reply_count,
                "quotes": tweet.quote_count
            },
            "media": [
                {
                    "media_key": m.media_key,
                    "type": m.type,
                    "url": m.url,
                    "preview_image_url": m.preview_image_url,
                    "alt_text": m.alt_text,
                    "width": m.width,
                    "height": m.height
                }
                for m in tweet.media
            ]
        }
        
        if include_concepts:
            # Include full concept details
            tweet_dict["concepts"] = concepts
        else:
            # Just include concept IDs
            tweet_dict["concept_ids"] = [c['concept_id'] for c in concepts]
        
        result.append(tweet_dict)
    
    return result

@router.get("/faceted-search")
def faceted_search(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    authors: Optional[List[str]] = Query(None),
    concept_ids: Optional[List[str]] = Query(None),
    search: Optional[str] = None,
    exclude_retweets: bool = Query(False),
    db: Session = Depends(get_db)
):
    """
    Faceted search for tweets with concept-based filtering
    """
    
    query = db.query(Tweet).options(
        joinedload(Tweet.media)
    )
    
    # Apply author filter
    if authors:
        query = query.filter(Tweet.author_username.in_(authors))
    
    # Apply concept filter
    if concept_ids:
        # Get tweet IDs that have ANY of the selected concepts
        instances = concept_service.tag_instances.find({
            'content_type': 'tweet',
            'concept_id': {'$in': concept_ids}
        })
        tweet_ids = list(set([inst['content_id'] for inst in instances]))
        
        if tweet_ids:
            query = query.filter(Tweet.id.in_(tweet_ids))
        else:
            # No tweets with these concepts
            return {
                "tweets": [],
                "facets": {"authors": [], "concepts": []},
                "total": 0,
                "page": page,
                "page_size": page_size
            }
    
    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(Tweet.text.ilike(search_term))
    
    # Exclude retweets if requested
    if exclude_retweets:
        query = query.filter(~Tweet.text.like('RT @%'))
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination
    skip = (page - 1) * page_size
    tweets = query.order_by(Tweet.created_at.desc()).offset(skip).limit(page_size).all()
    
    # Build facets - get all tweets for facet counts (not just current page)
    all_tweets_query = db.query(Tweet)
    if search:
        all_tweets_query = all_tweets_query.filter(Tweet.text.ilike(f"%{search}%"))
    if exclude_retweets:
        all_tweets_query = all_tweets_query.filter(~Tweet.text.like('RT @%'))
    
    # Author facets
    author_counts = db.query(
        Tweet.author_username,
        func.count(Tweet.id).label('count')
    )
    if search:
        author_counts = author_counts.filter(Tweet.text.ilike(f"%{search}%"))
    if exclude_retweets:
        author_counts = author_counts.filter(~Tweet.text.like('RT @%'))
    
    author_facets = [
        {"username": username, "count": count}
        for username, count in author_counts.group_by(Tweet.author_username).all()
    ]
    
    # Concept facets - get all concepts with counts
    concept_facets = []
    all_concepts = concept_service.get_all_concepts_with_counts(content_type='tweet')
    
    # Only include concepts that appear in the current filtered set
    if search or exclude_retweets or authors:
        # Get tweet IDs from current filter
        filtered_tweet_ids = [t.id for t in all_tweets_query.all()]
        
        # Filter concepts to only those on filtered tweets
        for concept in all_concepts:
            # Count how many of the filtered tweets have this concept
            count = concept_service.tag_instances.count_documents({
                'content_type': 'tweet',
                'concept_id': concept['concept_id'],
                'content_id': {'$in': filtered_tweet_ids}
            })
            if count > 0:
                concept_facets.append({
                    **concept,
                    'count': count
                })
    else:
        concept_facets = all_concepts[:200]  # Top 200 concepts
    
    # Sort concept facets by count
    concept_facets.sort(key=lambda x: x['count'], reverse=True)
    
    # Convert tweets to response format
    tweet_results = []
    for tweet in tweets:
        concepts = concept_service.get_tags_for_content('tweet', tweet.id)
        
        tweet_results.append({
            "id": tweet.id,
            "text": tweet.text,
            "author_id": tweet.author_id,
            "author_username": tweet.author_username,
            "created_at": tweet.created_at.isoformat() if tweet.created_at else None,
            "metrics": {
                "likes": tweet.like_count,
                "retweets": tweet.retweet_count,
                "replies": tweet.reply_count,
                "quotes": tweet.quote_count
            },
            "media": [
                {
                    "media_key": m.media_key,
                    "type": m.type,
                    "url": m.url,
                    "preview_image_url": m.preview_image_url,
                    "alt_text": m.alt_text,
                    "width": m.width,
                    "height": m.height
                }
                for m in tweet.media
            ],
            "concepts": concepts,
            "concept_ids": [c['concept_id'] for c in concepts]
        })
    
    return {
        "tweets": tweet_results,
        "facets": {
            "authors": author_facets,
            "concepts": concept_facets[:200]  # Return more concepts for UI to handle
        },
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/{tweet_id}")
def get_tweet(tweet_id: str, include_concepts: bool = Query(True), db: Session = Depends(get_db)):
    """Get a specific tweet by ID with concepts"""
    tweet = db.query(Tweet).options(
        joinedload(Tweet.media)
    ).filter(Tweet.id == tweet_id).first()
    
    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")
    
    # Get concepts
    concepts = concept_service.get_tags_for_content('tweet', tweet_id)
    
    # Build response
    result = {
        "id": tweet.id,
        "text": tweet.text,
        "author_id": tweet.author_id,
        "author_username": tweet.author_username,
        "created_at": tweet.created_at.isoformat() if tweet.created_at else None,
        "metrics": {
            "likes": tweet.like_count,
            "retweets": tweet.retweet_count,
            "replies": tweet.reply_count,
            "quotes": tweet.quote_count
        },
        "media": [
            {
                "media_key": m.media_key,
                "type": m.type,
                "url": m.url,
                "preview_image_url": m.preview_image_url,
                "alt_text": m.alt_text,
                "width": m.width,
                "height": m.height
            }
            for m in tweet.media
        ]
    }
    
    if include_concepts:
        result["concepts"] = concepts
    else:
        result["concept_ids"] = [c['concept_id'] for c in concepts]
    
    return result

@router.post("/{tweet_id}/concepts")
def add_concept_to_tweet(
    tweet_id: str,
    text: str = Query(..., description="Text to create/find concept from"),
    db: Session = Depends(get_db)
):
    """Add a concept to a tweet (creates concept if needed)"""
    
    # Check if tweet exists
    tweet = db.query(Tweet).filter(Tweet.id == tweet_id).first()
    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")
    
    # Add concept
    success, concept_id = concept_service.add_tag('tweet', tweet_id, text)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to add concept")
    
    # Get concept details
    concept = concept_service.get_concept_by_id(concept_id)
    
    return {
        "message": "Concept added successfully",
        "concept": {
            "concept_id": concept_id,
            "id": concept.get('id'),
            "slug": concept.get('slug'),
            "display_name": concept.get('display_name')
        }
    }

@router.delete("/{tweet_id}/concepts/{concept_id}")
def remove_concept_from_tweet(tweet_id: str, concept_id: str):
    """Remove a concept from a tweet"""
    
    success = concept_service.remove_tag('tweet', tweet_id, concept_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Concept not found on this tweet")
    
    return {"message": "Concept removed successfully"}

@router.get("/stats/concepts")
def get_concept_statistics():
    """Get concept usage statistics for tweets"""
    
    concepts = concept_service.get_all_concepts_with_counts(content_type='tweet')
    
    return {
        "total_concepts": len(concepts),
        "top_concepts": concepts[:20],  # Top 20 most used
        "statistics": {
            "total_assignments": sum(c['count'] for c in concepts),
            "average_per_concept": sum(c['count'] for c in concepts) / len(concepts) if concepts else 0
        }
    }

@router.get("/concepts/hierarchy")
def get_concept_hierarchy():
    """Get concepts organized in hierarchy for faceted browsing"""
    
    # Get all concepts with their hierarchy
    all_concepts = concept_service.concepts.find({})
    
    # Build hierarchy structure
    root_concepts = []
    concept_map = {}
    
    # First pass: Create concept map
    for concept in all_concepts:
        concept_id = str(concept['_id'])
        # Convert parent ObjectIds to strings
        parents = concept.get('parents', [])
        if parents:
            parents = [str(p) if hasattr(p, '__str__') else p for p in parents]
        
        concept_map[concept_id] = {
            "concept_id": concept_id,
            "id": concept.get('id'),
            "slug": concept.get('slug'),
            "display_name": concept.get('display_name'),
            "entity_type": concept.get('entity_type'),
            "parents": parents,
            "children": [],
            "count": 0  # Will be populated later
        }
    
    # Second pass: Build hierarchy
    for concept_id, concept_data in concept_map.items():
        if not concept_data['parents']:
            # Root concept
            root_concepts.append(concept_data)
        else:
            # Add to parent's children
            for parent_id in concept_data['parents']:
                if parent_id in concept_map:
                    concept_map[parent_id]['children'].append(concept_data)
    
    # Third pass: Add counts
    for concept_id in concept_map:
        count = concept_service.tag_instances.count_documents({
            'content_type': 'tweet',
            'concept_id': concept_id
        })
        concept_map[concept_id]['count'] = count
    
    return root_concepts

@router.post("/concepts/batch")
def get_concepts_batch(concept_ids: List[str]):
    """Get multiple concepts by their IDs"""
    
    concepts = []
    for concept_id in concept_ids:
        concept = concept_service.get_concept_by_id(concept_id)
        if concept:
            concepts.append({
                "concept_id": concept_id,
                "id": concept.get('id'),
                "slug": concept.get('slug'),
                "display_name": concept.get('display_name'),
                "entity_type": concept.get('entity_type'),
                "description": concept.get('description'),
                "icon": concept.get('icon'),
                "color": concept.get('color'),
                "auto_generated": concept.get('auto_generated', False)
            })
    
    return {"concepts": concepts}

@router.get("/concepts/search")
def search_concepts(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50)
):
    """Search for concepts by text"""
    
    # Search in display_name and slug
    search_results = concept_service.concepts.find({
        '$or': [
            {'display_name': {'$regex': q, '$options': 'i'}},
            {'slug': {'$regex': q, '$options': 'i'}},
            {'description': {'$regex': q, '$options': 'i'}}
        ]
    }).limit(limit)
    
    concepts = []
    for concept in search_results:
        concept_id = str(concept['_id'])
        
        # Get usage count
        count = concept_service.tag_instances.count_documents({
            'concept_id': concept_id
        })
        
        concepts.append({
            "concept_id": concept_id,
            "id": concept.get('id'),
            "slug": concept.get('slug'),
            "display_name": concept.get('display_name'),
            "entity_type": concept.get('entity_type'),
            "description": concept.get('description'),
            "usage_count": count
        })
    
    return {"concepts": concepts, "total": len(concepts)}

@router.get("/concepts/stats")
def get_concept_statistics(content_type: Optional[str] = None):
    """Get concept usage statistics"""
    
    # Get all concepts with counts
    concepts = concept_service.get_all_concepts_with_counts(content_type=content_type)
    
    return {
        "total_concepts": len(concepts),
        "top_concepts": concepts[:20],  # Top 20 most used
        "statistics": {
            "total_assignments": sum(c['count'] for c in concepts),
            "average_per_concept": sum(c['count'] for c in concepts) / len(concepts) if concepts else 0
        }
    }