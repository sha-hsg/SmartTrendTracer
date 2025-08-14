"""
API endpoints for Twitter Media Gallery
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel

from app.models import get_db, Tweet, TweetMedia, Tag

router = APIRouter()


class MediaItem(BaseModel):
    id: str
    tweet_id: str
    media_key: str
    type: str  # photo, video, animated_gif
    url: Optional[str]
    preview_image_url: Optional[str]
    alt_text: Optional[str]
    width: Optional[int]
    height: Optional[int]
    duration_ms: Optional[int]
    tweet_text: str
    author_username: str
    author_name: Optional[str]
    created_at: str
    likes: int
    retweets: int
    tags: List[str]


class MediaGalleryResponse(BaseModel):
    media: List[MediaItem]
    total: int
    page: int
    page_size: int
    filters: Dict[str, Any]
    stats: Dict[str, Any]


class MediaStats(BaseModel):
    total_media: int
    by_type: Dict[str, int]
    by_author: Dict[str, int]
    by_day: List[Dict[str, Any]]
    top_tags: List[Dict[str, Any]]


@router.get("/gallery", response_model=MediaGalleryResponse)
def get_media_gallery(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    media_type: Optional[str] = Query(None, description="Filter by media type: photo, video, animated_gif"),
    author: Optional[str] = Query(None, description="Filter by author username"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    search: Optional[str] = Query(None, description="Search in tweet text"),
    days: int = Query(7, description="Number of days to look back"),
    sort_by: str = Query("date_desc", description="Sort order: date_desc, date_asc, likes, retweets")
):
    """
    Get media gallery with filtering and pagination
    """
    # Base query
    query = db.query(TweetMedia).join(Tweet)
    
    # Time filter
    if days > 0:
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        query = query.filter(Tweet.created_at >= start_date)
    
    # Media type filter
    if media_type:
        query = query.filter(TweetMedia.type == media_type)
    
    # Author filter
    if author:
        query = query.filter(Tweet.author_username == author)
    
    # Tag filter
    if tag:
        query = query.join(Tag).filter(Tag.tag == tag)
    
    # Search filter
    if search:
        query = query.filter(Tweet.text.ilike(f"%{search}%"))
    
    # Count total before pagination
    total = query.count()
    
    # Sorting
    if sort_by == "date_desc":
        query = query.order_by(desc(Tweet.created_at))
    elif sort_by == "date_asc":
        query = query.order_by(Tweet.created_at)
    elif sort_by == "likes":
        query = query.order_by(desc(Tweet.like_count))
    elif sort_by == "retweets":
        query = query.order_by(desc(Tweet.retweet_count))
    else:
        query = query.order_by(desc(Tweet.created_at))
    
    # Pagination
    offset = (page - 1) * page_size
    media_items = query.offset(offset).limit(page_size).all()
    
    # Format response
    media_list = []
    for media in media_items:
        tweet = media.tweet
        tags = db.query(Tag.tag).filter(Tag.tweet_id == tweet.id).all()
        
        media_list.append(MediaItem(
            id=f"{tweet.id}_{media.media_key}",
            tweet_id=tweet.id,
            media_key=media.media_key,
            type=media.type,
            url=media.url,
            preview_image_url=media.preview_image_url,
            alt_text=media.alt_text,
            width=media.width,
            height=media.height,
            duration_ms=media.duration_ms,
            tweet_text=tweet.text,
            author_username=tweet.author_username,
            author_name=tweet.author_name or tweet.author_username,
            created_at=tweet.created_at.isoformat() if tweet.created_at else "",
            likes=tweet.like_count or 0,
            retweets=tweet.retweet_count or 0,
            tags=[t[0] for t in tags]
        ))
    
    # Calculate stats
    stats = {
        "total_pages": (total + page_size - 1) // page_size,
        "has_next": page * page_size < total,
        "has_prev": page > 1
    }
    
    return MediaGalleryResponse(
        media=media_list,
        total=total,
        page=page,
        page_size=page_size,
        filters={
            "media_type": media_type,
            "author": author,
            "tag": tag,
            "search": search,
            "days": days,
            "sort_by": sort_by
        },
        stats=stats
    )


@router.get("/stats", response_model=MediaStats)
def get_media_stats(
    db: Session = Depends(get_db),
    days: int = Query(7, description="Number of days to look back")
):
    """
    Get media statistics
    """
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Total media count
    total_media = db.query(TweetMedia).join(Tweet).filter(
        Tweet.created_at >= start_date
    ).count()
    
    # By type
    type_counts = db.query(
        TweetMedia.type,
        func.count(TweetMedia.media_key)
    ).join(Tweet).filter(
        Tweet.created_at >= start_date
    ).group_by(TweetMedia.type).all()
    
    by_type = {media_type: count for media_type, count in type_counts}
    
    # By author
    author_counts = db.query(
        Tweet.author_username,
        func.count(TweetMedia.media_key)
    ).join(TweetMedia).filter(
        Tweet.created_at >= start_date
    ).group_by(Tweet.author_username).order_by(
        desc(func.count(TweetMedia.media_key))
    ).limit(10).all()
    
    by_author = {author: count for author, count in author_counts}
    
    # By day
    daily_counts = db.query(
        func.date(Tweet.created_at).label('date'),
        func.count(TweetMedia.media_key).label('count')
    ).join(TweetMedia).filter(
        Tweet.created_at >= start_date
    ).group_by(func.date(Tweet.created_at)).order_by('date').all()
    
    by_day = [
        {"date": str(date), "count": count}
        for date, count in daily_counts
    ]
    
    # Top tags associated with media
    tag_counts = db.query(
        Tag.tag,
        func.count(Tag.tag).label('count')
    ).join(Tweet).join(TweetMedia).filter(
        Tweet.created_at >= start_date
    ).group_by(Tag.tag).order_by(
        desc('count')
    ).limit(20).all()
    
    top_tags = [
        {"tag": tag, "count": count}
        for tag, count in tag_counts
    ]
    
    return MediaStats(
        total_media=total_media,
        by_type=by_type,
        by_author=by_author,
        by_day=by_day,
        top_tags=top_tags
    )


@router.get("/tweet/{tweet_id}/media")
def get_tweet_media(
    tweet_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all media for a specific tweet
    """
    media_items = db.query(TweetMedia).filter(
        TweetMedia.tweet_id == tweet_id
    ).all()
    
    if not media_items:
        raise HTTPException(status_code=404, detail="No media found for this tweet")
    
    tweet = db.query(Tweet).filter(Tweet.id == tweet_id).first()
    
    return {
        "tweet_id": tweet_id,
        "tweet_text": tweet.text if tweet else "",
        "author": tweet.author_username if tweet else "",
        "media": [
            {
                "media_key": m.media_key,
                "type": m.type,
                "url": m.url,
                "preview_image_url": m.preview_image_url,
                "alt_text": m.alt_text,
                "width": m.width,
                "height": m.height,
                "duration_ms": m.duration_ms
            }
            for m in media_items
        ]
    }


