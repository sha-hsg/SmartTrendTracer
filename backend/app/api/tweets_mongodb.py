"""
Complete MongoDB-based tweets API.
All data operations use MongoDB - no SQLite dependencies.
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pymongo import ASCENDING, DESCENDING
from app.database.mongodb import get_database
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel
import logging
import uuid
import json
from bson import ObjectId

from app.services.concept_only_tag_service import ConceptOnlyTagService
from app.services.llm_manager import get_llm_manager

logger = logging.getLogger(__name__)
router = APIRouter()

# MongoDB connection
db = get_database()

# Initialize services
concept_service = ConceptOnlyTagService()
llm_manager = get_llm_manager()

# In-memory batch annotation task tracking
batch_annotation_tasks: Dict[str, Dict] = {}

# Cache for profile images to avoid repeated DB lookups
_profile_image_cache: Dict[str, Optional[str]] = {}

def get_profile_images_for_usernames(usernames: List[str]) -> Dict[str, Optional[str]]:
    """
    Batch lookup profile images from twitter_accounts collection.
    Returns a dict mapping username -> profile_image_url (or None if not found).
    Uses caching to avoid repeated lookups.
    """
    result = {}
    usernames_to_lookup = []

    # Check cache first
    for username in usernames:
        if username in _profile_image_cache:
            result[username] = _profile_image_cache[username]
        else:
            usernames_to_lookup.append(username)

    # Lookup remaining usernames from DB
    if usernames_to_lookup:
        accounts = list(db.twitter_accounts.find(
            {'username': {'$in': usernames_to_lookup}},
            {'username': 1, 'profile_image_url': 1}
        ))

        for account in accounts:
            username = account.get('username')
            profile_url = account.get('profile_image_url')
            result[username] = profile_url
            _profile_image_cache[username] = profile_url

        # Cache None for usernames not found
        for username in usernames_to_lookup:
            if username not in result:
                result[username] = None
                _profile_image_cache[username] = None

    return result


class BatchAnnotateRequest(BaseModel):
    """Request model for batch annotation"""
    tweet_ids: List[str]
    model: Optional[str] = None  # User-selected model (uses default if None)

@router.get("/", response_model=List[Dict])
@router.get("", response_model=List[Dict])
def get_tweets(
    limit: int = Query(50, ge=1, le=500),
    skip: int = Query(0, ge=0),
    with_media_only: bool = False,
    concept_id: Optional[str] = Query(None, description="Filter by concept ID"),
    include_concepts: bool = Query(True, description="Include full concept details")
):
    """Get recent tweets with concept-based tags from MongoDB"""
    
    # Build query
    query = {}
    
    # Filter by concept if provided
    tweet_ids_filter = None
    if concept_id:
        logger.info(f"Filtering tweets by concept: '{concept_id}'")
        # Convert string concept_id to ObjectId if needed
        try:
            if len(concept_id) == 24:  # Valid ObjectId length
                concept_filter = ObjectId(concept_id)
            else:
                concept_filter = concept_id
        except:
            concept_filter = concept_id
        
        # Find all tweet IDs that have this concept in tag_instances
        tag_instances = list(db.tag_instances.find({
            'content_type': 'tweet',
            'concept_id': concept_filter
        }))
        tweet_ids_filter = [ti['content_id'] for ti in tag_instances]
        logger.info(f"Found {len(tweet_ids_filter)} tweets with concept '{concept_id}'")
        
        if tweet_ids_filter:
            query['_id'] = {'$in': tweet_ids_filter}
        else:
            # No tweets with this concept, return empty result
            return []
    
    if with_media_only:
        query['media'] = {'$ne': []}
    
    # Execute query
    try:
        cursor = db.tweets.find(query).sort('created_at', DESCENDING).skip(skip).limit(limit)
        tweets = list(cursor)
    except Exception as e:
        logger.error(f"Error executing tweet query: {e}")
        tweets = []

    # Batch lookup profile images for all authors
    unique_usernames = list(set(t.get('author_username') for t in tweets if t.get('author_username')))
    profile_images = get_profile_images_for_usernames(unique_usernames)

    # Convert to response model with concepts
    result = []
    for tweet in tweets:
        tweet_id = tweet['_id']
        
        # Get concepts from tag_instances collection
        tag_instances = list(db.tag_instances.find({
            'content_type': 'tweet',
            'content_id': tweet_id
        }))
        
        concept_ids = [ti['concept_id'] for ti in tag_instances]
        
        # Get full concept details if requested
        if include_concepts and concept_ids:
            concepts = []
            for cid in concept_ids:
                concept = concept_service.get_concept_by_id(cid)
                if concept:
                    concepts.append({
                        'concept_id': str(cid),
                        'id': concept.get('id'),
                        'slug': concept.get('slug'),
                        'display_name': concept.get('display_name'),
                        'entity_type': concept.get('entity_type')
                    })
        else:
            concepts = []
        
        # Enhanced retweet handling: try to get full original tweet content
        display_text = tweet.get('full_text', '') or tweet.get('text', '')
        original_tweet_data = None
        is_truncated_retweet = False
        
        # Check if this is a retweet and try to get the original tweet
        if tweet.get('referenced_tweets'):
            for ref in tweet['referenced_tweets']:
                if ref.get('type') == 'retweeted':
                    original_tweet_id = ref.get('id')
                    if original_tweet_id:
                        # Try to find the original tweet in our database
                        original_tweet = db.tweets.find_one({'_id': original_tweet_id})
                        if original_tweet:
                            original_tweet_data = {
                                'id': str(original_tweet['_id']),
                                'author_username': original_tweet.get('author_username'),
                                'text': original_tweet.get('text', ''),
                                'media': original_tweet.get('media', [])
                            }
                            # Restore old logic: Extract RT prefix and combine with full text
                            if display_text.startswith('RT @'):
                                # Extract the RT @username: part and combine with full text
                                rt_parts = display_text.split(':', 1)
                                if len(rt_parts) >= 1:
                                    rt_prefix = rt_parts[0] + ': '
                                    display_text = rt_prefix + original_tweet_data['text']
                                else:
                                    # Fallback if no colon found
                                    display_text = f"RT @{original_tweet_data['author_username']}: {original_tweet_data['text']}"
                        else:
                            # Original tweet not in our database - mark as truncated
                            is_truncated_retweet = display_text.endswith('…') or display_text.endswith('...')
                    break
        
        # Combine media from tweet and original tweet (for retweets)
        all_media = tweet.get('media', [])
        if tweet.get('original_media'):
            all_media.extend(tweet.get('original_media', []))
        
        author_username = tweet.get('author_username')
        tweet_dict = {
            "id": str(tweet['_id']),  # Use MongoDB _id as tweet ID
            "text": display_text,  # Use full text when available
            "author_id": tweet.get('author_id'),
            "author_username": author_username,
            "author_profile_image_url": profile_images.get(author_username),
            "created_at": tweet.get('created_at').isoformat() if tweet.get('created_at') else None,
            "metrics": tweet.get('metrics', {
                "likes": 0,
                "retweets": 0,
                "replies": 0,
                "quotes": 0
            }),
            "media": all_media,  # Include all media (tweet + original if retweet)
            "hashtags": tweet.get('hashtags', []),
            "mentions": tweet.get('mentions', []),
            "urls": tweet.get('urls', []),
            "is_retweet": bool(tweet.get('referenced_tweets', [])),
            "is_truncated_retweet": is_truncated_retweet,
            "original_tweet": original_tweet_data
        }
        
        if include_concepts:
            tweet_dict["concepts"] = concepts
        else:
            tweet_dict["concept_ids"] = [str(cid) for cid in concept_ids]
        
        result.append(tweet_dict)
    
    return result

@router.get("/faceted-search")
def faceted_search(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    authors: Optional[List[str]] = Query(None),
    concept_ids: Optional[List[str]] = Query(None),
    years: Optional[List[int]] = Query(None),
    search: Optional[str] = None,
    exclude_retweets: bool = Query(False),
    annotation_status: Optional[str] = Query(None, description="Filter by annotation status: 'annotated' or 'not_annotated'")
):
    """
    Faceted search for tweets with concept-based filtering using MongoDB
    """
    
    # Build query
    query = {}
    
    # Apply author filter
    if authors:
        query['author_username'] = {'$in': authors}
    
    # Apply concept filter
    if concept_ids:
        # Convert string concept_ids to ObjectIds
        concept_object_ids = []
        for cid in concept_ids:
            try:
                if len(cid) == 24:  # Valid ObjectId length
                    concept_object_ids.append(ObjectId(cid))
                else:
                    # Keep as string for non-ObjectId concept IDs
                    concept_object_ids.append(cid)
            except:
                concept_object_ids.append(cid)
        
        # Find all tweet IDs that have any of these concepts
        tag_instances = list(db.tag_instances.find({
            'content_type': 'tweet',
            'concept_id': {'$in': concept_object_ids}
        }))
        tweet_ids_filter = list(set([ti['content_id'] for ti in tag_instances]))
        logger.info(f"Found {len(tweet_ids_filter)} tweets with concepts {concept_ids}")
        
        if tweet_ids_filter:
            query['_id'] = {'$in': tweet_ids_filter}
        else:
            # No tweets with these concepts
            return {
                "tweets": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "facets": {
                    "authors": [],
                    "concepts": [],
                    "years": []
                }
            }
    
    # Apply year filter
    if years:
        # Convert years to date ranges
        year_conditions = []
        for year in years:
            start_date = datetime(year, 1, 1)
            end_date = datetime(year + 1, 1, 1)
            year_conditions.append({
                'created_at': {
                    '$gte': start_date,
                    '$lt': end_date
                }
            })
        query['$or'] = year_conditions
    
    text_conditions = []

    # Apply search filter
    if search:
        # Check if search contains quotes (exact phrase search)
        if '"' in search:
            # Extract the quoted phrase
            import re
            quoted_match = re.search(r'"([^"]+)"', search)
            if quoted_match:
                # Use regex for exact phrase matching (case insensitive)
                phrase = quoted_match.group(1)
                
                # Build a flexible regex pattern that handles:
                # - Apostrophes (Innovator's vs Innovators)
                # - Variable whitespace
                # - Case insensitivity
                pattern_parts = []
                words = phrase.split()
                
                for word in words:
                    # Handle possessives: "Innovator's" should match "Innovators" and "Innovator's"
                    if "'s" in word:
                        base_word = word.replace("'s", "")
                        # Match base word followed by optional 's or s
                        pattern_parts.append(f"{re.escape(base_word)}(?:'?s)?")
                    elif "'" in word:
                        # Handle other apostrophes (like don't, won't)
                        pattern_parts.append(re.escape(word).replace(r"\'", "'?"))
                    else:
                        pattern_parts.append(re.escape(word))
                
                # Join with flexible whitespace
                regex_pattern = r"\s+".join(pattern_parts)
                text_conditions.append({'text': {'$regex': regex_pattern, '$options': 'i'}})
            else:
                # Fallback to text search if quotes are malformed
                query['$text'] = {'$search': search}
        else:
            # Use MongoDB text search for general searches
            query['$text'] = {'$search': search}

    # Exclude retweets if requested
    if exclude_retweets:
        text_conditions.append({'text': {'$not': {'$regex': '^RT @'}}})

    if text_conditions:
        query.setdefault('$and', [])
        query['$and'].extend(text_conditions)
    
    # Apply annotation status filter
    if annotation_status:
        if annotation_status == 'annotated':
            # Find tweets that have at least one annotation
            annotated_tweet_ids = db.tag_instances.distinct('content_id', {'content_type': 'tweet'})
            if annotated_tweet_ids:
                if query.get('_id'):
                    # Intersect with existing _id filter
                    existing_ids = query['_id'].get('$in', [])
                    query['_id'] = {'$in': list(set(existing_ids) & set(annotated_tweet_ids))}
                else:
                    query['_id'] = {'$in': annotated_tweet_ids}
            else:
                # No annotated tweets
                query['_id'] = {'$in': []}  # Will return no results
        elif annotation_status == 'not_annotated':
            # Find tweets that have NO annotations
            annotated_tweet_ids = db.tag_instances.distinct('content_id', {'content_type': 'tweet'})
            if annotated_tweet_ids:
                if query.get('_id'):
                    # Exclude annotated tweets from existing filter
                    existing_ids = query['_id'].get('$in', [])
                    query['_id'] = {'$in': list(set(existing_ids) - set(annotated_tweet_ids))}
                else:
                    query['_id'] = {'$nin': annotated_tweet_ids}
            # If no annotated tweets exist, all tweets are not annotated (no filter needed)
    
    # Get total count before pagination
    total = db.tweets.count_documents(query)
    
    # Apply pagination
    skip = (page - 1) * page_size
    cursor = db.tweets.find(query).sort('created_at', DESCENDING).skip(skip).limit(page_size)
    tweets = list(cursor)

    # Batch lookup profile images for all authors
    unique_usernames = list(set(t.get('author_username') for t in tweets if t.get('author_username')))
    profile_images = get_profile_images_for_usernames(unique_usernames)

    # Build facets using aggregation pipeline
    
    # Author facets
    author_pipeline = [
        {'$match': query if query else {}},
        {'$group': {
            '_id': '$author_username',
            'count': {'$sum': 1}
        }},
        {'$sort': {'count': -1}}
    ]
    author_facets = list(db.tweets.aggregate(author_pipeline))
    
    # Concept facets - get all concepts with counts
    concept_facets = []
    if not search and not exclude_retweets and not authors and not concept_ids:
        # Use pre-computed counts from concept service
        all_concepts = concept_service.get_all_concepts_with_counts(content_type='tweet')
        concept_facets = all_concepts[:200]
    else:
        # Calculate counts for filtered set of tweets
        # First get the tweet IDs matching the query
        filtered_tweet_ids = [t['_id'] for t in db.tweets.find(query, {'_id': 1})]
        
        if filtered_tweet_ids:
            # Get tag instances for these tweets
            concept_pipeline = [
                {'$match': {
                    'content_type': 'tweet',
                    'content_id': {'$in': filtered_tweet_ids}
                }},
                {'$group': {
                    '_id': '$concept_id',
                    'count': {'$sum': 1}
                }},
                {'$sort': {'count': -1}},
                {'$limit': 200}
            ]
            concept_counts = list(db.tag_instances.aggregate(concept_pipeline))
        else:
            concept_counts = []
        
        # Get concept details
        for cc in concept_counts:
            concept = concept_service.get_concept_by_id(cc['_id'])
            if concept:
                concept_facets.append({
                    'concept_id': str(cc['_id']),
                    'id': concept.get('id'),
                    'slug': concept.get('slug'),
                    'display_name': concept.get('display_name'),
                    'count': cc['count']
                })
    
    # Year facets
    year_pipeline = [
        {'$match': query if query else {}},
        {'$group': {
            '_id': {'$year': '$created_at'},
            'count': {'$sum': 1}
        }},
        {'$sort': {'_id': -1}}  # Most recent year first
    ]
    year_facets = list(db.tweets.aggregate(year_pipeline))
    
    # Convert tweets to response format
    tweet_results = []
    for tweet in tweets:
        tweet_id = tweet['_id']
        
        # Get concepts from tag_instances collection
        tag_instances = list(db.tag_instances.find({
            'content_type': 'tweet',
            'content_id': tweet_id
        }))
        
        concept_ids = [ti['concept_id'] for ti in tag_instances]
        
        # Get concept details
        concepts = []
        for cid in concept_ids:
            concept = concept_service.get_concept_by_id(cid)
            if concept:
                concepts.append({
                    'concept_id': str(cid),
                    'id': concept.get('id'),
                    'slug': concept.get('slug'),
                    'display_name': concept.get('display_name')
                })
        
        # Use full_text if available (for retweets), otherwise use text
        display_text = tweet.get('full_text', '') or tweet.get('text', '')
        
        # Combine media from tweet and original tweet (for retweets)
        all_media = tweet.get('media', [])
        if tweet.get('original_media'):
            all_media.extend(tweet.get('original_media', []))
        
        author_username = tweet.get('author_username')
        tweet_results.append({
            "id": str(tweet['_id']),
            "text": display_text,  # Use full text when available
            "author_id": tweet.get('author_id'),
            "author_username": author_username,
            "author_profile_image_url": profile_images.get(author_username),
            "created_at": tweet.get('created_at').isoformat() if tweet.get('created_at') else None,
            "metrics": tweet.get('metrics', {}),
            "media": all_media,  # Include all media
            "concepts": concepts,
            "concept_ids": [str(cid) for cid in concept_ids],
            "is_retweet": bool(tweet.get('referenced_tweets', []))
        })
    
    # Calculate annotation status facets
    total_tweets_count = db.tweets.count_documents({})
    annotated_tweet_ids = db.tag_instances.distinct('content_id', {'content_type': 'tweet'})
    annotated_count = len(annotated_tweet_ids)
    not_annotated_count = total_tweets_count - annotated_count
    
    annotation_facets = [
        {"status": "annotated", "label": "Annotated", "count": annotated_count},
        {"status": "not_annotated", "label": "Not Annotated", "count": not_annotated_count}
    ]
    
    return {
        "tweets": tweet_results,
        "facets": {
            "authors": [
                {"username": f['_id'], "count": f['count']}
                for f in author_facets
            ],
            "concepts": concept_facets,
            "years": [
                {"year": f['_id'], "count": f['count']}
                for f in year_facets
            ],
            "annotation_status": annotation_facets
        },
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/hierarchy-facets")
def get_hierarchy_facets():
    """Get hierarchical concept facets for tweets"""
    
    # Get all concepts with hierarchy information
    all_concepts = db.tag_concepts_v2.find()
    
    # Build hierarchy
    concepts_by_id = {}
    root_concepts = []
    
    for concept in all_concepts:
        concept_id = str(concept['_id'])
        concepts_by_id[concept_id] = {
            'concept_id': concept_id,
            'id': concept.get('id'),
            'slug': concept.get('slug'),
            'display_name': concept.get('display_name', concept.get('name')),
            'entity_type': concept.get('entity_type'),
            'parents': [str(p) if hasattr(p, '__str__') else p for p in concept.get('parents', [])],
            'children': [],
            'count': 0
        }
    
    # Identify root concepts and build parent-child relationships
    for concept_id, concept in concepts_by_id.items():
        if not concept['parents']:
            root_concepts.append(concept)
        else:
            # Add this concept to its parents' children lists
            for parent_id in concept['parents']:
                if parent_id in concepts_by_id:
                    concepts_by_id[parent_id]['children'].append(concept)
    
    # Get usage counts for all concepts
    pipeline = [
        {'$match': {'content_type': 'tweet'}},
        {'$group': {
            '_id': '$concept_id',
            'count': {'$sum': 1}
        }}
    ]
    
    counts = list(db.tag_instances.aggregate(pipeline))
    count_map = {str(c['_id']): c['count'] for c in counts}
    
    # Update counts in hierarchy
    for concept_id, concept in concepts_by_id.items():
        concept['count'] = count_map.get(concept_id, 0)
    
    # Calculate aggregate counts (parent includes all children)
    def calculate_aggregate_count(concept):
        """Recursively calculate total count including all descendants"""
        total = concept['count']
        for child in concept['children']:
            total += calculate_aggregate_count(child)
        concept['aggregate_count'] = total
        return total
    
    for root in root_concepts:
        calculate_aggregate_count(root)
    
    # Sort roots by aggregate count
    root_concepts.sort(key=lambda x: x.get('aggregate_count', 0), reverse=True)
    
    return {
        'hierarchy': root_concepts,
        'total_concepts': len(concepts_by_id),
        'concepts_with_tweets': len([c for c in concepts_by_id.values() if c['count'] > 0])
    }

@router.get("/{tweet_id}")
def get_tweet(tweet_id: str, include_concepts: bool = True):
    """Get a specific tweet by ID with concepts from MongoDB"""
    
    tweet = db.tweets.find_one({'_id': tweet_id})
    
    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")
    
    # Get concepts from tag_instances collection
    tag_instances = list(db.tag_instances.find({
        'content_type': 'tweet',
        'content_id': tweet_id
    }))
    
    concept_ids = [ti['concept_id'] for ti in tag_instances]
    
    # Get concept details
    concepts = []
    if include_concepts and concept_ids:
        for cid in concept_ids:
            concept = concept_service.get_concept_by_id(cid)
            if concept:
                concepts.append({
                    'concept_id': str(cid),
                    'id': concept.get('id'),
                    'slug': concept.get('slug'),
                    'display_name': concept.get('display_name')
                })
    
    # Use full_text if available (for retweets), otherwise use text
    display_text = tweet.get('full_text', '') or tweet.get('text', '')
    
    # Combine media from tweet and original tweet (for retweets)
    all_media = tweet.get('media', [])
    if tweet.get('original_media'):
        all_media.extend(tweet.get('original_media', []))
    
    # Build response
    result = {
        "id": str(tweet['_id']),
        "text": display_text,  # Use full text when available
        "author_id": tweet.get('author_id'),
        "author_username": tweet.get('author_username'),
        "created_at": tweet.get('created_at').isoformat() if tweet.get('created_at') else None,
        "metrics": tweet.get('metrics', {}),
        "media": all_media,  # Include all media
        "is_retweet": bool(tweet.get('referenced_tweets', []))
    }
    
    if include_concepts:
        result["concepts"] = concepts
    else:
        result["concept_ids"] = concept_ids
    
    return result

@router.post("/{tweet_id}/concepts")
def add_concept_to_tweet(
    tweet_id: str,
    text: str = Query(..., description="Text to create/find concept from")
):
    """Add a concept to a tweet (creates concept if needed)"""
    
    # Check if tweet exists
    tweet = db.tweets.find_one({'_id': tweet_id})
    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")
    
    # Add concept using the service
    success, concept_id = concept_service.add_tag('tweet', tweet_id, text)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to add concept")
    
    # Update tweet's concept_ids in MongoDB
    db.tweets.update_one(
        {'_id': tweet_id},
        {'$addToSet': {'concept_ids': concept_id}}
    )
    
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
    
    # Remove from concept service
    success = concept_service.remove_tag('tweet', tweet_id, concept_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Concept not found on this tweet")
    
    # Update tweet's concept_ids in MongoDB
    db.tweets.update_one(
        {'_id': tweet_id},
        {'$pull': {'concept_ids': concept_id}}
    )
    
    return {"message": "Concept removed successfully"}

@router.get("/stats/overview")
def get_statistics():
    """Get tweet statistics from MongoDB"""

    # Count tweets
    total_tweets = db.tweets.count_documents({})

    # Count tweets with media
    tweets_with_media = db.tweets.count_documents({'media': {'$ne': []}})

    # Count unique authors
    unique_authors = len(db.tweets.distinct('author_username'))

    # Get date range
    oldest_tweet = db.tweets.find_one({}, sort=[('created_at', ASCENDING)])
    newest_tweet = db.tweets.find_one({}, sort=[('created_at', DESCENDING)])

    # Count concepts
    concepts = concept_service.get_all_concepts_with_counts(content_type='tweet')

    # Tweet counts per author (aggregation pipeline)
    author_stats = list(db.tweets.aggregate([
        {'$group': {
            '_id': '$author_username',
            'count': {'$sum': 1},
            'total_likes': {'$sum': '$metrics.like_count'},
            'total_retweets': {'$sum': '$metrics.retweet_count'},
            'latest_tweet': {'$max': '$created_at'}
        }},
        {'$sort': {'count': -1}}
    ]))

    # Format author stats
    authors_by_count = [
        {
            'username': a['_id'],
            'tweet_count': a['count'],
            'total_likes': a.get('total_likes', 0) or 0,
            'total_retweets': a.get('total_retweets', 0) or 0,
            'latest_tweet': a['latest_tweet'].isoformat() if a.get('latest_tweet') else None
        }
        for a in author_stats if a['_id']
    ]

    return {
        "total_tweets": total_tweets,
        "tweets_with_media": tweets_with_media,
        "unique_authors": unique_authors,
        "total_concepts": len(concepts),
        "date_range": {
            "oldest": oldest_tweet['created_at'].isoformat() if oldest_tweet else None,
            "newest": newest_tweet['created_at'].isoformat() if newest_tweet else None
        },
        "top_concepts": concepts[:10] if concepts else [],
        "authors_by_count": authors_by_count
    }


# =============================================================================
# Batch Annotation Endpoints
# =============================================================================

def generate_tag_suggestions_for_text(text: str, model: Optional[str] = None) -> List[Dict]:
    """
    Generate tag suggestions for a given text using LLM.
    Returns list of suggested concepts with display_name, slug, and entity_type.
    """
    # Model mapping for frontend model names to actual model names
    model_mapping = {
        "gpt-5": "gpt-5-2025-08-07",
        "gpt-5.1": "gpt-5.1",
        "gpt-5-mini": "gpt-5-mini",
        "gpt-5-nano": "gpt-5-nano",
        "gpt-4o": "gpt-4o",
        "gpt-4o-mini": "gpt-4o-mini",
        "claude-sonnet-4.5": "claude-sonnet-4-5-20250929",
        "claude-opus-4.1": "claude-opus-4-1-20250805",
        "claude-haiku-4.5": "claude-haiku-4-5-20251001",
        "claude-3.5-sonnet": "claude-sonnet-4-20250514",
        "gemini-3-pro": "gemini-3.0-pro",
        "gemini-2.5-pro": "gemini-2.5-pro",
        "gemini-2.5-flash": "gemini-2.5-flash",
        "gemini-2.5-flash-lite": "gemini-2.5-flash-lite"
    }

    actual_model = model_mapping.get(model, model) if model else "claude-sonnet-4-20250514"

    prompt = f"""Analyze this tweet and suggest relevant concept tags.

