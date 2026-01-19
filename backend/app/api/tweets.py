from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime
import json
import logging

from app.schemas.tweet import TweetResponse, TweetWithMedia
from app.services.unified_tag_service import UnifiedTagService
from app.services.tag_display_service import TagDisplayService
from app.services.slug_normalizer import to_snake_case, to_display_name

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[TweetWithMedia])
def get_tweets(
    limit: int = Query(50, ge=1, le=500),
    skip: int = Query(0, ge=0),
    with_media_only: bool = False,
    tag: Optional[str] = Query(None, description="Filter by tag"),
    use_ontology: bool = Query(True, description="Use tag ontology for hierarchical filtering"),
):
    """Get recent tweets with optional filtering"""
    query = db.query(Tweet).options(
        joinedload(Tweet.media),
        joinedload(Tweet.tags)
    )
    
    # Filter by tag if provided
    if tag:
        tag = tag.strip()
        logger.info(f"Filtering tweets by tag: '{tag}'")
        
        # Use unified tag service for consistent filtering
        unified_service = UnifiedTagService(db)
        query = unified_service.filter_tweets_by_tag(query, tag, use_hierarchy=use_ontology)
        
        # Log the result count for debugging
        count = query.count()
        logger.info(f"Tag filter '{tag}' matched {count} tweets (hierarchy={'enabled' if use_ontology else 'disabled'})")
    
    if with_media_only:
        query = query.join(TweetMedia).distinct()
    
    # Execute query with proper error handling
    try:
        tweets = query.order_by(Tweet.created_at.desc()).offset(skip).limit(limit).all()
        
        # Log results for debugging
        if tag:
            logger.info(f"Tag filter '{tag}' returned {len(tweets)} tweets")
    except Exception as e:
        logger.error(f"Error executing tweet query with tag '{tag}': {e}")
        tweets = []
    
    # Convert to response model
    result = []
    for tweet in tweets:
        tweet_dict = {
            "id": tweet.id,
            "text": tweet.text,
            "author_id": tweet.author_id,
            "author_username": tweet.author_username,
            "created_at": tweet.created_at,
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
            "tags": [
                {
                    "tag": t.tag,
                    "display_name": to_display_name(t.tag),
                    "slug": to_snake_case(t.tag),
                    "type": t.tag_type
                }
                for t in tweet.tags
            ]
        }
        result.append(tweet_dict)
    
    return result

@router.get("/{tweet_id}")
    """Get a specific tweet by ID"""
    tweet = db.query(Tweet).options(
        joinedload(Tweet.media),
        joinedload(Tweet.tags)
    ).filter(Tweet.id == tweet_id).first()
    
    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")
    
    return tweet

@router.get("/stats/summary")
    """Get tweet statistics"""
    total_tweets = db.query(Tweet).count()
    tweets_with_media = db.query(Tweet).join(TweetMedia).distinct().count()
    total_tags = db.query(Tag).count()
    unique_tags = db.query(Tag.tag).distinct().count()
    
    return {
        "total_tweets": total_tweets,
        "tweets_with_media": tweets_with_media,
        "total_tags": total_tags,
        "unique_tags": unique_tags,
        "last_update": db.query(Tweet.created_at).order_by(Tweet.created_at.desc()).first()
    }