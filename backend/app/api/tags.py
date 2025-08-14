from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict
from pydantic import BaseModel

from app.models import get_db, Tag, Tweet
from app.services.llm_service import get_llm_service
from app.services.tag_normalizer import get_tag_normalizer

router = APIRouter()

class TagCreate(BaseModel):
    tag: str
    tag_type: str = "manual"
    confidence: float = 1.0

class TagResponse(BaseModel):
    id: int
    tag: str
    tag_type: str
    confidence: float
    tweet_id: str

@router.get("/")
def get_all_tags(db: Session = Depends(get_db)):
    """Get all unique tags with counts"""
    tags = db.query(
        Tag.tag,
        func.count(Tag.id).label("count")
    ).group_by(Tag.tag).order_by(func.count(Tag.id).desc()).all()
    
    return [{"tag": tag, "count": count} for tag, count in tags]

@router.get("/tweet/{tweet_id}")
def get_tweet_tags(tweet_id: str, db: Session = Depends(get_db)):
    """Get all tags for a specific tweet"""
    tags = db.query(Tag).filter(Tag.tweet_id == tweet_id).all()
    return tags

@router.post("/tweet/{tweet_id}")
def add_tag(tweet_id: str, tag_data: TagCreate, db: Session = Depends(get_db)):
    """Add a tag to a tweet with normalization"""
    # Validate tag is not empty
    if not tag_data.tag or not tag_data.tag.strip():
        raise HTTPException(status_code=400, detail="Tag cannot be empty")
    
    # Check if tweet exists
    tweet = db.query(Tweet).filter(Tweet.id == tweet_id).first()
    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")
    
    # Preserve capitalization for AI-suggested tags and manual tags
    if tag_data.tag_type in ["ai-suggested", "llm", "manual"]:
        # Just clean up spaces, preserve capitalization
        final_tag = tag_data.tag.strip().replace(" ", "-")
    else:
        # Normalize the tag for other types
        normalizer = get_tag_normalizer(db)
        final_tag = normalizer.normalize_tag(tag_data.tag)
    
    # Check if tag already exists for this tweet (case-insensitive)
    existing = db.query(Tag).filter(
        Tag.tweet_id == tweet_id,
        func.lower(Tag.tag) == func.lower(final_tag)
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Tag already exists for this tweet")
    
    # Create new tag with preserved or normalized form
    new_tag = Tag(
        tweet_id=tweet_id,
        tag=final_tag,
        tag_type=tag_data.tag_type,
        confidence=tag_data.confidence
    )
    
    db.add(new_tag)
    db.commit()
    db.refresh(new_tag)
    
    return new_tag

@router.delete("/tweet/{tweet_id}/{tag}")
def remove_tag(tweet_id: str, tag: str, db: Session = Depends(get_db)):
    """Remove a tag from a tweet"""
    tag_obj = db.query(Tag).filter(
        Tag.tweet_id == tweet_id,
        Tag.tag == tag
    ).first()
    
    if not tag_obj:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    db.delete(tag_obj)
    db.commit()
    
    return {"message": "Tag removed successfully"}

@router.get("/popular")
def get_popular_tags(limit: int = 20, db: Session = Depends(get_db)):
    """Get most popular tags"""
    tags = db.query(
        Tag.tag,
        func.count(Tag.id).label("count")
    ).group_by(Tag.tag).order_by(
        func.count(Tag.id).desc()
    ).limit(limit).all()
    
    return [{"tag": tag, "count": count} for tag, count in tags]

@router.post("/suggest/{tweet_id}")
def suggest_tags_for_tweet(tweet_id: str, db: Session = Depends(get_db)):
    """Get AI-suggested tags for a specific tweet using both similarity search and LLM"""
    # Get the tweet
    tweet = db.query(Tweet).filter(Tweet.id == tweet_id).first()
    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")
    
    # Get vector store for similarity search
    from app.services.vector_store_openai import get_vector_store
    vector_store = get_vector_store()
    
    # Get LLM service for new tag generation
    llm_service = get_llm_service()
    
    # Check which tags already exist for this tweet
    existing_tags_on_tweet = db.query(Tag.tag).filter(Tag.tweet_id == tweet_id).all()
    existing_tag_names_on_tweet = [t[0] for t in existing_tags_on_tweet]
    
    # 1. Find similar existing tags from the vector store
    similar_tags = []
    try:
        # Adjust similarity threshold based on tweet length
        # Longer tweets need lower threshold due to more diverse content
        tweet_length = len(tweet.text)
        if tweet_length > 500:
            min_sim = 0.35  # Lower threshold for long tweets
        elif tweet_length > 280:
            min_sim = 0.4   # Medium threshold for extended tweets
        else:
            min_sim = 0.5   # Normal threshold for short tweets
        
        # Search for tags similar to the tweet content
        search_results = vector_store.search_similar_tags(
            query_text=tweet.text,
            k=10,  # Get more candidates for long tweets
            min_similarity=min_sim
        )
        
        # Filter out tags already on this tweet
        for tag, score, count in search_results:
            if tag not in existing_tag_names_on_tweet:
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
        suggested_tags = llm_service.suggest_tags(
            tweet_text=tweet.text,
            author=tweet.author_username
        )
        
        # Check if API was successfully used
        api_was_used = "__api_success__" in suggested_tags if suggested_tags else False
        if api_was_used:
            suggested_tags = [tag for tag in suggested_tags if tag != "__api_success__"]
        
        # Get model name from config
        import json
        with open('llm.json', 'r') as f:
            llm_config = json.load(f)
        model_name = llm_config['models']['tag_suggestion']['model']
        
        if api_was_used:
            model_used = model_name
        else:
            model_used = "spacy-fallback"
        
        # Ensure we have at least some tags
        if not suggested_tags:
            print(f"No tags generated for tweet {tweet_id}, using enhanced fallback")
            suggested_tags = llm_service._fallback_tag_extraction(tweet.text)
            model_used = "spacy-empty-response"
            
            if not suggested_tags:
                suggested_tags = [
                    tweet.author_username.lower(),
                    "ai-news",
                    "tech-update"
                ]
                model_used = "generic-fallback"
        
        # Filter out tags that already exist (on tweet or in similar tags)
        similar_tag_names = [t['tag'] for t in similar_tags]
        for tag in suggested_tags:
            if tag not in existing_tag_names_on_tweet and tag not in similar_tag_names:
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
    
    # If we don't have enough suggestions, add some fallback
    if len(similar_tags) + len(new_tags) < 3:
        from datetime import datetime
        month = datetime.now().strftime('%b').lower()
        fallback_tags = [
            {'tag': f"ai-{month}", 'type': 'new', 'model': 'fallback'},
            {'tag': "trending", 'type': 'new', 'model': 'fallback'},
            {'tag': "discussion", 'type': 'new', 'model': 'fallback'}
        ]
        for ft in fallback_tags:
            if ft['tag'] not in existing_tag_names_on_tweet and ft['tag'] not in [t['tag'] for t in similar_tags + new_tags]:
                if len(new_tags) < 5:
                    new_tags.append(ft)
    
    return {
        "tweet_id": tweet_id,
        "existing_suggestions": similar_tags,  # Existing tags from vector store
        "new_suggestions": new_tags,  # New tags from LLM
        "already_tagged": existing_tag_names_on_tweet,  # Tags already on this tweet
        "model_used": model_used,
        "total_suggestions": len(similar_tags) + len(new_tags)
    }

@router.post("/suggest/batch")
def suggest_tags_batch(
    tweet_ids: List[str],
    db: Session = Depends(get_db)
):
    """Get AI-suggested tags for multiple tweets"""
    # Limit batch size
    if len(tweet_ids) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 tweets per batch")
    
    # Get tweets
    tweets = db.query(Tweet).filter(Tweet.id.in_(tweet_ids)).all()
    if not tweets:
        raise HTTPException(status_code=404, detail="No tweets found")
    
    # Prepare tweet data
    tweet_data = [
        {
            "id": tweet.id,
            "text": tweet.text,
            "author": tweet.author_username
        }
        for tweet in tweets
    ]
    
    # Get LLM service
    llm_service = get_llm_service()
    
    try:
        # Get suggestions for all tweets
        suggestions = llm_service.batch_suggest_tags(tweet_data)
        
        return {
            "suggestions": suggestions,
            "count": len(suggestions),
            "model_used": "o1-mini"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating suggestions: {str(e)}")

@router.post("/auto-tag/{tweet_id}")
def auto_tag_tweet(
    tweet_id: str,
    apply_threshold: int = 3,
    db: Session = Depends(get_db)
):
    """Automatically tag a tweet with AI suggestions (applies tags automatically)"""
    # Get the tweet
    tweet = db.query(Tweet).filter(Tweet.id == tweet_id).first()
    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")
    
    # Get LLM service
    llm_service = get_llm_service()
    
    try:
        # Get tag suggestions
        suggested_tags = llm_service.suggest_tags(
            tweet_text=tweet.text,
            author=tweet.author_username
        )
        
        # Only apply top N tags
        tags_to_apply = suggested_tags[:apply_threshold]
        
        # Check existing tags
        existing_tags = db.query(Tag.tag).filter(Tag.tweet_id == tweet_id).all()
        existing_tag_names = [t[0] for t in existing_tags]
        
        # Add new tags
        added_tags = []
        for tag in tags_to_apply:
            if tag not in existing_tag_names:
                new_tag = Tag(
                    tweet_id=tweet_id,
                    tag=tag,
                    tag_type="ai-suggested",
                    confidence=0.8  # Could be improved with actual confidence from LLM
                )
                db.add(new_tag)
                added_tags.append(tag)
        
        db.commit()
        
        return {
            "tweet_id": tweet_id,
            "suggested_tags": suggested_tags,
            "applied_tags": added_tags,
            "already_existed": [t for t in tags_to_apply if t in existing_tag_names],
            "model_used": "o1-mini"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error auto-tagging: {str(e)}")