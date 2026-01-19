"""
Complete MongoDB-based Reddit API.
Provides CRUD operations for Reddit posts with faceted browsing and tagging.
"""

from fastapi import APIRouter, HTTPException, Query, Body
from pymongo import ASCENDING, DESCENDING
from app.database.mongodb import get_database
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import logging
from bson import ObjectId
import json

from app.services.concept_only_tag_service import ConceptOnlyTagService
from app.models.mongodb_models import RedditPost, RedditCollectionStats

logger = logging.getLogger(__name__)
router = APIRouter()

# MongoDB connection
db = get_database()
posts_collection = db.reddit_posts

# Initialize concept service
concept_service = ConceptOnlyTagService()

@router.get("/", response_model=List[Dict])
def get_reddit_posts(
    limit: int = Query(50, ge=1, le=500),
    skip: int = Query(0, ge=0),
    subreddit: Optional[str] = Query(None, description="Filter by subreddit"),
    concept_id: Optional[str] = Query(None, description="Filter by concept ID"),
    include_concepts: bool = Query(True, description="Include full concept details"),
    sort_by: str = Query("created_utc", description="Sort field"),
    sort_order: int = Query(-1, description="Sort order: 1 for ASC, -1 for DESC"),
    text_search: Optional[str] = Query(None, description="Search in title and selftext"),
    min_score: Optional[int] = Query(None, description="Minimum post score"),
    time_range: Optional[str] = Query(None, description="Time range: 24h, 7d, 30d"),
    author: Optional[str] = Query(None, description="Filter by author")
):
    """Get Reddit posts with filtering and concept-based tags from MongoDB"""
    
    # Build query
    query = {}
    
    # Subreddit filter
    if subreddit:
        query["subreddit"] = {"$regex": f"^{subreddit}$", "$options": "i"}
    
    # Author filter
    if author:
        query["author"] = {"$regex": f"^{author}$", "$options": "i"}
    
    # Score filter
    if min_score is not None:
        query["score"] = {"$gte": min_score}
    
    # Time range filter
    if time_range:
        now = datetime.now(timezone.utc)
        if time_range == "24h":
            since = now - timedelta(hours=24)
        elif time_range == "7d":
            since = now - timedelta(days=7)
        elif time_range == "30d":
            since = now - timedelta(days=30)
        else:
            since = now - timedelta(days=7)  # Default to 7 days
        
        query["created_utc"] = {"$gte": since}
    
    # Text search
    if text_search:
        query["$or"] = [
            {"title": {"$regex": text_search, "$options": "i"}},
            {"selftext": {"$regex": text_search, "$options": "i"}}
        ]
    
    # Filter by concept if provided
    if concept_id:
        logger.info(f"Filtering Reddit posts by concept: '{concept_id}'")
        try:
            if len(concept_id) == 24:  # Valid ObjectId length
                concept_filter = ObjectId(concept_id)
            else:
                concept_filter = concept_id
        except:
            concept_filter = concept_id
        
        # Find tag instances for this concept
        tag_instances = list(db.tag_instances.find({"concept_id": concept_filter}))
        if not tag_instances:
            return []  # No posts found for this concept
        
        # Extract Reddit post IDs
        reddit_post_ids = []
        for instance in tag_instances:
            if instance.get("content_type") == "reddit_post" and instance.get("content_id"):
                try:
                    reddit_post_ids.append(ObjectId(instance["content_id"]))
                except:
                    pass  # Skip invalid ObjectIds
        
        if not reddit_post_ids:
            return []
        
        query["_id"] = {"$in": reddit_post_ids}
    
    logger.info(f"Reddit posts query: {query}")
    
    # Execute query
    cursor = posts_collection.find(query)
    
    # Sort
    sort_field = sort_by
    cursor = cursor.sort(sort_field, sort_order)
    
    # Pagination
    cursor = cursor.skip(skip).limit(limit)
    
    posts = list(cursor)
    
    # Convert ObjectIds to strings and add concept information
    result = []
    for post in posts:
        # Convert ObjectId to string
        post["_id"] = str(post["_id"])
        
        # Add concept information if requested
        if include_concepts:
            post_concepts = concept_service.get_concepts_for_content(
                content_id=post["_id"], 
                content_type="reddit_post"
            )
            post["concepts"] = post_concepts
        else:
            post["concepts"] = []
        
        result.append(post)
    
    logger.info(f"Returning {len(result)} Reddit posts")
    return result

