"""
Heatmap and bubble chart endpoints for analytics trends.
Split from visualizations.py.
"""

from fastapi import APIRouter, Query
from datetime import datetime, timedelta, timezone
from collections import Counter, defaultdict

from app.database.mongodb import safe_object_id, concept_id_query_variants

from .utils import (
    normalize_datetime,
    db,
    get_date_range,
    get_previous_period_range,
    get_concept_by_id,
    get_concepts_by_ids,
    count_tags_for_content,
    calculate_tag_velocity,
    fetch_tweets_in_range,
    fetch_articles_in_range,
    fetch_papers_in_range,
    aggregate_concept_usage,
)

router = APIRouter()


@router.get("/heatmap")
def get_trends_heatmap(
    days: int = Query(14, ge=7, le=90, description="Number of days to analyze"),
    top_n: int = Query(20, ge=5, le=50, description="Number of top concepts")
):
    """
    Get heatmap data for concept activity over time.
    Returns a matrix of concepts x dates with activity counts.
    """
    start_date, end_date = get_date_range(days)

    # Get top concepts by usage
    usage_results = aggregate_concept_usage(db, content_type=None, limit=top_n)
    concept_ids = [str(r['_id']) for r in usage_results]

    # Get concept details
    concepts_map = get_concepts_by_ids(db, [r['_id'] for r in usage_results])

    # Initialize date range
    dates = []
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)

    # Fetch content once for the whole range and map content IDs to day buckets
    tweets = fetch_tweets_in_range(db, start_date, end_date)
    articles = fetch_articles_in_range(db, start_date, end_date)
    papers = fetch_papers_in_range(db, start_date, end_date)

    date_set = set(dates)
    date_by_content = {}  # (content_type, content_id_str) -> 'YYYY-MM-DD'
    for content_type, items, date_field in (
        ('tweet', tweets, 'created_at'),
        ('article', articles, 'published_at'),
        ('paper', papers, 'created_at'),
    ):
        for item in items:
            dt = normalize_datetime(item.get(date_field))
            if dt:
                date_str = dt.strftime('%Y-%m-%d')
                if date_str in date_set:
                    date_by_content[(content_type, str(item['_id']))] = date_str

    # Batch-load tag instances per content type (one query per type instead of
    # one find_one per concept x date x content item)
    concept_oids = [r['_id'] for r in usage_results]
    cell_counts = defaultdict(int)  # (concept_id_str, date_str) -> count
    seen_pairs = set()  # dedupe (concept, content) pairs to keep old counting semantics

    for content_type, items in (('tweet', tweets), ('article', articles), ('paper', papers)):
        content_ids = [str(item['_id']) for item in items]
        if not content_ids:
            continue
        cursor = db.tag_instances.find(
            {
                'content_type': content_type,
                'concept_id': {'$in': concept_oids},
                'content_id': {'$in': content_ids}
            },
            {'concept_id': 1, 'content_id': 1}
        )
        for inst in cursor:
            concept_str = str(inst['concept_id'])
            pair = (concept_str, content_type, inst['content_id'])
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            date_str = date_by_content.get((content_type, inst['content_id']))
            if date_str:
                cell_counts[(concept_str, date_str)] += 1

    # Build matrix: concepts x dates
    matrix = []
    concept_names = []
    concept_ids_result = []
    max_value = 0
    min_value = float('inf')

    for concept_oid, concept in concepts_map.items():
        concept_names.append(concept.get('display_name', 'Unknown'))
        concept_ids_result.append(concept_oid)

        row = []
        for date_str in dates:
            total = cell_counts.get((str(concept_oid), date_str), 0)
            row.append(total)

            if total > max_value:
                max_value = total
            if total < min_value:
                min_value = total

        matrix.append(row)

    if min_value == float('inf'):
        min_value = 0

    return {
        "period_days": days,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "concepts": concept_names,
        "concept_ids": concept_ids_result,
        "dates": dates,
        "matrix": matrix,
        "max_value": max_value,
        "min_value": min_value
    }


