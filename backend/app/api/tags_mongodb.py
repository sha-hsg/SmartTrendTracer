"""
Updated tags API using MongoDB for tag management.
Replaces SQLite tag operations with MongoDB tag_instances collection.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.tag_suggestion_service import TagSuggestionService
from app.services.vector_store_mongodb import get_vector_store
from app.services.concept_only_tag_service import ConceptOnlyTagService
from app.database.mongodb import get_database

router = APIRouter()

# Initialize MongoDB connection and services
db = get_database()
concept_service = ConceptOnlyTagService()

class TagCreate(BaseModel):
    tag: str
    tag_type: str = "manual"
    confidence: float = 1.0

class TagResponse(BaseModel):
    tag: str
    tag_type: str
    confidence: float
    content_id: str
    content_type: str

@router.get("/")
def get_all_tags():
    """Get all unique concepts (tags) with counts from MongoDB"""
    return concept_service.get_all_concepts_with_counts()

@router.get("/tweet/{tweet_id}")
def get_tweet_tags(tweet_id: str):
    """Get all tags for a specific tweet from MongoDB"""
    tags = concept_service.get_tags_for_content('tweet', tweet_id)
    return tags

@router.post("/tweet/{tweet_id}")
def add_tag(tweet_id: str, tag_data: TagCreate):
    """Add a tag to a tweet using MongoDB"""
    # Validate tag is not empty
    if not tag_data.tag or not tag_data.tag.strip():
        raise HTTPException(status_code=400, detail="Tag cannot be empty")
    
    # Check if tweet exists in MongoDB
    tweet = db.tweets.find_one({"id": tweet_id})
    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")
    
    # Preserve capitalization for AI-suggested tags and manual tags
    if tag_data.tag_type in ["ai-suggested", "llm", "manual"]:
        # Just clean up spaces, preserve capitalization
        final_tag = tag_data.tag.strip()
    else:
        # Normalize the tag for other types
        final_tag = tag_data.tag.strip()
    
    # Add concept using the dedicated service (returns success flag and concept_id)
    success, concept_id = concept_service.add_concept_to_content(
        content_type='tweet',
        content_id=tweet_id,
        concept_name=final_tag,
        preserve_display_name=True
    )

    if not success or not concept_id:
        raise HTTPException(status_code=400, detail="Failed to add tag")

    concept_details = concept_service.get_concept_by_id(concept_id) or {}
    
    # Update vector store with new tag
    try:
        vector_store = get_vector_store()
        # Get tweet text for context
        context = tweet.get('text', '')[:200] if tweet.get('text') else final_tag
        vector_store.update_tag_incrementally(final_tag.lower(), 'twitter', context)
    except Exception as e:
        # Log error but don't fail the request
        print(f"Failed to update vector store for tag '{final_tag}': {e}")
    
    return {
        "tag": final_tag,
        "tag_type": tag_data.tag_type,
        "confidence": tag_data.confidence,
        "content_id": tweet_id,
        "content_type": "tweet",
        "concept_id": concept_id,
        "concept": {
            "concept_id": concept_id,
            "display_name": concept_details.get('display_name'),
            "slug": concept_details.get('slug')
        }
    }

@router.delete("/tweet/{tweet_id}/{tag}")
def remove_tag(tweet_id: str, tag: str):
    """Remove a tag from a tweet using MongoDB"""
    success = concept_service.remove_concept_from_content(
        content_type='tweet',
        content_id=tweet_id,
        concept_name=tag
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    return {"message": "Tag removed successfully"}

@router.get("/popular")
def get_popular_tags(limit: int = 20):
    """Get most popular tags from MongoDB"""
    all_tags = concept_service.get_all_tags_with_counts()
    # Sort by count and limit
    popular = sorted(all_tags, key=lambda x: x['count'], reverse=True)[:limit]
    return popular

@router.post("/suggest/{tweet_id}")
def suggest_tags_for_tweet(tweet_id: str):
    """Get AI-suggested tags for a specific tweet using both similarity search and LLM"""
    # Get the tweet from MongoDB
    tweet = db.tweets.find_one({"id": tweet_id})
    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")
    
    # Get vector store for similarity search
    from app.services.vector_store_mongodb import get_vector_store
    vector_store = get_vector_store()
    
    # Get LLM service for new tag generation
    tag_service = TagSuggestionService()

    # Check which tags already exist for this tweet in MongoDB
    existing_tags = concept_service.get_tags_for_content('tweet', tweet_id)

    existing_tag_names = []
    existing_tag_lookup = set()
    for tag in existing_tags:
        display_value = tag.get('display_name') or tag.get('original_text') or tag.get('slug')
        if display_value:
            existing_tag_names.append(display_value)
            existing_tag_lookup.add(display_value.lower())
    
    # 1. Find similar existing tags from the vector store
    similar_tags = []
    try:
        # Adjust similarity threshold based on tweet length
        tweet_text = tweet.get('text', '')
        tweet_length = len(tweet_text)
        if tweet_length > 500:
            min_sim = 0.35  # Lower threshold for long tweets
        elif tweet_length > 280:
            min_sim = 0.4   # Medium threshold for extended tweets
        else:
            min_sim = 0.5   # Normal threshold for short tweets
        
        # Search for tags similar to the tweet content
        search_results = vector_store.search_similar_tags(
            query_text=tweet_text,
            k=10,  # Get more candidates for long tweets
            min_similarity=min_sim
        )
        
        # Filter out tags already on this tweet
        for tag, score, count in search_results:
            tag_lower = tag.lower()
            if tag_lower not in existing_tag_lookup:
                similar_tags.append({
                    'tag': tag,
                    'score': round(score, 3),
                    'usage_count': count,
                    'type': 'existing'
                })
        
        # Keep top 5 similar tags
        similar_tags = similar_tags[:5]
        
    except Exception as e:
        print(f"Error searching similar tags: {e}")
        similar_tags = []
    
    # 2. Generate new tags using LLM
    new_tags = []
    model_used = "unknown"
    
    try:
        suggested_tags = tag_service.suggest_tags(
            tweet_text=tweet.get('text', ''),
            author=tweet.get('author_username', '')
        )

        # Check if API was successfully used
        api_was_used = "__api_success__" in suggested_tags if suggested_tags else False
        if api_was_used:
            suggested_tags = [tag for tag in suggested_tags if tag != "__api_success__"]

        # Get model used from tag service
        model_used = tag_service.model_name if api_was_used else "fallback"
        
        # Filter out tags already on this tweet and create tag objects
        for tag in suggested_tags or []:
            tag_lower = tag.lower()
            if tag_lower not in existing_tag_lookup:
                new_tags.append({
                    'tag': tag,
                    'type': 'new',
                    'model': model_used
                })
        
        # Keep top 5 new tags
        new_tags = new_tags[:5]
        
    except Exception as e:
        print(f"Error generating new tags: {e}")
        new_tags = []
    
    # Combine and format response
    return {
        'tweet_id': tweet_id,
        'existing_suggestions': similar_tags,
        'new_suggestions': new_tags,
        'already_tagged': existing_tag_names,
        'model_used': model_used,
        'total_suggestions': len(similar_tags) + len(new_tags)
    }

@router.get("/orphans")
def get_orphan_tags():
    """Get all orphan tags (tags without concept_id) from MongoDB"""
    orphans = concept_service.get_orphan_tags()
    return {
        "total_orphans": len(orphans),
        "orphans": orphans
    }

@router.post("/update-concept-links")
def update_concept_links():
    """Update concept_id links for orphan tags that now have matching concepts"""
    updated_count = concept_service.update_tag_concept_links()
    return {
        "updated": updated_count,
        "message": f"Updated {updated_count} orphan tags with concept links"
    }
