import re
from datetime import datetime
from typing import List, Optional, Dict, Set, Tuple
from bson import ObjectId
from bson.errors import InvalidId

from .utils import logger, db, concept_service


def build_concept_id_filter(concept_ids: List[str]) -> List:
    concept_object_ids = []
    for cid in concept_ids:
        try:
            if len(cid) == 24:
                concept_object_ids.append(ObjectId(cid))
            else:
                concept_object_ids.append(cid)
        except Exception:
            concept_object_ids.append(cid)
    return concept_object_ids


def get_tweet_ids_for_concepts(concept_object_ids: List) -> List:
    tag_instances = list(db.tag_instances.find({
        'content_type': 'tweet',
        'concept_id': {'$in': concept_object_ids}
    }))
    return list(set([ti['content_id'] for ti in tag_instances]))


def build_search_conditions(search: str) -> Tuple[List[Dict], Optional[Dict]]:
    text_conditions = []
    text_search = None

    if '"' in search:
        quoted_match = re.search(r'"([^"]+)"', search)
        if quoted_match:
            phrase = quoted_match.group(1)

            pattern_parts = []
            words = phrase.split()

            for word in words:
                if "'s" in word:
                    base_word = word.replace("'s", "")
                    pattern_parts.append(f"{re.escape(base_word)}(?:'?s)?")
                elif "'" in word:
                    pattern_parts.append(re.escape(word).replace(r"\'", "'?"))
                else:
                    pattern_parts.append(re.escape(word))

            regex_pattern = r"\s+".join(pattern_parts)
            text_conditions.append({'text': {'$regex': regex_pattern, '$options': 'i'}})
        else:
            text_search = {'$search': search}
    else:
        text_search = {'$search': search}

    return text_conditions, text_search


def apply_annotation_status_filter(query: Dict, annotation_status: str):
    annotated_pipeline = [
        {'$match': {'content_type': 'tweet'}},
        {'$group': {'_id': '$content_id'}},
        {'$project': {'content_id': '$_id', '_id': 0}}
    ]
    annotated_results = list(db.tag_instances.aggregate(annotated_pipeline))
    annotated_tweet_ids = [r['content_id'] for r in annotated_results]

    if annotation_status == 'annotated':
        if annotated_tweet_ids:
            object_ids = _convert_to_object_ids(annotated_tweet_ids)

            if query.get('_id'):
                existing_ids = set(query['_id'].get('$in', []))
                query['_id'] = {'$in': list(existing_ids & set(object_ids))}
            else:
                query['_id'] = {'$in': object_ids}
        else:
            query['_id'] = {'$in': []}

    elif annotation_status == 'not_annotated':
        if annotated_tweet_ids:
            object_ids = _convert_to_object_ids(annotated_tweet_ids)

            if query.get('_id'):
                existing_ids = set(query['_id'].get('$in', []))
                query['_id'] = {'$in': list(existing_ids - set(object_ids))}
            else:
                query['_id'] = {'$nin': object_ids}


def _convert_to_object_ids(ids: List) -> List:
    object_ids = []
    for tid in ids:
        try:
            if isinstance(tid, str) and len(tid) == 24:
                object_ids.append(ObjectId(tid))
            else:
                object_ids.append(tid)
        except (InvalidId, TypeError):
            object_ids.append(tid)
    return object_ids


def build_facets(query: Dict, search: Optional[str], exclude_retweets: bool,
                 authors: Optional[List[str]], concept_ids: Optional[List[str]]) -> Dict:
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

    # Concept facets
    concept_facets = []
    if not search and not exclude_retweets and not authors and not concept_ids:
        all_concepts = concept_service.get_all_concepts_with_counts(content_type='tweet')
        concept_facets = all_concepts[:200]
    else:
        filtered_tweet_ids = [t['_id'] for t in db.tweets.find(query, {'_id': 1})]

        if filtered_tweet_ids:
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

        concept_ids_for_facets = [cc['_id'] for cc in concept_counts]
        concepts_lookup = concept_service.get_concepts_by_ids(concept_ids_for_facets)
        for cc in concept_counts:
            concept = concepts_lookup.get(str(cc['_id']))
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
        {'$sort': {'_id': -1}}
    ]
    year_facets = list(db.tweets.aggregate(year_pipeline))

    # Annotation status facets
    total_tweets_count = db.tweets.count_documents({})
    annotated_tweet_ids = set(db.tag_instances.distinct('content_id', {'content_type': 'tweet'}))
    all_tweet_ids = set(str(tid) for tid in db.tweets.distinct('_id'))
    annotated_count = len(annotated_tweet_ids & all_tweet_ids)
    not_annotated_count = total_tweets_count - annotated_count

    annotation_facets = [
        {"status": "annotated", "label": "Annotated", "count": annotated_count},
        {"status": "not_annotated", "label": "Not Annotated", "count": not_annotated_count}
    ]

    return {
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
    }