@router.get("/bubble-chart")
def get_bubble_chart_data(
    days: int = Query(30, ge=7, le=365, description="Number of days to analyze"),
    limit: int = Query(50, ge=10, le=100, description="Maximum bubbles to return")
):
    """
    Get bubble chart data for concept importance and growth.
    X = Days since first occurrence
    Y = Velocity (% change)
    Size = Total count
    Color = Entity type
    """
    start_date, end_date = get_date_range(days)
    previous_start, previous_end = get_previous_period_range(start_date, days)

    # Get current period counts
    current_counts = Counter()
    previous_counts = Counter()

    # Fetch content
    tweets = fetch_tweets_in_range(db, start_date, end_date)
    articles = fetch_articles_in_range(db, start_date, end_date)
    papers = fetch_papers_in_range(db, start_date, end_date)

    prev_tweets = fetch_tweets_in_range(db, previous_start, previous_end)
    prev_articles = fetch_articles_in_range(db, previous_start, previous_end)
    prev_papers = fetch_papers_in_range(db, previous_start, previous_end)

    # Count current
    count_tags_for_content(db, tweets, 'tweet', current_counts)
    count_tags_for_content(db, articles, 'article', current_counts)
    count_tags_for_content(db, papers, 'paper', current_counts)

    # Count previous
    count_tags_for_content(db, prev_tweets, 'tweet', previous_counts)
    count_tags_for_content(db, prev_articles, 'article', previous_counts)
    count_tags_for_content(db, prev_papers, 'paper', previous_counts)

    # Get first seen dates for concepts
    # Using a simple heuristic: earliest content date
    def get_first_seen(concept_id):
        """Find the earliest content date for a concept.

        Tweets use their Twitter ID string as `_id`, so the string content_id
        is used directly against db.tweets; articles/papers use ObjectIds.
        """
        # Sort by tagging time so the sample is the OLDEST 100 instances —
        # unsorted limit(100) made "first seen" the earliest of an arbitrary
        # sample, biased late for any concept with >100 instances. Query all
        # concept_id forms (mixed ObjectId/string storage).
        instances = db.tag_instances.find(
            {'concept_id': {'$in': concept_id_query_variants(concept_id)}},
            {'content_type': 1, 'content_id': 1}
        ).sort('created_at', 1).limit(100)

        ids_by_type = defaultdict(list)
        for inst in instances:
            content_type = inst.get('content_type')
            content_id = inst.get('content_id')
            if not content_type or not content_id:
                continue
            if content_type == 'tweet':
                # Tweet _ids are Twitter ID strings - use as-is
                ids_by_type['tweet'].append(str(content_id))
            else:
                oid = safe_object_id(content_id)
                if oid:
                    ids_by_type[content_type].append(oid)

        lookups = {
            'tweet': (db.tweets, 'created_at'),
            'article': (db.articles, 'published_at'),
            'paper': (db.papers, 'created_at'),
        }

        earliest = None
        for content_type, id_list in ids_by_type.items():
            lookup = lookups.get(content_type)
            if not lookup or not id_list:
                continue
            collection, date_field = lookup
            for doc in collection.find({'_id': {'$in': id_list}}, {date_field: 1}):
                dt = doc.get(date_field)
                if not isinstance(dt, datetime):
                    continue
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                if earliest is None or dt < earliest:
                    earliest = dt

        return earliest if earliest is not None else datetime.now(timezone.utc)

    # Entity type colors
    colors = {
        'person': '#3B82F6',      # Blue
        'organisation': '#10B981', # Green
        'location': '#F59E0B',     # Amber
        'concept': '#8B5CF6',      # Purple
        'product': '#EC4899',      # Pink
        'event': '#14B8A6',        # Teal
        'technology': '#F97316',   # Orange
        'default': '#6366F1'       # Indigo
    }

    bubbles = []
    x_min, x_max = float('inf'), 0
    y_min, y_max = float('inf'), float('-inf')
    z_min, z_max = float('inf'), 0

    for concept_id, count in current_counts.most_common(limit):
        concept = get_concept_by_id(db, concept_id)
        if not concept:
            continue

        previous_count = previous_counts.get(concept_id, 0)
        velocity = calculate_tag_velocity(count, previous_count)

        first_seen = get_first_seen(concept_id)
        days_since_first = (datetime.now(timezone.utc) - first_seen).days

        entity_type = concept.get('entity_type', 'concept')
        color = colors.get(entity_type, colors['default'])

        bubble = {
            'concept_id': str(concept_id),
            'display_name': concept.get('display_name', 'Unknown'),
            'x': days_since_first,
            'y': round(velocity, 1),
            'z': count,
            'entity_type': entity_type,
            'color': color,
            'first_seen': first_seen.isoformat(),
            'last_seen': end_date.isoformat()
        }
        bubbles.append(bubble)

        x_min = min(x_min, days_since_first)
        x_max = max(x_max, days_since_first)
        y_min = min(y_min, velocity)
        y_max = max(y_max, velocity)
        z_min = min(z_min, count)
        z_max = max(z_max, count)

    return {
        "period_days": days,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "data": bubbles,
        "x_range": {"min": x_min if x_min != float('inf') else 0, "max": x_max},
        "y_range": {"min": y_min if y_min != float('inf') else -100, "max": y_max if y_max != float('-inf') else 100},
        "z_range": {"min": z_min if z_min != float('inf') else 0, "max": z_max}
    }
