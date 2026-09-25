"""
Data access for app.api.trend_analysis_mongodb (extracted by the arch-audit refactor).

Trend Analysis API using MongoDB
Provides comprehensive trend analysis across tweets, papers, and articles
"""
from app.database.mongodb import concept_id_query_variants
from collections import defaultdict
from datetime import datetime
from datetime import timedelta
from datetime import timezone

from app.database.mongodb import get_database

db = get_database()




def get_top_concepts(days, limit, content_type):
    """Get top concepts by usage count over a time period"""

    # Calculate date filter
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

    # Build aggregation pipeline
    match_criteria = {'created_at': {'$gte': cutoff_date}}

    if content_type:
        match_criteria['content_type'] = content_type

    pipeline = [
        {'$match': match_criteria}
    ]

    pipeline.extend([
        {'$group': {
            '_id': '$concept_id',
            'count': {'$sum': 1},
            'content_types': {'$addToSet': '$content_type'},
            'first_seen': {'$min': '$created_at'},
            'last_seen': {'$max': '$created_at'}
        }},
        {'$sort': {'count': -1}},
        {'$limit': limit}
    ])

    # Get counts
    concept_stats = list(db.tag_instances.aggregate(pipeline))

    # Batch-fetch concept details (fixes N+1)
    concept_ids = [s['_id'] for s in concept_stats if s['_id']]
    concept_map = {c['_id']: c for c in db.tag_concepts_v2.find({'_id': {'$in': concept_ids}})}

    results = []
    for stat in concept_stats:
        if stat['_id']:
            concept = concept_map.get(stat['_id'])
            if concept:
                # Parse first_seen/last_seen — now native datetime after migration
                first_seen = stat['first_seen']
                last_seen = stat['last_seen']
                if isinstance(first_seen, str):
                    first_seen = datetime.fromisoformat(first_seen)
                if isinstance(last_seen, str):
                    last_seen = datetime.fromisoformat(last_seen)

                results.append({
                    'concept_id': str(stat['_id']),
                    'display_name': concept.get('display_name', concept.get('name', '')),
                    'slug': concept.get('slug', ''),
                    'entity_type': concept.get('entity_type', 'concept'),
                    'count': stat['count'],
                    'content_types': stat['content_types'],
                    'first_seen': first_seen.isoformat() if isinstance(first_seen, datetime) else str(first_seen),
                    'last_seen': last_seen.isoformat() if isinstance(last_seen, datetime) else str(last_seen),
                    'days_active': (last_seen - first_seen).days + 1
                })

    return {
        'period_days': days,
        'concepts': results,
        'total': len(results)
    }



def get_velocity_leaders(days, limit):
    """Get concepts with highest velocity (growth rate) in recent period"""

    # Define time periods
    current_end = datetime.now(timezone.utc)
    current_start = current_end - timedelta(days=days)
    previous_start = current_start - timedelta(days=days)

    # Get current period counts
    current_pipeline = [
        {'$match': {
            'created_at': {
                '$gte': current_start,
                '$lt': current_end
            }
        }},
        {'$group': {
            '_id': '$concept_id',
            'current_count': {'$sum': 1}
        }}
    ]

    # Get previous period counts
    previous_pipeline = [
        {'$match': {
            'created_at': {
                '$gte': previous_start,
                '$lt': current_start
            }
        }},
        {'$group': {
            '_id': '$concept_id',
            'previous_count': {'$sum': 1}
        }}
    ]

    current_counts = {doc['_id']: doc['current_count']
                     for doc in db.tag_instances.aggregate(current_pipeline)}
    previous_counts = {doc['_id']: doc['previous_count']
                      for doc in db.tag_instances.aggregate(previous_pipeline)}

    # Calculate velocities
    velocities = []
    for concept_id, current_count in current_counts.items():
        previous_count = previous_counts.get(concept_id, 0)

        # Calculate velocity (growth rate)
        if previous_count > 0:
            velocity = ((current_count - previous_count) / previous_count) * 100
        else:
            velocity = 100 if current_count > 0 else 0

        # Calculate acceleration (change in growth rate)
        acceleration = current_count - previous_count

        velocities.append({
            'concept_id': concept_id,
            'current_count': current_count,
            'previous_count': previous_count,
            'velocity': velocity,
            'acceleration': acceleration
        })

    # Sort by velocity
    velocities.sort(key=lambda x: x['velocity'], reverse=True)

    # Batch-fetch concept details for top velocity leaders (fixes N+1)
    top_vel = velocities[:limit]
    vel_concept_ids = [v['concept_id'] for v in top_vel if v['concept_id']]
    vel_concept_map = {c['_id']: c for c in db.tag_concepts_v2.find({'_id': {'$in': vel_concept_ids}})}

    results = []
    for vel in top_vel:
        if vel['concept_id']:
            concept = vel_concept_map.get(vel['concept_id'])
            if concept:
                results.append({
                    'concept_id': str(vel['concept_id']),
                    'display_name': concept.get('display_name', concept.get('name', '')),
                    'slug': concept.get('slug', ''),
                    'entity_type': concept.get('entity_type', 'concept'),
                    'current_period_count': vel['current_count'],
                    'previous_period_count': vel['previous_count'],
                    'velocity_percent': round(vel['velocity'], 1),
                    'acceleration': vel['acceleration'],
                    'trend': 'accelerating' if vel['acceleration'] > 5 else
                            'growing' if vel['acceleration'] > 0 else
                            'stable' if vel['acceleration'] == 0 else 'slowing'
                })

    return {
        'period_days': days,
        'velocity_leaders': results,
        'total': len(results)
    }



