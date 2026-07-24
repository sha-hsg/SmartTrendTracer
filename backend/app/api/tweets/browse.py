from fastapi import APIRouter, HTTPException, Query
from pymongo import DESCENDING
from typing import List, Optional, Dict
from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId

from .utils import (
    logger, db, concept_service,
    get_profile_images_for_usernames,
)
from .browse_helpers import (
    build_concept_id_filter,
    get_tweet_ids_for_concepts,
    build_search_conditions,
    apply_annotation_status_filter,
    build_facets,
    tweet_to_response_dict,
    build_hierarchy_tree,
)

router = APIRouter()


@router.get("/", response_model=List[Dict])
def get_tweets(
    limit: int = Query(50, ge=1, le=500),
    skip: int = Query(0, ge=0, le=100000),
    with_media_only: bool = False,
    concept_id: Optional[str] = Query(None, description="Filter by concept ID"),
    include_concepts: bool = Query(True, description="Include full concept details")
):
    query = {}

    tweet_ids_filter = None
    if concept_id:
        logger.info(f"Filtering tweets by concept: '{concept_id}'")
        try:
            if len(concept_id) == 24:
                concept_filter = ObjectId(concept_id)
            else:
                concept_filter = concept_id
        except (InvalidId, TypeError) as e:
            logger.debug(f"concept_id '{concept_id}' is not a valid ObjectId: {e}")
            concept_filter = concept_id

        tag_instances = list(db.tag_instances.find({
            'content_type': 'tweet',
            'concept_id': concept_filter
        }))
        tweet_ids_filter = [ti['content_id'] for ti in tag_instances]
        logger.info(f"Found {len(tweet_ids_filter)} tweets with concept '{concept_id}'")

        if tweet_ids_filter:
            query['_id'] = {'$in': tweet_ids_filter}
        else:
            return []

    if with_media_only:
        query['media'] = {'$exists': True, '$ne': []}

    try:
        cursor = db.tweets.find(query).sort('created_at', DESCENDING).skip(skip).limit(limit)
        tweets = list(cursor)
    except Exception as e:
        logger.error(f"Error executing tweet query: {e}")
        raise HTTPException(status_code=500, detail="Failed to query tweets from database")

    unique_usernames = list(set(t.get('author_username') for t in tweets if t.get('author_username')))
    profile_images = get_profile_images_for_usernames(unique_usernames)

    result = []
    for tweet in tweets:
        tweet_dict = tweet_to_response_dict(
            tweet, profile_images,
            include_concepts=include_concepts,
            include_retweet_expansion=True
        )
        result.append(tweet_dict)

    return result

@router.get("/faceted-search")
def faceted_search(
    page: int = Query(1, ge=1, le=10000),
    page_size: int = Query(50, ge=1, le=200),
    authors: Optional[List[str]] = Query(None),
    concept_ids: Optional[List[str]] = Query(None),
    years: Optional[List[int]] = Query(None),
    search: Optional[str] = None,
    exclude_retweets: bool = Query(False),
    annotation_status: Optional[str] = Query(None, description="Filter by annotation status: 'annotated' or 'not_annotated'")
):
    query = {}

    if authors:
        query['author_username'] = {'$in': authors}

    if concept_ids:
        concept_object_ids = build_concept_id_filter(concept_ids)

        tweet_ids_filter = get_tweet_ids_for_concepts(concept_object_ids)
        logger.info(f"Found {len(tweet_ids_filter)} tweets with concepts {concept_ids}")

        if tweet_ids_filter:
            query['_id'] = {'$in': tweet_ids_filter}
        else:
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

    if years:
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

    if search:
        search_conditions, text_search = build_search_conditions(search)
        text_conditions.extend(search_conditions)
        if text_search:
            query['$text'] = text_search

    if exclude_retweets:
        text_conditions.append({'text': {'$not': {'$regex': '^RT @'}}})

    if text_conditions:
        query.setdefault('$and', [])
        query['$and'].extend(text_conditions)

    if annotation_status:
        apply_annotation_status_filter(query, annotation_status)

    total = db.tweets.count_documents(query)

    skip = (page - 1) * page_size
    cursor = db.tweets.find(query).sort('created_at', DESCENDING).skip(skip).limit(page_size)
    tweets = list(cursor)

    unique_usernames = list(set(t.get('author_username') for t in tweets if t.get('author_username')))
    profile_images = get_profile_images_for_usernames(unique_usernames)

    facets = build_facets(query, search, exclude_retweets, authors, concept_ids)

    tweet_results = []
    for tweet in tweets:
        tweet_dict = tweet_to_response_dict(tweet, profile_images, include_concepts=True)
        tweet_dict["concept_ids"] = [str(cid) for cid in
                                     [ti['concept_id'] for ti in db.tag_instances.find({
                                         'content_type': 'tweet',
                                         'content_id': tweet['_id']
                                     })]]
        tweet_results.append(tweet_dict)

    return {
        "tweets": tweet_results,
        "facets": facets,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/hierarchy-facets")
def get_hierarchy_facets():
    return build_hierarchy_tree()

@router.get("/{tweet_id}")
def get_tweet(tweet_id: str, include_concepts: bool = True):
    tweet = db.tweets.find_one({'_id': tweet_id})

    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")

    tag_instances = list(db.tag_instances.find({
        'content_type': 'tweet',
        'content_id': tweet_id
    }))

    concept_ids = [ti['concept_id'] for ti in tag_instances]

    concepts = []
    if include_concepts and concept_ids:
        concepts_lookup = concept_service.get_concepts_by_ids(concept_ids)
        for cid in concept_ids:
            concept = concepts_lookup.get(str(cid))
            if concept:
                concepts.append({
                    'concept_id': str(cid),
                    'id': concept.get('id'),
                    'slug': concept.get('slug'),
                    'display_name': concept.get('display_name')
                })

    display_text = tweet.get('full_text', '') or tweet.get('text', '')

    all_media = tweet.get('media', [])
    if tweet.get('original_media'):
        all_media.extend(tweet.get('original_media', []))

    result = {
        "id": str(tweet['_id']),
        "text": display_text,
        "author_id": tweet.get('author_id'),
        "author_username": tweet.get('author_username'),
        "created_at": tweet.get('created_at').isoformat() if tweet.get('created_at') else None,
        "metrics": tweet.get('metrics', {}),
        "media": all_media,
        "is_retweet": bool(tweet.get('referenced_tweets', []))
    }

    if include_concepts:
        result["concepts"] = concepts
    else:
        result["concept_ids"] = concept_ids

    return result