Tweet: {text}

Instructions:
1. Suggest 3-5 relevant concepts for this tweet
2. Focus on main topics, technologies, people, organizations mentioned
3. Use snake_case for slugs (e.g., machine_learning, sam_altman)
4. Use proper capitalization for display names (e.g., "Machine Learning", "Sam Altman")

Return as JSON array with format:
[
  {{
    "display_name": "Proper Name",
    "slug": "snake_case_slug",
    "entity_type": "topic|person|organisation|location|event|product"
  }}
]
"""

    try:
        messages = [{"role": "user", "content": prompt}]

        response = llm_manager.completion_sync(
            task_type='tag_suggestion',
            messages=messages,
            user_id='batch_annotation',
            override_params={'model': actual_model} if actual_model else None
        )

        response_text = response.choices[0].message.content

        if response_text:
            # Extract JSON from response (handle markdown code blocks)
            json_text = response_text.strip()
            if json_text.startswith("```json"):
                json_text = json_text[7:]
            if json_text.startswith("```"):
                json_text = json_text[3:]
            if json_text.endswith("```"):
                json_text = json_text[:-3]

            return json.loads(json_text.strip())
    except Exception as e:
        logger.error(f"Error generating tag suggestions: {e}")

    return []


def run_batch_annotation(task_id: str, tweet_ids: List[str], model: Optional[str]):
    """Process batch annotation in background"""

    batch_annotation_tasks[task_id] = {
        "status": "running",
        "progress": 0,
        "total": len(tweet_ids),
        "processed": 0,
        "new_tags_count": 0,
        "skipped_count": 0,
        "error_count": 0,
        "results": {},
        "started_at": datetime.utcnow().isoformat()
    }

    for i, tweet_id in enumerate(tweet_ids):
        try:
            # Get tweet content
            tweet = db.tweets.find_one({"_id": tweet_id})
            if not tweet:
                batch_annotation_tasks[task_id]["results"][tweet_id] = {"error": "not_found"}
                batch_annotation_tasks[task_id]["error_count"] += 1
                continue

            # Get existing concepts for this tweet (to avoid duplicates)
            existing_concepts = concept_service.get_tags_for_content('tweet', tweet_id)
            existing_slugs = {c['slug'] for c in existing_concepts}

            # Generate suggestions using LLM
            tweet_text = tweet.get('full_text', '') or tweet.get('text', '')
            suggestions = generate_tag_suggestions_for_text(tweet_text, model)

            # Apply only NEW concepts
            new_concepts = []
            skipped = 0
            for suggestion in suggestions:
                slug = suggestion.get('slug', '')
                if slug and slug not in existing_slugs:
                    # Add the concept using the service
                    success, concept_id = concept_service.add_tag(
                        content_type='tweet',
                        content_id=tweet_id,
                        text=suggestion['display_name'],
                        preserve_display_name=True
                    )

                    if success:
                        new_concepts.append(suggestion['display_name'])
                        existing_slugs.add(slug)  # Prevent duplicates within same batch
                else:
                    skipped += 1

            batch_annotation_tasks[task_id]["results"][tweet_id] = {
                "status": "success",
                "new_concepts": new_concepts,
                "skipped": skipped
            }
            batch_annotation_tasks[task_id]["new_tags_count"] += len(new_concepts)
            batch_annotation_tasks[task_id]["skipped_count"] += skipped

        except Exception as e:
            logger.error(f"Error annotating tweet {tweet_id}: {e}")
            batch_annotation_tasks[task_id]["results"][tweet_id] = {"error": str(e)}
            batch_annotation_tasks[task_id]["error_count"] += 1

        # Update progress
        batch_annotation_tasks[task_id]["processed"] = i + 1
        batch_annotation_tasks[task_id]["progress"] = int(((i + 1) / len(tweet_ids)) * 100)

    batch_annotation_tasks[task_id]["status"] = "completed"
    batch_annotation_tasks[task_id]["completed_at"] = datetime.utcnow().isoformat()

    logger.info(f"Batch annotation {task_id} completed: {batch_annotation_tasks[task_id]['new_tags_count']} new tags, {batch_annotation_tasks[task_id]['skipped_count']} skipped, {batch_annotation_tasks[task_id]['error_count']} errors")


@router.post("/batch-annotate")
async def batch_annotate_tweets(
    request: BatchAnnotateRequest,
    background_tasks: BackgroundTasks
):
    """
    Start batch annotation of tweets.
    Returns immediately with a task_id for status polling.
    """
    if not request.tweet_ids:
        raise HTTPException(status_code=400, detail="No tweet IDs provided")

    task_id = str(uuid.uuid4())

    # Start background task
    background_tasks.add_task(
        run_batch_annotation,
        task_id,
        request.tweet_ids,
        request.model
    )

    logger.info(f"Started batch annotation task {task_id} for {len(request.tweet_ids)} tweets")

    return {
        "task_id": task_id,
        "status": "started",
        "total": len(request.tweet_ids),
        "message": f"Batch annotation started for {len(request.tweet_ids)} tweets"
    }


@router.get("/batch-annotate/{task_id}/status")
async def get_batch_annotation_status(task_id: str):
    """
    Get the status of a batch annotation task.
    """
    task = batch_annotation_tasks.get(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        "task_id": task_id,
        "status": task["status"],
        "progress": task["progress"],
        "total": task["total"],
        "processed": task["processed"],
        "new_tags_count": task.get("new_tags_count", 0),
        "skipped_count": task.get("skipped_count", 0),
        "error_count": task.get("error_count", 0),
        "started_at": task.get("started_at"),
        "completed_at": task.get("completed_at")
    }