def get_rising_trends(days, min_growth, limit):
    """Get concepts that are rising in popularity"""

    # Use shorter comparison periods for rising trends
    comparison_days = min(days, 7)

    current_end = datetime.now(timezone.utc)
    current_start = current_end - timedelta(days=comparison_days)
    previous_start = current_start - timedelta(days=comparison_days)

    # Get current week counts
    current_pipeline = [
        {'$match': {
            'created_at': {
                '$gte': current_start,
                '$lt': current_end
            }
        }},
        {'$group': {
            '_id': '$concept_id',
            'count': {'$sum': 1},
            'unique_authors': {'$addToSet': '$content_id'}
        }}
    ]

    # Get previous week counts
    previous_pipeline = [
        {'$match': {
            'created_at': {
                '$gte': previous_start,
                '$lt': current_start
            }
        }},
        {'$group': {
            '_id': '$concept_id',
            'count': {'$sum': 1}
        }}
    ]

    current_data = list(db.tag_instances.aggregate(current_pipeline))
    previous_counts = {doc['_id']: doc['count']
                      for doc in db.tag_instances.aggregate(previous_pipeline)}

    # Find rising concepts
    rising = []
    for doc in current_data:
        concept_id = doc['_id']
        current_count = doc['count']
        previous_count = previous_counts.get(concept_id, 0)

        # Calculate growth
        if previous_count > 0:
            growth = ((current_count - previous_count) / previous_count) * 100
        else:
            growth = 100 if current_count >= 3 else 0  # New concept needs at least 3 mentions

        if growth >= min_growth:
            rising.append({
                'concept_id': concept_id,
                'current_count': current_count,
                'previous_count': previous_count,
                'growth_percent': growth,
                'unique_sources': len(doc['unique_authors'])
            })

    # Sort by growth
    rising.sort(key=lambda x: x['growth_percent'], reverse=True)

    # Batch-fetch concept details (fixes N+1)
    top_rising = rising[:limit]
    rising_concept_ids = [item['concept_id'] for item in top_rising if item['concept_id']]
    rising_concept_map = {c['_id']: c for c in db.tag_concepts_v2.find({'_id': {'$in': rising_concept_ids}})}

    results = []
    for item in top_rising:
        if item['concept_id']:
            concept = rising_concept_map.get(item['concept_id'])
            if concept:
                results.append({
                    'concept_id': str(item['concept_id']),
                    'display_name': concept.get('display_name', concept.get('name', '')),
                    'slug': concept.get('slug', ''),
                    'entity_type': concept.get('entity_type', 'concept'),
                    'current_mentions': item['current_count'],
                    'previous_mentions': item['previous_count'],
                    'growth_percent': round(item['growth_percent'], 1),
                    'unique_sources': item['unique_sources'],
                    'momentum': 'explosive' if item['growth_percent'] > 200 else
                               'strong' if item['growth_percent'] > 100 else
                               'moderate' if item['growth_percent'] > 50 else 'emerging'
                })

    return {
        'period_days': comparison_days,
        'min_growth_filter': min_growth,
        'rising_concepts': results,
        'total': len(results)
    }



