"""
MongoDB-based Media Gallery API for Twitter media
"""

import re

from fastapi import APIRouter, Query
from pymongo import DESCENDING, ASCENDING
from app.database.mongodb import get_database
from typing import Optional
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# MongoDB connection
db = get_database()

# Server-side sort options (tweet schema uses metrics.like_count / metrics.retweet_count)
GALLERY_SORT_OPTIONS = {
    'date_desc': [('created_at', DESCENDING)],
    'date_asc': [('created_at', ASCENDING)],
    'likes_desc': [('metrics.like_count', DESCENDING), ('created_at', DESCENDING)],
    'retweets_desc': [('metrics.retweet_count', DESCENDING), ('created_at', DESCENDING)],
    'engagement': [('metrics.like_count', DESCENDING), ('metrics.retweet_count', DESCENDING)],
}


def _empty_gallery_response(page: int, page_size: int) -> dict:
    return {
        'media': [],
        'total': 0,
        'page': page,
        'page_size': page_size,
        'total_pages': 0
    }


@router.get("/gallery")
async def get_media_gallery(
    page: int = Query(1, ge=1, le=10000),
    page_size: int = Query(20, ge=1, le=100),
    days: int = Query(7, ge=1, le=365),
    media_type: Optional[str] = Query(None, description="Filter by media type: photo, video, animated_gif"),
    author: Optional[str] = Query(None, description="Filter by author username"),
    search: Optional[str] = Query(None, description="Filter by tweet text (case-insensitive substring)"),
    tag: Optional[str] = Query(None, description="Filter by concept tag (name, display name or slug)"),
    sort_by: str = Query("date_desc", description="Sort order: date_desc, date_asc, likes_desc, retweets_desc, engagement")
):
    """Get media items from tweets with pagination and filters"""

    # Calculate date filter
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

    # Build query (all filters applied before pagination)
    query = {
        'created_at': {'$gte': cutoff_date},
        'media': {'$exists': True, '$ne': []}
    }

    if author:
        query['author_username'] = author

    if media_type:
        query['media.type'] = media_type

    if search:
        query['text'] = {'$regex': re.escape(search), '$options': 'i'}

    if tag:
        # Concept name -> tag_concepts_v2 lookup -> tag_instances -> tweet IDs
        tag_pattern = f'^{re.escape(tag)}$'
        concept = db.tag_concepts_v2.find_one({
            '$or': [
                {'name': {'$regex': tag_pattern, '$options': 'i'}},
                {'display_name': {'$regex': tag_pattern, '$options': 'i'}},
                {'slug': {'$regex': tag_pattern, '$options': 'i'}},
            ]
        })
        if not concept:
            return _empty_gallery_response(page, page_size)

        tweet_ids = [
            ti['content_id'] for ti in db.tag_instances.find({
                'content_type': 'tweet',
                'concept_id': {'$in': [concept['_id'], str(concept['_id'])]}
            })
        ]
        if not tweet_ids:
            return _empty_gallery_response(page, page_size)
        query['_id'] = {'$in': tweet_ids}

    sort_field = GALLERY_SORT_OPTIONS.get(sort_by, GALLERY_SORT_OPTIONS['date_desc'])

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
            # Within a matching tweet, only return media of the requested type
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
                'metrics': tweet.get('metrics', {})
            }
            media_items.append(media_item)

    # Get total count (query already includes all filters)
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
    
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    
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
    
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    
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
