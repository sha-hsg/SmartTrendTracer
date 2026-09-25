"""
Data access for app.api.tweets.browse (extracted by the arch-audit refactor).


"""
from app.repositories.concepts import ConceptOnlyTagService
from app.repositories.errors import DataAccessError, NotFoundError
from app.repositories.tweet_browse import apply_annotation_status_filter
from app.repositories.tweet_browse import build_concept_id_filter
from app.repositories.tweet_browse import build_facets
from app.repositories.tweet_browse import build_search_conditions
from app.repositories.tweet_browse import get_tweet_ids_for_concepts
from app.repositories.tweet_browse import tweet_to_response_dict
from app.repositories.tweets import get_profile_images_for_usernames
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime
from pymongo import DESCENDING
import logging

concept_service = ConceptOnlyTagService()

from app.database.mongodb import get_database

db = get_database()

logger = logging.getLogger(__name__)




def get_tweets(limit, skip, with_media_only, concept_id, include_concepts):
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
        cursor = db.tweets.find(query).sort([('created_at', DESCENDING), ('_id', DESCENDING)]).skip(skip).limit(limit)
        tweets = list(cursor)
    except Exception as e:
        logger.error(f"Error executing tweet query: {e}")
        raise DataAccessError("Failed to query tweets from database")

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



def faceted_search(page, page_size, authors, concept_ids, years, search, exclude_retweets, annotation_status):
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
    cursor = db.tweets.find(query).sort([('created_at', DESCENDING), ('_id', DESCENDING)]).skip(skip).limit(page_size)
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



def get_tweet(tweet_id, include_concepts):
    tweet = db.tweets.find_one({'_id': tweet_id})

    if not tweet:
        raise NotFoundError("Tweet not found")

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

