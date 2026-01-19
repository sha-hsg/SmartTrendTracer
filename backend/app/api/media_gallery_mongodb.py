"""
MongoDB-based Media Gallery API for Twitter media
"""

from fastapi import APIRouter, Query, HTTPException
from pymongo import DESCENDING, ASCENDING
from app.database.mongodb import get_database
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# MongoDB connection
db = get_database()

@router.get("/gallery")
async def get_media_gallery(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    days: int = Query(7, ge=1, le=365),
    media_type: Optional[str] = Query(None, description="Filter by media type: photo, video, animated_gif"),
    author: Optional[str] = Query(None, description="Filter by author username"),
    sort_by: str = Query("date_desc", description="Sort order: date_desc, date_asc, engagement")
):
    """Get media items from tweets with pagination and filters"""
    
    # Calculate date filter
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # Build query
    query = {
        'created_at': {'$gte': cutoff_date},
        'media': {'$exists': True, '$ne': []}
    }
    
    if author:
        query['author_username'] = author
    
    # Get tweets with media
    sort_order = DESCENDING if sort_by == "date_desc" else ASCENDING
    sort_field = 'created_at'
    
    if sort_by == "engagement":
        # For engagement, we'll sort by likes + retweets
        sort_field = [('metrics.likes', DESCENDING), ('metrics.retweets', DESCENDING)]
    else:
        sort_field = [(sort_field, sort_order)]
    
    skip = (page - 1) * page_size
    
    tweets_with_media = list(
        db.tweets.find(query)
        .sort(sort_field)
        .skip(skip)
        .limit(page_size)
    )
    
    # Transform media items
    media_items = []
    for tweet in tweets_with_media:
        # Handle both regular media and original_media (from retweets)
        all_media = tweet.get('media', [])
        if tweet.get('original_media'):
            all_media.extend(tweet.get('original_media', []))
        
        for media in all_media:
            # Filter by media type if specified
            if media_type and media.get('type') != media_type:
                continue
                
            media_item = {
                'id': f"{tweet['_id']}_{media.get('media_key', '')}",
                'tweet_id': str(tweet['_id']),
                'type': media.get('type', 'photo'),
                'url': media.get('url', ''),
                'thumbnail_url': media.get('preview_image_url') or media.get('url', ''),
                'width': media.get('width'),
                'height': media.get('height'),
                'duration_ms': media.get('duration_ms'),
                'author_username': tweet.get('author_username', ''),
                'author_id': tweet.get('author_id', ''),
                'tweet_text': tweet.get('text', '')[:100],  # First 100 chars
                'created_at': tweet.get('created_at').isoformat() if tweet.get('created_at') else None,
                'metrics': tweet.get('metrics', {
                    'likes': 0,
                    'retweets': 0,
                    'replies': 0
                })
            }
            media_items.append(media_item)
    
    # Get total count
    total_count = db.tweets.count_documents(query)
    
    return {
        'media': media_items,
        'total': total_count,
        'page': page,
        'page_size': page_size,
        'total_pages': (total_count + page_size - 1) // page_size
    }

@router.get("/stats")
async def get_media_stats(
    days: int = Query(7, ge=1, le=365)
):
    """Get statistics about media in tweets"""
    
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # Count tweets with media
    tweets_with_media = db.tweets.count_documents({
        'created_at': {'$gte': cutoff_date},
        'media': {'$exists': True, '$ne': []}
    })
    
    # Count total tweets in period
    total_tweets = db.tweets.count_documents({
        'created_at': {'$gte': cutoff_date}
    })
    
    # Get media type breakdown using aggregation
    pipeline = [
        {'$match': {
            'created_at': {'$gte': cutoff_date},
            'media': {'$exists': True, '$ne': []}
        }},
        {'$unwind': '$media'},
        {'$group': {
            '_id': '$media.type',
            'count': {'$sum': 1}
        }}
    ]
    
    media_types = list(db.tweets.aggregate(pipeline))
    type_breakdown = {item['_id']: item['count'] for item in media_types if item['_id']}
    
    # Get top authors with media
    author_pipeline = [
        {'$match': {
            'created_at': {'$gte': cutoff_date},
            'media': {'$exists': True, '$ne': []}
        }},
        {'$group': {
            '_id': '$author_username',
            'count': {'$sum': 1},
            'total_media': {'$sum': {'$size': '$media'}}
        }},
        {'$sort': {'total_media': -1}},
        {'$limit': 10}
    ]
    
    top_authors = list(db.tweets.aggregate(author_pipeline))
    
    return {
        'period_days': days,
        'tweets_with_media': tweets_with_media,
        'total_tweets': total_tweets,
        'media_percentage': round((tweets_with_media / total_tweets * 100) if total_tweets > 0 else 0, 2),
        'media_types': type_breakdown,
        'top_authors': [
            {
                'username': author['_id'],
                'tweet_count': author['count'],
                'media_count': author['total_media']
            }
            for author in top_authors
        ]
    }

@router.get("/authors")
async def get_media_authors(
    days: int = Query(7, ge=1, le=365)
):
    """Get list of authors who have posted media"""
    
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # Get authors with media using aggregation
    pipeline = [
        {'$match': {
            'created_at': {'$gte': cutoff_date},
            'media': {'$exists': True, '$ne': []}
        }},
        {'$group': {
            '_id': '$author_username',
            'media_count': {'$sum': {'$size': '$media'}},
            'tweet_count': {'$sum': 1}
        }},
        {'$sort': {'media_count': -1}}
    ]
    
    authors = list(db.tweets.aggregate(pipeline))
    
    return [
        {
            'username': author['_id'],
            'media_count': author['media_count'],
            'tweet_count': author['tweet_count']
        }
        for author in authors
    ]

@router.get("/types")
async def get_media_types():
    """Get available media types"""
    
    # Get distinct media types
    pipeline = [
        {'$match': {'media': {'$exists': True, '$ne': []}}},
        {'$unwind': '$media'},
        {'$group': {
            '_id': '$media.type',
            'count': {'$sum': 1}
        }},
        {'$sort': {'count': -1}}
    ]
    
    media_types = list(db.tweets.aggregate(pipeline))
    
    return [
        {
            'type': mt['_id'] if mt['_id'] else 'unknown',
            'count': mt['count'],
            'label': mt['_id'].replace('_', ' ').title() if mt['_id'] else 'Unknown'
        }
        for mt in media_types
    ]

@router.get("/tweet/{tweet_id}/media")
async def get_tweet_media(tweet_id: str):
    """Get all media from a specific tweet"""
    
    tweet = db.tweets.find_one({'_id': tweet_id})
    
    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")
    
    # Get all media
    all_media = tweet.get('media', [])
    if tweet.get('original_media'):
        all_media.extend(tweet.get('original_media', []))
    
    return {
        'tweet_id': tweet_id,
        'author_username': tweet.get('author_username'),
        'created_at': tweet.get('created_at').isoformat() if tweet.get('created_at') else None,
        'media': all_media,
        'text': tweet.get('text', '')
    }