def get_declining_trends(days, min_decline, limit):
    """Get concepts that are declining in popularity"""

    comparison_days = min(days, 7)

    current_end = datetime.now(timezone.utc)
    current_start = current_end - timedelta(days=comparison_days)
    previous_start = current_start - timedelta(days=comparison_days)

    # Get counts for both periods
    current_pipeline = [
        {'$match': {
            'created_at': {
                '$gte': current_start,
                '$lt': current_end
            }
        }},
        {'$group': {
            '_id': '$concept_id',
            'count': {'$sum': 1}
        }}
    ]

    previous_pipeline = [
        {'$match': {
            'created_at': {
                '$gte': previous_start,
                '$lt': current_start
            }
        }},
        {'$group': {
            '_id': '$concept_id',
            'count': {'$sum': 1},
            'peak_day': {'$max': '$created_at'}
        }}
    ]

    current_counts = {doc['_id']: doc['count']
                     for doc in db.tag_instances.aggregate(current_pipeline)}
    previous_data = list(db.tag_instances.aggregate(previous_pipeline))

    # Find declining concepts
    declining = []
    for doc in previous_data:
        concept_id = doc['_id']
        previous_count = doc['count']
        current_count = current_counts.get(concept_id, 0)

        # Calculate decline
        if previous_count > 0:
            decline = ((previous_count - current_count) / previous_count) * 100
        else:
            continue

        if decline >= min_decline:
            declining.append({
                'concept_id': concept_id,
                'current_count': current_count,
                'previous_count': previous_count,
                'decline_percent': decline,
                'peak_day': doc.get('peak_day')
            })

    # Sort by decline
    declining.sort(key=lambda x: x['decline_percent'], reverse=True)

    # Batch-fetch concept details (fixes N+1)
    top_declining = declining[:limit]
    dec_concept_ids = [item['concept_id'] for item in top_declining if item['concept_id']]
    dec_concept_map = {c['_id']: c for c in db.tag_concepts_v2.find({'_id': {'$in': dec_concept_ids}})}

    results = []
    for item in top_declining:
        if item['concept_id']:
            concept = dec_concept_map.get(item['concept_id'])
            if concept:
                peak_day = item.get('peak_day')
                if isinstance(peak_day, datetime):
                    peak_day = peak_day.isoformat()
                results.append({
                    'concept_id': str(item['concept_id']),
                    'display_name': concept.get('display_name', concept.get('name', '')),
                    'slug': concept.get('slug', ''),
                    'entity_type': concept.get('entity_type', 'concept'),
                    'current_mentions': item['current_count'],
                    'previous_mentions': item['previous_count'],
                    'decline_percent': round(item['decline_percent'], 1),
                    'peak_day': peak_day,
                    'status': 'fading' if item['decline_percent'] > 75 else
                             'declining' if item['decline_percent'] > 50 else
                             'cooling' if item['decline_percent'] > 25 else 'stabilizing'
                })

    return {
        'period_days': comparison_days,
        'min_decline_filter': min_decline,
        'declining_concepts': results,
        'total': len(results)
    }



