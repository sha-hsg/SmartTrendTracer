"""
MongoDB-based Trends Analysis API with Full Implementation
Provides comprehensive trend analysis for tweets, articles, and papers
"""

from fastapi import APIRouter, Query
from app.database.mongodb import get_database
from typing import Dict, List, Optional
from datetime import datetime, timedelta, timezone
from collections import defaultdict, Counter
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# MongoDB connection
db = get_database()


def _batch_fetch_concept_counts(content_type: str, content_ids: List[str]) -> Counter:
    """Batch-fetch tag_instances for a list of content IDs and return concept counts."""
    if not content_ids:
        return Counter()

    instances = db.tag_instances.find({
        'content_type': content_type,
        'content_id': {'$in': content_ids}
    })

    counts = Counter()
    for inst in instances:
        cid = inst.get('concept_id')
        if cid:
            counts[cid] += 1  # Keep as ObjectId
    return counts


def _batch_fetch_concept_counts_by_date(content_type: str, content_ids: List[str],
                                         id_to_date: Dict[str, str]) -> tuple:
    """Batch-fetch tag_instances and return (concept_counts, timeline_concepts, type_counts).

    type_counts: {concept_id: {content_type: count}} for content_breakdown
    """
    concept_counts = Counter()
    timeline_concepts = defaultdict(set)  # date_key -> set of concept_ids
    type_counts = defaultdict(lambda: Counter())  # concept_id -> Counter({type: count})

    if not content_ids:
        return concept_counts, timeline_concepts, type_counts

    instances = db.tag_instances.find({
        'content_type': content_type,
        'content_id': {'$in': content_ids}
    })

    for inst in instances:
        cid = inst.get('concept_id')
        if cid:
            concept_counts[cid] += 1
            type_counts[cid][content_type] += 1
            content_id = inst['content_id']
            date_key = id_to_date.get(content_id)
            if date_key:
                timeline_concepts[date_key].add(cid)

    return concept_counts, timeline_concepts, type_counts


def _batch_lookup_concepts(concept_ids) -> Dict:
    """Batch-lookup concept details from tag_concepts_v2. Returns {ObjectId: doc}."""
    if not concept_ids:
        return {}

    # Ensure all IDs are ObjectId
    oids = []
    for cid in concept_ids:
        if isinstance(cid, ObjectId):
            oids.append(cid)
        else:
            try:
                oids.append(ObjectId(cid))
            except Exception:
                pass

    if not oids:
        return {}

    cursor = db.tag_concepts_v2.find({'_id': {'$in': oids}})
    return {doc['_id']: doc for doc in cursor}


