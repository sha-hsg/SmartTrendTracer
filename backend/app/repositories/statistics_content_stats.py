"""
Data access for app.api.statistics.content_stats (extracted by the arch-audit refactor).

Per-content-type statistics (concepts).
"""
from app.database.mongodb import safe_object_id
from collections import defaultdict
from datetime import datetime
from datetime import timedelta
from datetime import timezone

from app.database.mongodb import get_database

db = get_database()




def get_detailed_concept_statistics(content_type, days, include_hierarchy):
    """Get detailed concept statistics with usage patterns"""

    # Build match conditions
    match_conditions = {}
    if content_type:
        match_conditions['content_type'] = content_type

    # Get concept usage statistics
    concept_pipeline = [
        {'$match': match_conditions},
        {'$group': {
            '_id': '$concept_id',
            'total_usage': {'$sum': 1},
            'content_types': {'$addToSet': '$content_type'},
            'content_ids': {'$addToSet': '$content_id'}
        }},
        {'$sort': {'total_usage': -1}}
    ]

    concept_usage = list(db.tag_instances.aggregate(concept_pipeline))

    # Top 50 concepts (skip orphans)
    top_usages = [u for u in concept_usage[:50] if u['_id']]
    top_ids = [u['_id'] for u in top_usages]

    # Batch-fetch concept documents
    concept_map = {c['_id']: c for c in db.tag_concepts_v2.find({'_id': {'$in': top_ids}})}

    # Batch-count usage by content type for all top concepts (one aggregation
    # instead of 3 count_documents per concept)
    by_type_map = defaultdict(dict)
    for row in db.tag_instances.aggregate([
        {'$match': {'concept_id': {'$in': top_ids}, 'content_type': {'$in': ['tweet', 'paper', 'article']}}},
        {'$group': {'_id': {'concept_id': '$concept_id', 'content_type': '$content_type'}, 'count': {'$sum': 1}}}
    ]):
        by_type_map[row['_id']['concept_id']][row['_id']['content_type']] = row['count']

    # Pre-compute recent usage per concept if a day window was requested
    recent_usage_map = defaultdict(int)
    if days and top_ids:
        date_threshold = datetime.now(timezone.utc) - timedelta(days=days)

        instances = list(db.tag_instances.find(
            {
                'concept_id': {'$in': top_ids},
                'content_type': {'$in': ['tweet', 'paper', 'article']}
            },
            {'concept_id': 1, 'content_type': 1, 'content_id': 1}
        ))

        # Collect content IDs per type
        ids_by_type = defaultdict(set)
        for inst in instances:
            cid = inst.get('content_id')
            if cid:
                ids_by_type[inst['content_type']].add(cid)

        # Batch-check which content items fall into the recent window.
        # Tweets use Twitter-ID strings as _id; papers/articles use ObjectIds
        # (tag_instances stores their _id as string -> convert with ObjectId).
        recent_content = set()  # (content_type, content_id-as-stored)

        tweet_ids = [str(cid) for cid in ids_by_type.get('tweet', set())]
        if tweet_ids:
            for doc in db.tweets.find(
                {'_id': {'$in': tweet_ids}, 'created_at': {'$gte': date_threshold}},
                {'_id': 1}
            ):
                recent_content.add(('tweet', doc['_id']))

        for ctype, collection, date_field in (
            ('paper', db.papers, 'created_at'),
            ('article', db.articles, 'published_at'),
        ):
            stored_by_oid = {}
            for cid in ids_by_type.get(ctype, set()):
                oid = safe_object_id(cid)
                if oid is not None:
                    stored_by_oid[oid] = cid
            if stored_by_oid:
                for doc in collection.find(
                    {'_id': {'$in': list(stored_by_oid.keys())}, date_field: {'$gte': date_threshold}},
                    {'_id': 1}
                ):
                    recent_content.add((ctype, stored_by_oid[doc['_id']]))

        for inst in instances:
            if (inst['content_type'], inst.get('content_id')) in recent_content:
                recent_usage_map[inst['concept_id']] += 1

    # Build detailed concept list
    detailed_concepts = []
    for usage in top_usages:
        concept = concept_map.get(usage['_id'])
        if not concept:
            continue

        concept_data = {
            'concept_id': str(concept['_id']),
            'display_name': concept.get('display_name'),
            'slug': concept.get('slug'),
            'entity_type': concept.get('entity_type'),
            'usage': {
                'total': usage['total_usage'],
                'by_type': by_type_map.get(usage['_id'], {})
            }
        }

        # Add hierarchy info if requested
        if include_hierarchy:
            concept_data['hierarchy'] = {
                'parents': [str(p) for p in concept.get('parents', [])],
                'children': [str(c) for c in concept.get('children', [])],
                'level': len(concept.get('parents', [])),
                'is_poly_hierarchy': len(concept.get('parents', [])) > 1
            }

        # Add recent trend if days specified
        if days:
            recent_count = recent_usage_map.get(usage['_id'], 0)
            concept_data['recent_usage'] = {
                'period_days': days,
                'count': recent_count,
                'percentage_of_total': round((recent_count / usage['total_usage']) * 100, 1) if usage['total_usage'] > 0 else 0
            }

        detailed_concepts.append(concept_data)

    # Get orphan statistics
    orphan_count = db.tag_instances.count_documents({'concept_id': None})

    return {
        "content_type_filter": content_type,
        "period_days": days,
        "total_concepts_used": len(concept_usage),
        "orphan_assignments": orphan_count,
        "concepts": detailed_concepts,
        "statistics": {
            "most_used": detailed_concepts[0] if detailed_concepts else None,
            "poly_hierarchy_count": sum(1 for c in detailed_concepts if c.get('hierarchy', {}).get('is_poly_hierarchy', False)),
            "average_usage": round(sum(c['usage']['total'] for c in detailed_concepts) / len(detailed_concepts), 1) if detailed_concepts else 0
        }
    }