def get_trend_timeline(concept_ids, days, granularity, max_concepts):
    """Get timeline data for specific concepts or overall activity"""

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

    # Determine date format based on granularity
    # After migration, created_at is native datetime — use $dateToString directly
    if granularity == "monthly":
        date_modifier = {'$dateToString': {'format': '%Y-%m', 'date': '$created_at'}}
    elif granularity == "weekly":
        date_modifier = {'$dateToString': {'format': '%G-W%V', 'date': '$created_at'}}  # %G = ISO year (with %Y, year-end weeks collided into January)
    else:  # daily
        date_modifier = {'$dateToString': {'format': '%Y-%m-%d', 'date': '$created_at'}}

    # Build match criteria
    match_criteria = {'created_at': {'$gte': cutoff_date}}

    if concept_ids:
        # Mixed-form concept_id: always filter with all id variants. (The old
        # code dropped the filter entirely when no id was a valid ObjectId,
        # silently returning the unfiltered timeline.)
        id_variants = []
        for cid in concept_ids:
            id_variants.extend(concept_id_query_variants(cid))
        match_criteria['concept_id'] = {'$in': id_variants}

    # Aggregation pipeline for timeline
    pipeline = [
        {'$match': match_criteria},
        {'$addFields': {
            'date_key': date_modifier
        }},
        {'$group': {
            '_id': {
                'date': '$date_key',
                'concept_id': '$concept_id'
            },
            'count': {'$sum': 1},
            'content_types': {'$addToSet': '$content_type'}
        }},
        {'$sort': {'_id.date': 1}}
    ]

    timeline_data = list(db.tag_instances.aggregate(pipeline))

    # Organize data by concept
    concepts_timeline = defaultdict(lambda: defaultdict(int))
    dates_set = set()

    for item in timeline_data:
        date = item['_id']['date']
        concept_id = str(item['_id']['concept_id'])
        concepts_timeline[concept_id][date] = item['count']
        dates_set.add(date)

    # Batch-fetch concept details (fixes N+1). Query BOTH _id forms —
    # legacy slug-id concepts were silently dropped from the series.
    all_concept_ids = []
    for concept_id in concepts_timeline.keys():
        all_concept_ids.extend(concept_id_query_variants(concept_id))
    concept_details = {}
    for c in db.tag_concepts_v2.find({'_id': {'$in': all_concept_ids}}):
        concept_details[str(c['_id'])] = {
            'display_name': c.get('display_name', c.get('name', '')),
            'slug': c.get('slug', ''),
            'entity_type': c.get('entity_type', 'concept')
        }

    # Format timeline series
    sorted_dates = sorted(dates_set)
    series = []

    for concept_id, date_counts in concepts_timeline.items():
        if concept_id in concept_details:
            data_points = []
            for date in sorted_dates:
                data_points.append({
                    'date': date,
                    'value': date_counts.get(date, 0)
                })

            series.append({
                'concept_id': concept_id,
                'name': concept_details[concept_id]['display_name'],
                'data': data_points,
                'total': sum(date_counts.values()),
                'peak_value': max(date_counts.values()) if date_counts else 0,
                'peak_date': max(date_counts.items(), key=lambda x: x[1])[0] if date_counts else None
            })

    # Sort series by total mentions
    series.sort(key=lambda x: x['total'], reverse=True)

    # Limit results based on whether specific concepts were requested
    if concept_ids:
        # When specific concepts are requested, only return those concepts.
        # Compare against ALL id variants — the series key is the ObjectId hex,
        # so a slug/legacy-id request previously matched nothing (empty series
        # while dates/statistics stayed populated).
        requested_ids = set()
        for cid in concept_ids:
            requested_ids.update(str(v) for v in concept_id_query_variants(cid))
        series = [s for s in series if s['concept_id'] in requested_ids]
    elif len(series) > max_concepts:
        # When no specific concepts requested, limit to top N concepts
        series = series[:max_concepts]

    # Calculate overall statistics
    overall_stats = {
        'total_mentions': sum(s['total'] for s in series),
        'unique_concepts': len(series),
        'date_range': {
            'start': sorted_dates[0] if sorted_dates else None,
            'end': sorted_dates[-1] if sorted_dates else None
        },
        'peak_activity': {
            'date': None,
            'count': 0
        }
    }

    # Find peak activity date
    date_totals = defaultdict(int)
    for s in series:
        for point in s['data']:
            date_totals[point['date']] += point['value']

    if date_totals:
        peak_date = max(date_totals.items(), key=lambda x: x[1])
        overall_stats['peak_activity'] = {
            'date': peak_date[0],
            'count': peak_date[1]
        }

    return {
        'period_days': days,
        'granularity': granularity,
        'timeline': series,
        'dates': sorted_dates,
        'statistics': overall_stats
    }