@router.get("/analysis")
def get_trend_analysis(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    content_type: Optional[str] = Query(None, description="Filter by content type (tweet/article/paper)")
):
    """
    Get comprehensive trend analysis across all content types with real data.
    Uses batch queries for performance.
    """

    # Calculate date ranges
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    previous_start = start_date - timedelta(days=days)

    # Initialize
    current_concepts = Counter()
    previous_concepts = Counter()
    content_counts = {"tweets": 0, "articles": 0, "papers": 0}
    timeline_data = defaultdict(lambda: {"tweets": 0, "articles": 0, "papers": 0, "concepts": set()})
    concept_type_counts = defaultdict(lambda: Counter())  # concept_id -> {tweet: N, article: M, paper: P}

    # --- Tweets ---
    if not content_type or content_type == "tweet":
        current_tweets = list(db.tweets.find({'created_at': {'$gte': start_date}}))
        content_counts["tweets"] = len(current_tweets)

        # Build ID-to-date mapping and timeline counts
        id_to_date = {}
        for tweet in current_tweets:
            date_key = tweet['created_at'].strftime('%Y-%m-%d')
            timeline_data[date_key]["tweets"] += 1
            id_to_date[str(tweet['_id'])] = date_key

        # Batch fetch current period concepts
        tweet_ids = list(id_to_date.keys())
        tweet_concepts, tweet_timeline, tweet_type_counts = _batch_fetch_concept_counts_by_date(
            'tweet', tweet_ids, id_to_date
        )
        current_concepts += tweet_concepts
        for dk, cids in tweet_timeline.items():
            timeline_data[dk]["concepts"].update(cids)
        for cid, tc in tweet_type_counts.items():
            concept_type_counts[cid] += tc

        # Batch fetch previous period concepts
        previous_tweets = list(db.tweets.find({
            'created_at': {'$gte': previous_start, '$lt': start_date}
        }))
        prev_tweet_ids = [str(t['_id']) for t in previous_tweets]
        previous_concepts += _batch_fetch_concept_counts('tweet', prev_tweet_ids)

    # --- Articles ---
    if not content_type or content_type == "article":
        current_articles = list(db.articles.find({'published_at': {'$gte': start_date}}))
        content_counts["articles"] = len(current_articles)

        id_to_date = {}
        for article in current_articles:
            date_key = article['published_at'].strftime('%Y-%m-%d')
            timeline_data[date_key]["articles"] += 1
            id_to_date[str(article['_id'])] = date_key

        article_ids = list(id_to_date.keys())
        art_concepts, art_timeline, art_type_counts = _batch_fetch_concept_counts_by_date(
            'article', article_ids, id_to_date
        )
        current_concepts += art_concepts
        for dk, cids in art_timeline.items():
            timeline_data[dk]["concepts"].update(cids)
        for cid, tc in art_type_counts.items():
            concept_type_counts[cid] += tc

        previous_articles = list(db.articles.find({
            'published_at': {'$gte': previous_start, '$lt': start_date}
        }))
        prev_art_ids = [str(a['_id']) for a in previous_articles]
        previous_concepts += _batch_fetch_concept_counts('article', prev_art_ids)

    # --- Papers ---
    if not content_type or content_type == "paper":
        current_papers = list(db.papers.find({'created_at': {'$gte': start_date}}))
        content_counts["papers"] = len(current_papers)

        id_to_date = {}
        for paper in current_papers:
            date_key = paper['created_at'].strftime('%Y-%m-%d')
            timeline_data[date_key]["papers"] += 1
            id_to_date[str(paper['_id'])] = date_key

        paper_ids = list(id_to_date.keys())
        pap_concepts, pap_timeline, pap_type_counts = _batch_fetch_concept_counts_by_date(
            'paper', paper_ids, id_to_date
        )
        current_concepts += pap_concepts
        for dk, cids in pap_timeline.items():
            timeline_data[dk]["concepts"].update(cids)
        for cid, tc in pap_type_counts.items():
            concept_type_counts[cid] += tc

        previous_papers = list(db.papers.find({
            'created_at': {'$gte': previous_start, '$lt': start_date}
        }))
        prev_pap_ids = [str(p['_id']) for p in previous_papers]
        previous_concepts += _batch_fetch_concept_counts('paper', prev_pap_ids)

    # Calculate concept trends
    rising_concepts = []
    stable_concepts = []
    declining_concepts = []

    all_concept_ids = set(current_concepts.keys()) | set(previous_concepts.keys())

    # Batch lookup all concept details at once
    concept_map = _batch_lookup_concepts(all_concept_ids)

    for concept_id in all_concept_ids:
        current_count = current_concepts.get(concept_id, 0)
        previous_count = previous_concepts.get(concept_id, 0)

        # Calculate velocity (change rate)
        if previous_count > 0:
            velocity = ((current_count - previous_count) / previous_count) * 100
        elif current_count > 0:
            velocity = 100  # New concept
        else:
            velocity = 0

        # Get concept details from batch lookup
        concept = concept_map.get(concept_id)
        if concept:
            # Build content breakdown
            type_breakdown = concept_type_counts.get(concept_id, Counter())

            concept_data = {
                'concept_id': str(concept_id),
                'display_name': concept.get('display_name'),
                'current_count': current_count,
                'previous_count': previous_count,
                'velocity': round(velocity, 1),
                'content_breakdown': {
                    'tweets': type_breakdown.get('tweet', 0),
                    'articles': type_breakdown.get('article', 0),
                    'papers': type_breakdown.get('paper', 0)
                }
            }

            if velocity > 20:
                rising_concepts.append(concept_data)
            elif velocity < -20:
                declining_concepts.append(concept_data)
            elif current_count > 0:
                stable_concepts.append(concept_data)

    # Sort by velocity/count
    rising_concepts.sort(key=lambda x: x['velocity'], reverse=True)
    declining_concepts.sort(key=lambda x: x['velocity'])
    stable_concepts.sort(key=lambda x: x['current_count'], reverse=True)

    # Get top concepts (already have concept_map)
    top_concepts = []
    for concept_id, count in current_concepts.most_common(10):
        concept = concept_map.get(concept_id)
        if concept:
            top_concepts.append({
                'concept_id': str(concept_id),
                'display_name': concept.get('display_name'),
                'count': count,
                'entity_type': concept.get('entity_type')
            })

    # Prepare timeline
    timeline = []
    for date in sorted(timeline_data.keys()):
        timeline.append({
            'date': date,
            'tweets': timeline_data[date]['tweets'],
            'articles': timeline_data[date]['articles'],
            'papers': timeline_data[date]['papers'],
            'unique_concepts': len(timeline_data[date]['concepts']),
            'total': timeline_data[date]['tweets'] + timeline_data[date]['articles'] + timeline_data[date]['papers']
        })

    # Find most active day
    most_active_day = max(timeline, key=lambda x: x['total'])['date'] if timeline else None

    # Find most active concept
    most_active_concept = None
    if top_concepts:
        concept = top_concepts[0]
        most_active_concept = {
            'name': concept['display_name'],
            'count': concept['count']
        }

    # Find fastest rising/declining
    fastest_rising = rising_concepts[0] if rising_concepts else None
    fastest_declining = declining_concepts[0] if declining_concepts else None

    return {
        "period_days": days,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "trends": {
            "rising": rising_concepts[:10],
            "stable": stable_concepts[:10],
            "declining": declining_concepts[:10]
        },
        "top_concepts": top_concepts,
        "concept_velocity": rising_concepts[:5] + declining_concepts[:5],
        "content_distribution": content_counts,
        "timeline": timeline,
        "insights": {
            "most_active_day": most_active_day,
            "most_active_concept": most_active_concept,
            "fastest_rising": fastest_rising,
            "fastest_declining": fastest_declining,
            "total_content": sum(content_counts.values()),
            "unique_concepts_used": len(current_concepts)
        }
    }

