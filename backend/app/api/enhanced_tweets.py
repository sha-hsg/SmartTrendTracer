"""
Enhanced Tweets API with faceted browsing
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict
from pydantic import BaseModel

router = APIRouter()

class FacetedTweetSearchResponse(BaseModel):
    tweets: List[Dict]
    facets: Dict
    total: int
    page: int
    page_size: int

class HierarchyFacet(BaseModel):
    tag: str
    display_name: str
    count: int
    level: int
    parent: Optional[str] = None

@router.get("/tweets/faceted-search")
def faceted_search_tweets(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    authors: Optional[List[str]] = Query(None),
    tags: Optional[List[str]] = Query(None),
    search: Optional[str] = None,
    exclude_retweets: bool = Query(False),
):
    """
    Faceted search for tweets
    Supports filtering by multiple authors and tags simultaneously
    """
    
    # Base query
    query = db.query(Tweet).options(
        joinedload(Tweet.tags),
        joinedload(Tweet.media)
    )
    
    # Apply author filter
    if authors:
        query = query.filter(Tweet.author_username.in_(authors))
    
    # Apply tag filter with hierarchy support
    if tags:
        # Use TagOntologyService to expand tags to include children and synonyms
        ontology_service = TagOntologyService(db)
        expanded_tags_list = []
        
        for tag in tags:
            # Get all related tags (including children and synonyms)
            related_tags = ontology_service.get_tags_for_filtering(tag)
            expanded_tags_list.append(related_tags)
        
        # If multiple tags specified, find tweets that match ALL tag groups
        if len(expanded_tags_list) == 1:
            # Single tag - just use the expanded list
            query = query.join(Tag).filter(Tag.tag.in_(expanded_tags_list[0]))
        else:
            # Multiple tags - ensure tweet has at least one tag from each group
            subqueries = []
            for expanded_tags in expanded_tags_list:
                subq = db.query(Tag.tweet_id).filter(Tag.tag.in_(expanded_tags)).subquery()
                subqueries.append(subq)
            
            # Find tweets that appear in all subqueries
            tweet_ids = db.query(subqueries[0].c.tweet_id)
            for subq in subqueries[1:]:
                tweet_ids = tweet_ids.filter(subqueries[0].c.tweet_id.in_(
                    db.query(subq.c.tweet_id)
                ))
            
            query = query.filter(Tweet.id.in_(tweet_ids))
    
    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(Tweet.text.ilike(search_term))
    
    # Exclude retweets if requested
    if exclude_retweets:
        # Check if text starts with 'RT @' to identify retweets
        query = query.filter(~Tweet.text.like('RT @%'))
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination
    skip = (page - 1) * page_size
    tweets = query.order_by(desc(Tweet.created_at))\
                 .offset(skip)\
                 .limit(page_size)\
                 .all()
    
    # Get facet counts
    # Author facets - get all authors with tweet counts
    author_facets = db.query(
        Tweet.author_username,
        func.count(Tweet.id).label('count')
    ).group_by(Tweet.author_username)\
     .order_by(desc('count'))\
     .all()
    
    # Tag facets (all tags, no limit to match regular dashboard)
    tag_facets = db.query(
        Tag.tag,
        func.count(Tag.id).label('count')
    ).group_by(Tag.tag)\
     .order_by(desc('count'))\
     .all()
    
    # Format response
    tweets_data = []
    for tweet in tweets:
        tweets_data.append({
            'id': tweet.id,
            'text': tweet.text,
            'author_username': tweet.author_username,
            'tags': [tag.tag for tag in tweet.tags],
            'created_at': tweet.created_at,
            'is_retweet': tweet.text.startswith('RT @') if tweet.text else False,
            'like_count': tweet.like_count,
            'retweet_count': tweet.retweet_count,
            'reply_count': tweet.reply_count,
            'media': [
                {
                    'type': m.type,
                    'url': m.url,
                    'thumbnail_url': m.preview_image_url
                } for m in tweet.media
            ] if tweet.media else []
        })
    
    facets = {
        'authors': [
            {
                'username': username,
                'count': count
            }
            for username, count in author_facets
        ],
        'tags': [
            {'tag': tag, 'count': count}
            for tag, count in tag_facets
        ]
    }
    
    return FacetedTweetSearchResponse(
        tweets=tweets_data,
        facets=facets,
        total=total,
        page=page,
        page_size=page_size
    )

@router.get("/tweets/hierarchy-facets")
    """Get tag hierarchy concepts with tweet counts for faceted browsing"""
    
    ontology_service = TagOntologyService(db)
    
    # Get all concepts
    concepts = db.query(TagConcept).order_by(TagConcept.level, TagConcept.display_name).all()
    
    hierarchy_facets = []
    
    for concept in concepts:
        # Get all tags this concept maps to
        related_tags = ontology_service.get_tags_for_filtering(concept.tag)
        
        # Count tweets with these tags
        tweet_count = db.query(func.count(distinct(Tag.tweet_id))).filter(
            Tag.tag.in_(related_tags)
        ).scalar() or 0
        
        # Only include concepts with tweets
        if tweet_count > 0:
            hierarchy_facets.append({
                'tag': concept.tag,
                'display_name': concept.display_name,
                'count': tweet_count,
                'level': concept.level,
                'parent': db.query(TagConcept.tag).filter(
                    TagConcept.id == concept.parent_id
                ).scalar() if concept.parent_id else None
            })
    
    # Sort by level (root first) then by count
    hierarchy_facets.sort(key=lambda x: (x['level'], -x['count']))
    
    return hierarchy_facets

@router.get("/tweets/by-author/{author_username}")
def get_tweets_by_author(
    author_username: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    tags: Optional[List[str]] = Query(None),
    exclude_retweets: bool = Query(False),
):
    """Get tweets from a specific author with optional tag filtering"""
    
    query = db.query(Tweet).options(
        joinedload(Tweet.tags),
        joinedload(Tweet.media)
    ).filter(Tweet.author_username == author_username)
    
    # Apply tag filter if provided
    if tags:
        tweet_ids_with_tags = db.query(Tag.tweet_id)\
            .filter(Tag.tag.in_(tags))\
            .subquery()
        query = query.filter(Tweet.id.in_(tweet_ids_with_tags))
    
    # Exclude retweets if requested
    if exclude_retweets:
        # Check if text starts with 'RT @' to identify retweets
        query = query.filter(~Tweet.text.like('RT @%'))
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    skip = (page - 1) * page_size
    tweets = query.order_by(desc(Tweet.created_at))\
                 .offset(skip)\
                 .limit(page_size)\
                 .all()
    
    # Get tag statistics for this author
    author_tags = db.query(
        Tag.tag,
        func.count(Tag.id).label('count')
    ).join(Tweet)\
     .filter(Tweet.author_username == author_username)\
     .group_by(Tag.tag)\
     .order_by(desc('count'))\
     .limit(20)\
     .all()
    
    tweets_data = []
    for tweet in tweets:
        tweets_data.append({
            'id': tweet.id,
            'text': tweet.text,
            'author_username': tweet.author_username,
            'tags': [tag.tag for tag in tweet.tags],
            'created_at': tweet.created_at,
            'is_retweet': tweet.text.startswith('RT @') if tweet.text else False,
            'like_count': tweet.like_count,
            'retweet_count': tweet.retweet_count,
            'reply_count': tweet.reply_count,
            'media': [
                {
                    'type': m.type,
                    'url': m.url,
                    'thumbnail_url': m.preview_image_url
                } for m in tweet.media
            ] if tweet.media else []
        })
    
    return {
        'tweets': tweets_data,
        'total': total,
        'page': page,
        'page_size': page_size,
        'author_tags': [
            {'tag': tag, 'count': count}
            for tag, count in author_tags
        ]
    }

@router.get("/tweets/by-tags")
def get_tweets_by_tags(
    tags: List[str] = Query(...),
    mode: str = Query('all', regex='^(all|any)$'),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    authors: Optional[List[str]] = Query(None),
    exclude_retweets: bool = Query(False),
):
    """
    Get tweets by tags
    mode='all': tweets must have ALL specified tags
    mode='any': tweets must have ANY of the specified tags
    """
    
    query = db.query(Tweet).options(
        joinedload(Tweet.tags),
        joinedload(Tweet.media)
    )
    
    if mode == 'all':
        # Tweets must have ALL tags
        tweet_ids_with_all_tags = db.query(Tag.tweet_id)\
            .filter(Tag.tag.in_(tags))\
            .group_by(Tag.tweet_id)\
            .having(func.count(distinct(Tag.tag)) == len(tags))\
            .subquery()
        
        query = query.filter(Tweet.id.in_(tweet_ids_with_all_tags))
    else:
        # Tweets must have ANY tag
        tweet_ids_with_any_tag = db.query(Tag.tweet_id)\
            .filter(Tag.tag.in_(tags))\
            .subquery()
        
        query = query.filter(Tweet.id.in_(tweet_ids_with_any_tag))
    
    # Apply author filter if provided
    if authors:
        query = query.filter(Tweet.author_username.in_(authors))
    
    # Exclude retweets if requested
    if exclude_retweets:
        # Check if text starts with 'RT @' to identify retweets
        query = query.filter(~Tweet.text.like('RT @%'))
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    skip = (page - 1) * page_size
    tweets = query.order_by(desc(Tweet.created_at))\
                 .offset(skip)\
                 .limit(page_size)\
                 .all()
    
    tweets_data = []
    for tweet in tweets:
        tweets_data.append({
            'id': tweet.id,
            'text': tweet.text,
            'author_username': tweet.author_username,
            'tags': [tag.tag for tag in tweet.tags],
            'created_at': tweet.created_at,
            'is_retweet': tweet.text.startswith('RT @') if tweet.text else False,
            'like_count': tweet.like_count,
            'retweet_count': tweet.retweet_count,
            'reply_count': tweet.reply_count,
            'media': [
                {
                    'type': m.type,
                    'url': m.url,
                    'thumbnail_url': m.preview_image_url
                } for m in tweet.media
            ] if tweet.media else []
        })
    
    return {
        'tweets': tweets_data,
        'total': total,
        'page': page,
        'page_size': page_size,
        'filter_mode': mode,
        'filtered_tags': tags
    }

@router.get("/authors")
    """Get all tweet authors with their tweet counts"""
    
    authors = db.query(
        Tweet.author_username,
        func.count(Tweet.id).label('tweet_count'),
        func.max(Tweet.created_at).label('latest_tweet')
    ).group_by(Tweet.author_username)\
     .order_by(desc('tweet_count'))\
     .all()
    
    return [
        {
            'username': username,
            'tweet_count': count,
            'latest_tweet': latest.isoformat() if latest else None
        }
        for username, count, latest in authors
    ]