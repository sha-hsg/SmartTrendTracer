"""
Trend overview ("at a glance"): hot, declining and stable concepts plus
anomalies for a time window. Used by GET /api/analytics/trends/at-a-glance
and by the weekly digest. Moved unchanged from the router.
"""
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from app.database.mongodb import get_database
from app.repositories import analytics_trends_analysis_queries as queries
from app.repositories.analytics import (
    calculate_tag_velocity,
    count_tags_for_content,
    determine_trend,
    fetch_articles_in_range,
    fetch_papers_in_range,
    fetch_tweets_in_range,
    get_concepts_by_ids,
)


def compute_at_a_glance(hours: int = 48, anomaly_threshold: float = 2.5, limit: int = 10) -> dict:
    """
    Get at-a-glance trend summary with hot topics, declining topics, stable evergreens, and anomalies.

    Hot Topics: >50% increase in activity
    Declining: >30% decrease in activity
    Stable: Consistent activity with <20% change
    Anomalies: Z-score > threshold indicating spikes
    """
    db = get_database()
    from app.services.anomaly_detection import AnomalyDetector, get_concept_activity_by_day

    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(hours=hours)
    days = hours // 24

    # Calculate comparison period (same length as current)
    previous_end = start_date
    previous_start = previous_end - timedelta(hours=hours)

    # Get current and previous period counts
    current_counts = Counter()
    previous_counts = Counter()

    # Fetch content for current period
    tweets = fetch_tweets_in_range(db, start_date, end_date)
    articles = fetch_articles_in_range(db, start_date, end_date)
    papers = fetch_papers_in_range(db, start_date, end_date)

    count_tags_for_content(db, tweets, 'tweet', current_counts)
    count_tags_for_content(db, articles, 'article', current_counts)
    count_tags_for_content(db, papers, 'paper', current_counts)

    # Fetch content for previous period
    prev_tweets = fetch_tweets_in_range(db, previous_start, previous_end)
    prev_articles = fetch_articles_in_range(db, previous_start, previous_end)
    prev_papers = fetch_papers_in_range(db, previous_start, previous_end)

    count_tags_for_content(db, prev_tweets, 'tweet', previous_counts)
    count_tags_for_content(db, prev_articles, 'article', previous_counts)
    count_tags_for_content(db, prev_papers, 'paper', previous_counts)

    # Categorize topics
    hot_topics = []
    declining = []
    stable = []

    # Get sparkline data (last 7 days)
    all_concept_ids = list(set(current_counts.keys()) | set(previous_counts.keys()))
    sparkline_data = get_concept_activity_by_day(db, [str(cid) for cid in all_concept_ids], days=7)

    # Batch-load concepts (avoids one find_one per concept)
    concepts_map = get_concepts_by_ids(db, all_concept_ids)

    # Batch-compute content breakdown per concept (one aggregation per content
    # type instead of one find_one per concept x content item).
    # Counts distinct content items per concept, matching the old semantics.
    breakdown_map = defaultdict(lambda: {'tweets': 0, 'articles': 0, 'papers': 0})
    for content_type, items, key in (
        ('tweet', tweets, 'tweets'),
        ('article', articles, 'articles'),
        ('paper', papers, 'papers'),
    ):
        content_ids = [str(item['_id']) for item in items]
        if not content_ids:
            continue
        pipeline = [
            {'$match': {'content_type': content_type, 'content_id': {'$in': content_ids}}},
            {'$group': {'_id': '$concept_id', 'content_ids': {'$addToSet': '$content_id'}}}
        ]
        for row in queries.tag_instances_aggregate__get_trends_at_a_glance(pipeline):
            if row['_id'] is not None:
                breakdown_map[row['_id']][key] += len(row['content_ids'])

    for concept_id in all_concept_ids:
        concept = concepts_map.get(str(concept_id))
        if not concept:
            continue

        current = current_counts.get(concept_id, 0)
        previous = previous_counts.get(concept_id, 0)
        velocity = calculate_tag_velocity(current, previous)

        # Get sparkline
        sparkline = sparkline_data.get(str(concept_id), [0] * 7)

        # Content breakdown from pre-computed batch lookup
        breakdown = breakdown_map.get(concept_id, {})
        tweet_count = breakdown.get('tweets', 0)
        article_count = breakdown.get('articles', 0)
        paper_count = breakdown.get('papers', 0)

        trend_data = {
            'concept_id': str(concept_id),
            'display_name': concept.get('display_name', 'Unknown'),
            'slug': concept.get('slug', ''),
            'count': current,
            'previous_count': previous,
            'velocity': round(velocity, 1),
            'trend': determine_trend(velocity, rising_threshold=50, declining_threshold=-30),
            'sparkline': sparkline,
            'entity_type': concept.get('entity_type', 'concept'),
            'content_breakdown': {
                'tweets': tweet_count,
                'articles': article_count,
                'papers': paper_count,
                'reddit': 0
            }
        }

        # Categorize
        if velocity > 50:
            trend_data['trend'] = 'hot'
            hot_topics.append(trend_data)
        elif velocity < -30:
            trend_data['trend'] = 'declining'
            declining.append(trend_data)
        elif abs(velocity) < 20 and current >= 3:
            trend_data['trend'] = 'stable'
            stable.append(trend_data)

    # Sort by velocity/count
    hot_topics.sort(key=lambda x: x['velocity'], reverse=True)
    declining.sort(key=lambda x: x['velocity'])
    stable.sort(key=lambda x: x['count'], reverse=True)

    # Get anomalies
    detector = AnomalyDetector(db)
    anomalies_raw = detector.get_all_anomalies(hours=hours, threshold=anomaly_threshold, limit=limit)

    anomalies = []
    for a in anomalies_raw:
        anomalies.append({
            'concept_id': a['concept_id'],
            'display_name': a.get('display_name', 'Unknown'),
            'spike_magnitude': round(a.get('spike_magnitude', 0), 1),
            'z_score': a['z_score'],
            'timestamp': a['timestamp'],
            'baseline_avg': a['baseline_avg'],
            'current_value': a['current_value']
        })

    # Calculate overall statistics
    total_content = len(tweets) + len(articles) + len(papers)
    unique_concepts = len(all_concept_ids)

    velocities = [calculate_tag_velocity(current_counts.get(cid, 0), previous_counts.get(cid, 0))
                  for cid in all_concept_ids if current_counts.get(cid, 0) > 0]
    avg_velocity = sum(velocities) / len(velocities) if velocities else 0

    return {
        "hot_topics": hot_topics[:limit],
        "declining": declining[:limit],
        "stable": stable[:limit],
        "anomalies": anomalies,
        "time_range": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "hours": hours
        },
        "statistics": {
            "total_content": total_content,
            "unique_concepts": unique_concepts,
            "avg_velocity": round(avg_velocity, 1)
        }
    }