@router.get("/faceted-search")
def get_reddit_faceted_search(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    subreddit: Optional[str] = Query(None, description="Filter by subreddit"),
    concept_id: Optional[str] = Query(None, description="Filter by concept ID"),
    text_search: Optional[str] = Query(None, description="Search query"),
    min_score: Optional[int] = Query(None, description="Minimum score"),
    time_range: Optional[str] = Query(None, description="Time range filter"),
    author: Optional[str] = Query(None, description="Filter by author"),
    sort_by: str = Query("created_utc", description="Sort field"),
    sort_order: int = Query(-1, description="Sort order")
):
    """Get Reddit posts with faceted search and pagination"""
    
    # Calculate skip value
    skip = (page - 1) * page_size
    
    # Get posts
    posts = get_reddit_posts(
        limit=page_size,
        skip=skip,
        subreddit=subreddit,
        concept_id=concept_id,
        text_search=text_search,
        min_score=min_score,
        time_range=time_range,
        author=author,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    # Get total count for pagination
    query = {}
    if subreddit:
        query["subreddit"] = {"$regex": f"^{subreddit}$", "$options": "i"}
    if author:
        query["author"] = {"$regex": f"^{author}$", "$options": "i"}
    if min_score is not None:
        query["score"] = {"$gte": min_score}
    if time_range:
        now = datetime.now(timezone.utc)
        if time_range == "24h":
            since = now - timedelta(hours=24)
        elif time_range == "7d":
            since = now - timedelta(days=7)
        elif time_range == "30d":
            since = now - timedelta(days=30)
        else:
            since = now - timedelta(days=7)
        query["created_utc"] = {"$gte": since}
    if text_search:
        query["$or"] = [
            {"title": {"$regex": text_search, "$options": "i"}},
            {"selftext": {"$regex": text_search, "$options": "i"}}
        ]
    
    total_posts = posts_collection.count_documents(query)
    total_pages = (total_posts + page_size - 1) // page_size
    
    return {
        "posts": posts,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_posts": total_posts,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }

@router.get("/facets")
def get_reddit_facets():
    """Get faceted search options for Reddit posts"""
    
    # Subreddits with post counts
    subreddit_pipeline = [
        {"$group": {"_id": "$subreddit", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 20}
    ]
    subreddits = list(posts_collection.aggregate(subreddit_pipeline))
    
    # Top authors with post counts
    author_pipeline = [
        {"$match": {"author": {"$ne": "[deleted]"}}},
        {"$group": {"_id": "$author", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 20}
    ]
    authors = list(posts_collection.aggregate(author_pipeline))
    
    # Time-based facets
    now = datetime.now(timezone.utc)
    time_facets = {
        "24h": posts_collection.count_documents({"created_utc": {"$gte": now - timedelta(hours=24)}}),
        "7d": posts_collection.count_documents({"created_utc": {"$gte": now - timedelta(days=7)}}),
        "30d": posts_collection.count_documents({"created_utc": {"$gte": now - timedelta(days=30)}})
    }
    
    # Score ranges
    score_facets = {
        "high_score": posts_collection.count_documents({"score": {"$gte": 100}}),
        "medium_score": posts_collection.count_documents({"score": {"$gte": 10, "$lt": 100}}),
        "low_score": posts_collection.count_documents({"score": {"$lt": 10}})
    }
    
    # Post types
    type_facets = {
        "text_posts": posts_collection.count_documents({"is_self": True}),
        "link_posts": posts_collection.count_documents({"is_self": False}),
        "video_posts": posts_collection.count_documents({"is_video": True})
    }
    
    return {
        "subreddits": [{"name": item["_id"], "count": item["count"]} for item in subreddits],
        "authors": [{"name": item["_id"], "count": item["count"]} for item in authors],
        "time_ranges": time_facets,
        "score_ranges": score_facets,
        "post_types": type_facets,
        "total_posts": posts_collection.count_documents({})
    }

@router.get("/{post_id}")
def get_reddit_post(post_id: str):
    """Get a specific Reddit post by ID"""
    
    try:
        # Try ObjectId first
        if len(post_id) == 24:
            query = {"_id": ObjectId(post_id)}
        else:
            # Try reddit_id
            query = {"reddit_id": post_id}
    except:
        query = {"reddit_id": post_id}
    
    post = posts_collection.find_one(query)
    
    if not post:
        raise HTTPException(status_code=404, detail="Reddit post not found")
    
    # Convert ObjectId to string
    post["_id"] = str(post["_id"])
    
    # Add concept information
    post_concepts = concept_service.get_concepts_for_content(
        content_id=post["_id"],
        content_type="reddit_post"
    )
    post["concepts"] = post_concepts
    
    return post

@router.post("/{post_id}/tags")
def add_reddit_post_tag(post_id: str, tag_data: Dict[str, Any] = Body(...)):
    """Add a tag to a Reddit post"""
    
    try:
        if len(post_id) == 24:
            query = {"_id": ObjectId(post_id)}
        else:
            query = {"reddit_id": post_id}
    except:
        query = {"reddit_id": post_id}
    
    post = posts_collection.find_one(query)
    if not post:
        raise HTTPException(status_code=404, detail="Reddit post not found")
    
    # Use concept service to add tag
    tag_name = tag_data.get("tag_name", "").strip()
    if not tag_name:
        raise HTTPException(status_code=400, detail="Tag name is required")
    
    try:
        success, concept_id = concept_service.add_concept_to_content(
            content_id=str(post["_id"]),
            content_type="reddit_post",
            concept_name=tag_name,
            context=f"Reddit post: {post.get('title', '')}"
        )
    except Exception as e:
        logger.error(f"Error adding tag to Reddit post: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    if not success:
        raise HTTPException(status_code=400, detail="Failed to add tag to Reddit post")

    return {
        "success": True,
        "message": f"Tag '{tag_name}' added to post",
        "concept_id": concept_id
    }

@router.delete("/{post_id}/tags/{concept_id}")
def remove_reddit_post_tag(post_id: str, concept_id: str):
    """Remove a tag from a Reddit post"""
    
    try:
        if len(post_id) == 24:
            query = {"_id": ObjectId(post_id)}
        else:
            query = {"reddit_id": post_id}
    except:
        query = {"reddit_id": post_id}
    
    post = posts_collection.find_one(query)
    if not post:
        raise HTTPException(status_code=404, detail="Reddit post not found")
    
    try:
        removed = concept_service.remove_concept_from_content(
            content_id=str(post["_id"]),
            content_type="reddit_post",
            concept_id=concept_id
        )
    except Exception as e:
        logger.error(f"Error removing tag from Reddit post: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    if not removed:
        raise HTTPException(status_code=404, detail="Concept not found on this post")

    return {"success": True, "message": "Tag removed from post"}

@router.get("/stats/collection")
def get_reddit_collection_stats():
    """Get Reddit collection statistics"""
    
    try:
        from app.collectors.reddit_collector import RedditCollector
        collector = RedditCollector()
        return collector.get_collection_stats()
    except Exception as e:
        logger.error(f"Error getting collection stats: {e}")
        # Fallback to basic stats
        total_posts = posts_collection.count_documents({})
        return {
            "total_posts": total_posts,
            "error": "Could not load full statistics"
        }

@router.post("/collect")
def trigger_reddit_collection(max_posts_per_subreddit: Optional[int] = Body(25)):
    """Manually trigger Reddit collection"""
    
    try:
        from app.collectors.reddit_collector import RedditCollector
        collector = RedditCollector()
        stats = collector.collect_posts(max_posts_per_subreddit=max_posts_per_subreddit)
        return {
            "success": True,
            "message": "Collection completed",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error triggering Reddit collection: {e}")
        raise HTTPException(status_code=500, detail=f"Collection failed: {str(e)}")

@router.get("/subreddits/config")
def get_subreddit_config():
    """Get configured subreddits"""
    
    try:
        with open('reddit_config.json', 'r') as f:
            config = json.load(f)
        return config['subreddits']
    except Exception as e:
        logger.error(f"Error loading subreddit config: {e}")
        raise HTTPException(status_code=500, detail="Could not load subreddit configuration")

@router.get("/search/suggest")
def get_reddit_search_suggestions(q: str = Query(..., min_length=2)):
    """Get search suggestions for Reddit posts"""
    
    # Search in titles
    title_suggestions = posts_collection.distinct("title", {
        "title": {"$regex": q, "$options": "i"}
    })
    
    # Search in authors
    author_suggestions = posts_collection.distinct("author", {
        "author": {"$regex": q, "$options": "i"},
        "author": {"$ne": "[deleted]"}
    })
    
    # Search in subreddits
    subreddit_suggestions = posts_collection.distinct("subreddit", {
        "subreddit": {"$regex": q, "$options": "i"}
    })
    
    return {
        "titles": title_suggestions[:10],
        "authors": author_suggestions[:10],
        "subreddits": subreddit_suggestions[:10]
    }