@router.get("/authors")
def get_media_authors(
    db: Session = Depends(get_db),
    days: int = Query(30)
):
    """
    Get list of authors who have posted media
    """
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    authors = db.query(
        Tweet.author_username,
        Tweet.author_name,
        func.count(TweetMedia.media_key).label('media_count')
    ).join(TweetMedia).filter(
        Tweet.created_at >= start_date
    ).group_by(
        Tweet.author_username,
        Tweet.author_name
    ).order_by(
        desc('media_count')
    ).all()
    
    return [
        {
            "username": username,
            "name": name,
            "media_count": count
        }
        for username, name, count in authors
    ]


@router.get("/types")
def get_media_types(db: Session = Depends(get_db)):
    """
    Get available media types
    """
    types = db.query(
        TweetMedia.type,
        func.count(TweetMedia.media_key)
    ).group_by(TweetMedia.type).all()
    
    return [
        {
            "type": media_type,
            "count": count,
            "icon": get_media_icon(media_type),
            "label": get_media_label(media_type)
        }
        for media_type, count in types
    ]


def get_media_icon(media_type: str) -> str:
    """Get icon for media type"""
    icons = {
        "photo": "🖼️",
        "video": "🎬",
        "animated_gif": "🎞️"
    }
    return icons.get(media_type, "📎")


def get_media_label(media_type: str) -> str:
    """Get display label for media type"""
    labels = {
        "photo": "Photos",
        "video": "Videos",
        "animated_gif": "GIFs"
    }
    return labels.get(media_type, media_type.title())


@router.post("/download")
def prepare_media_download(
    media_ids: List[str],
    db: Session = Depends(get_db)
):
    """
    Prepare media for bulk download
    """
    # Extract tweet_id and media_key from composite IDs
    download_items = []
    
    for media_id in media_ids:
        parts = media_id.split("_")
        if len(parts) != 2:
            continue
            
        tweet_id, media_key = parts
        media = db.query(TweetMedia).filter(
            TweetMedia.tweet_id == tweet_id,
            TweetMedia.media_key == media_key
        ).first()
        
        if media:
            download_items.append({
                "media_key": media.media_key,
                "url": media.url,
                "type": media.type,
                "filename": f"{media.tweet_id}_{media.media_key}.{get_file_extension(media.type, media.url)}"
            })
    
    return {
        "download_items": download_items,
        "total": len(download_items),
        "ready": True
    }


def get_file_extension(media_type: str, url: str = None) -> str:
    """Determine file extension based on media type and URL"""
    if media_type == "photo":
        if url and "." in url:
            ext = url.split(".")[-1].split("?")[0]
            if ext in ["jpg", "jpeg", "png", "webp", "gif"]:
                return ext
        return "jpg"
    elif media_type == "video":
        return "mp4"
    elif media_type == "animated_gif":
        return "gif"
    return "bin"