def tweet_to_response_dict(tweet: Dict, profile_images: Dict,
                           include_concepts: bool = True,
                           include_retweet_expansion: bool = False) -> Dict:
    tweet_id = tweet['_id']

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
                    'display_name': concept.get('display_name'),
                    'entity_type': concept.get('entity_type')
                })

    display_text = tweet.get('full_text', '') or tweet.get('text', '')
    original_tweet_data = None
    is_truncated_retweet = False

    if include_retweet_expansion and tweet.get('referenced_tweets'):
        for ref in tweet['referenced_tweets']:
            if ref.get('type') == 'retweeted':
                original_tweet_id = ref.get('id')
                if original_tweet_id:
                    original_tweet = db.tweets.find_one({'_id': original_tweet_id})
                    if original_tweet:
                        original_tweet_data = {
                            'id': str(original_tweet['_id']),
                            'author_username': original_tweet.get('author_username'),
                            'text': original_tweet.get('text', ''),
                            'media': original_tweet.get('media', [])
                        }
                        if display_text.startswith('RT @'):
                            rt_parts = display_text.split(':', 1)
                            if len(rt_parts) >= 1:
                                rt_prefix = rt_parts[0] + ': '
                                display_text = rt_prefix + original_tweet_data['text']
                            else:
                                display_text = f"RT @{original_tweet_data['author_username']}: {original_tweet_data['text']}"
                    else:
                        is_truncated_retweet = display_text.endswith('\u2026') or display_text.endswith('...')
                break

    all_media = tweet.get('media', [])
    if tweet.get('original_media'):
        all_media.extend(tweet.get('original_media', []))

    author_username = tweet.get('author_username')
    tweet_dict = {
        "id": str(tweet['_id']),
        "text": display_text,
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
        "media": all_media,
        "hashtags": tweet.get('hashtags', []),
        "mentions": tweet.get('mentions', []),
        "urls": tweet.get('urls', []),
        "is_retweet": bool(tweet.get('referenced_tweets', [])),
    }

    if include_retweet_expansion:
        tweet_dict["is_truncated_retweet"] = is_truncated_retweet
        tweet_dict["original_tweet"] = original_tweet_data

    if include_concepts:
        tweet_dict["concepts"] = concepts
    else:
        tweet_dict["concept_ids"] = [str(cid) for cid in concept_ids]

    return tweet_dict


def build_hierarchy_tree() -> Dict:
    all_concepts = db.tag_concepts_v2.find().limit(5000)

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

    for concept_id, concept in concepts_by_id.items():
        if not concept['parents']:
            root_concepts.append(concept)
        else:
            for parent_id in concept['parents']:
                if parent_id in concepts_by_id:
                    concepts_by_id[parent_id]['children'].append(concept)

    pipeline = [
        {'$match': {'content_type': 'tweet'}},
        {'$group': {
            '_id': '$concept_id',
            'count': {'$sum': 1}
        }}
    ]

    counts = list(db.tag_instances.aggregate(pipeline))
    count_map = {str(c['_id']): c['count'] for c in counts}

    for concept_id, concept in concepts_by_id.items():
        concept['count'] = count_map.get(concept_id, 0)

    def calculate_aggregate_count(concept):
        total = concept['count']
        for child in concept['children']:
            total += calculate_aggregate_count(child)
        concept['aggregate_count'] = total
        return total

    for root in root_concepts:
        calculate_aggregate_count(root)

    root_concepts.sort(key=lambda x: x.get('aggregate_count', 0), reverse=True)

    return {
        'hierarchy': root_concepts,
        'total_concepts': len(concepts_by_id),
        'concepts_with_tweets': len([c for c in concepts_by_id.values() if c['count'] > 0])
    }
