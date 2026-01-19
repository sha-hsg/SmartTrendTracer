from fastapi import APIRouter, Depends, Query
from typing import List, Optional

router = APIRouter()

@router.get("/")
def get_media(
    limit: int = Query(50, ge=1, le=200),
    media_type: Optional[str] = None,
):
    """Get recent media with tweet context"""
    query = db.query(TweetMedia).join(Tweet).options(
        joinedload(TweetMedia.tweet)
    )
    
    if media_type:
        query = query.filter(TweetMedia.type == media_type)
    
    media_items = query.order_by(Tweet.created_at.desc()).limit(limit).all()
    
    result = []
    for media in media_items:
        result.append({
            "media_key": media.media_key,
            "type": media.type,
            "url": media.url,
            "preview_image_url": media.preview_image_url,
            "alt_text": media.alt_text,
            "width": media.width,
            "height": media.height,
            "tweet_id": media.tweet_id,
            "tweet_text": media.tweet.text if media.tweet else None,
            "author_username": media.tweet.author_username if media.tweet else None,
            "created_at": media.tweet.created_at if media.tweet else None
        })
    
    return result

@router.get("/stats")
def get_media_stats():
    """Get media statistics"""
    total = db.query(TweetMedia).count()
    photos = db.query(TweetMedia).filter(TweetMedia.type == "photo").count()
    videos = db.query(TweetMedia).filter(TweetMedia.type == "video").count()
    gifs = db.query(TweetMedia).filter(TweetMedia.type == "animated_gif").count()
    
    return {
        "total": total,
        "photos": photos,
        "videos": videos,
        "gifs": gifs,
        "tweets_with_media": db.query(TweetMedia.tweet_id).distinct().count()
    }