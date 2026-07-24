"""
Animated timeline endpoint for analytics trends.
Split from visualizations.py.
"""

from fastapi import APIRouter, Query
from datetime import timedelta
from collections import Counter, defaultdict
from bson import ObjectId

from .utils import (
    logger,
    db,
    get_date_range,
    count_tags_for_content,
    fetch_tweets_in_range,
    fetch_articles_in_range,
    fetch_papers_in_range,
)

router = APIRouter()


@router.get("/animated-timeline")
def get_animated_timeline_data(
    days: int = Query(30, ge=7, le=90, description="Number of days to analyze"),
    top_n: int = Query(15, ge=5, le=30, description="Number of top concepts to track")
):
    """
    Get animated timeline data showing concept rankings over time.
    Returns daily frames with concept positions for bar chart race animation.
    """
    start_date, end_date = get_date_range(days)

    # Entity type colors
    colors = {
        'person': '#3B82F6',
        'organisation': '#10B981',
        'location': '#F59E0B',
        'concept': '#8B5CF6',
        'product': '#EC4899',
        'event': '#14B8A6',
        'technology': '#F97316',
        'default': '#6366F1'
    }

    # Get cumulative counts by day for top concepts
    daily_counts = defaultdict(lambda: defaultdict(int))

    # First pass: collect all data to find top concepts
    all_concept_counts = Counter()

    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        date_end = current_date + timedelta(days=1)

        # Fetch content for this day
        tweets = fetch_tweets_in_range(db, current_date, date_end)
        articles = fetch_articles_in_range(db, current_date, date_end)
        papers = fetch_papers_in_range(db, current_date, date_end)

        day_counts = Counter()
        count_tags_for_content(db, tweets, 'tweet', day_counts)
        count_tags_for_content(db, articles, 'article', day_counts)
        count_tags_for_content(db, papers, 'paper', day_counts)

        for concept_id, count in day_counts.items():
            daily_counts[date_str][str(concept_id)] += count
            all_concept_counts[concept_id] += count

        current_date += timedelta(days=1)

    # Get top N concepts overall
    top_concept_ids = [str(cid) for cid, _ in all_concept_counts.most_common(top_n)]

    # Get concept details
    concepts_info = {}
    for cid in top_concept_ids:
        try:
            concept = db.tag_concepts_v2.find_one({'_id': ObjectId(cid)})
            if concept:
                entity_type = concept.get('entity_type', 'concept')
                concepts_info[cid] = {
                    'concept_id': cid,
                    'display_name': concept.get('display_name', 'Unknown'),
                    'color': colors.get(entity_type, colors['default']),
                    'total_value': all_concept_counts.get(ObjectId(cid), 0)
                }
        except Exception:
            pass

    # Build frames with cumulative counts
    frames = []
    cumulative = defaultdict(int)

    dates = sorted(daily_counts.keys())
    for date_str in dates:
        # Add today's counts to cumulative
        for cid in top_concept_ids:
            cumulative[cid] += daily_counts[date_str].get(cid, 0)

        # Build rankings for this frame
        rankings = []
        for rank, cid in enumerate(sorted(top_concept_ids, key=lambda x: cumulative[x], reverse=True)):
            if cid in concepts_info:
                rankings.append({
                    'concept_id': cid,
                    'display_name': concepts_info[cid]['display_name'],
                    'value': cumulative[cid],
                    'rank': rank + 1,
                    'color': concepts_info[cid]['color']
                })

        frames.append({
            'date': date_str,
            'rankings': rankings
        })

    return {
        "period_days": days,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "frames": frames,
        "concepts": list(concepts_info.values()),
        "date_range": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        }
    }
