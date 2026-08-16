"""
Anomaly Detection Service
Detects spikes and anomalies in concept activity using statistical methods.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import numpy as np
import logging

from app.database.mongodb import safe_object_id, concept_id_query_variants

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Detects anomalies in concept activity patterns using Z-score analysis.
    """

    def __init__(self, db):
        """
        Initialize the anomaly detector.

        Args:
            db: MongoDB database instance
        """
        self.db = db

    def get_baseline_stats(
        self,
        concept_id: str,
        window_days: int = 30
    ) -> Dict[str, float]:
        """
        Calculate baseline statistics for a concept over a time window.

        Args:
            concept_id: The concept ObjectId string
            window_days: Number of days for baseline calculation

        Returns:
            Dict with mean, std_dev, and daily counts
        """
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=window_days)

        # Get daily counts
        daily_counts = self._get_daily_counts(concept_id, start_date, end_date)

        # Ensure we have counts for all days
        counts = []
        current_date = start_date
        while current_date <= end_date:
            day_key = current_date.strftime('%Y-%m-%d')
            counts.append(daily_counts.get(day_key, 0))
            current_date += timedelta(days=1)

        if not counts or all(c == 0 for c in counts):
            return {
                'mean': 0.0,
                'std_dev': 0.0,
                'min': 0,
                'max': 0,
                'total': 0,
                'daily_counts': counts
            }

        mean = np.mean(counts)
        std_dev = np.std(counts) if len(counts) > 1 else 0.0

        return {
            'mean': float(mean),
            'std_dev': float(std_dev) if std_dev > 0 else 1.0,  # Avoid division by zero
            'min': int(min(counts)),
            'max': int(max(counts)),
            'total': int(sum(counts)),
            'daily_counts': counts
        }

    def _get_daily_counts(
        self,
        concept_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, int]:
        """
        Get daily tag instance counts for a concept using batch queries
        instead of N+1 individual lookups.

        Args:
            concept_id: The concept ObjectId string
            start_date: Start of period
            end_date: End of period

        Returns:
            Dict mapping date strings to counts
        """
        daily_counts: Dict[str, int] = defaultdict(int)

        # Mixed-form concept_id (ObjectId / string / slug) — query all
        # variants; slug-id concepts previously returned empty counts
        instances = list(self.db.tag_instances.find({
            'concept_id': {'$in': concept_id_query_variants(concept_id)}
        }))

        if not instances:
            return daily_counts

        # Group content IDs by type for batch lookup
        ids_by_type: Dict[str, list] = defaultdict(list)
        for inst in instances:
            content_type = inst.get('content_type')
            content_id = inst.get('content_id')
            if content_type and content_id:
                oid = safe_object_id(content_id)
                ids_by_type[content_type].append(oid if oid else content_id)

        # Batch-fetch dates for each content type
        date_field_map = {
            'tweet': ('tweets', 'created_at'),
            'article': ('articles', 'published_at'),
            'paper': ('papers', 'created_at'),
        }

        content_dates: Dict[str, datetime] = {}
        for content_type, id_list in ids_by_type.items():
            if content_type not in date_field_map or not id_list:
                continue
            collection_name, date_field = date_field_map[content_type]
            collection = self.db[collection_name]
            # Batch query with $in instead of N individual find_one calls
            for doc in collection.find(
                {'_id': {'$in': id_list}},
                {'_id': 1, date_field: 1}
            ):
                date_val = doc.get(date_field)
                if date_val:
                    content_dates[f"{content_type}:{doc['_id']}"] = date_val

        # Count by day using the batch-fetched dates
        for inst in instances:
            content_type = inst.get('content_type')
            content_id = inst.get('content_id')
            oid = safe_object_id(content_id)
            key = f"{content_type}:{oid if oid else content_id}"
            date_value = content_dates.get(key)
            if date_value is not None and date_value.tzinfo is None:
                # DB datetimes are naive UTC - normalize for aware comparison
                date_value = date_value.replace(tzinfo=timezone.utc)
            if date_value and start_date <= date_value <= end_date:
                day_key = date_value.strftime('%Y-%m-%d')
                daily_counts[day_key] += 1

        return daily_counts

    def calculate_z_score(
        self,
        value: float,
        mean: float,
        std_dev: float
    ) -> float:
        """
        Calculate Z-score for a value.

        Args:
            value: The observed value
            mean: Baseline mean
            std_dev: Baseline standard deviation

        Returns:
            Z-score value
        """
        if std_dev <= 0:
            return 0.0 if value == mean else (3.0 if value > mean else -3.0)
        return (value - mean) / std_dev

    def detect_spikes(
        self,
        concept_id: str,
        threshold: float = 2.5,
        recent_hours: int = 48
    ) -> Optional[Dict[str, Any]]:
        """
        Detect if a concept has a spike in activity.

        Args:
            concept_id: The concept ObjectId string
            threshold: Z-score threshold for spike detection
            recent_hours: Hours to check for spike

        Returns:
            Spike info dict or None if no spike
        """
        # Get baseline stats from last 30 days
        baseline = self.get_baseline_stats(concept_id, window_days=30)

        # Get recent activity
        recent_end = datetime.now(timezone.utc)
        recent_start = recent_end - timedelta(hours=recent_hours)

        recent_counts = self._get_daily_counts(concept_id, recent_start, recent_end)
        recent_total = sum(recent_counts.values())

        # Normalize to daily rate
        recent_daily_rate = recent_total / (recent_hours / 24) if recent_hours > 0 else 0

        # Calculate Z-score
        z_score = self.calculate_z_score(
            recent_daily_rate,
            baseline['mean'],
            baseline['std_dev']
        )

        if z_score >= threshold:
            return {
                'concept_id': concept_id,
                'z_score': round(z_score, 2),
                'current_value': recent_total,
                'current_daily_rate': round(recent_daily_rate, 1),
                'baseline_avg': round(baseline['mean'], 1),
                'baseline_std': round(baseline['std_dev'], 1),
                'spike_magnitude': recent_total - baseline['mean'] * (recent_hours / 24),
                'timestamp': recent_end.isoformat()
            }

        return None

    def get_all_anomalies(
        self,
        hours: int = 48,
        threshold: float = 2.5,
        min_activity: int = 3,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Find all concepts with anomalous activity.

        Args:
            hours: Recent time window to check
            threshold: Z-score threshold
            min_activity: Minimum recent activity to consider
            limit: Maximum anomalies to return

        Returns:
            List of anomaly dicts sorted by Z-score
        """
        anomalies = []

        # Get all active concepts from recent period
        recent_end = datetime.now(timezone.utc)
        recent_start = recent_end - timedelta(hours=hours)

        # Aggregate recent tag instances by concept
        pipeline = [
            {
                '$lookup': {
                    'from': 'tweets',
                    'localField': 'content_id',
                    'foreignField': '_id',
                    'as': 'tweet'
                }
            },
            {
                '$match': {
                    'concept_id': {'$ne': None}
                }
            },
            {
                '$group': {
                    '_id': '$concept_id',
                    'count': {'$sum': 1}
                }
            },
            {
                '$match': {
                    'count': {'$gte': min_activity}
                }
            },
            {
                '$sort': {'count': -1}
            },
            {
                '$limit': 100  # Check top 100 most active
            }
        ]

        active_concepts = list(self.db.tag_instances.aggregate(pipeline))

        for entry in active_concepts:
            concept_id = str(entry['_id'])
            spike = self.detect_spikes(concept_id, threshold, hours)

            if spike:
                # Get concept info via service
                from app.services.concept_only_tag_service import ConceptOnlyTagService
                concept = ConceptOnlyTagService().get_concept_by_id(entry['_id'])
                if concept:
                    spike['display_name'] = concept.get('display_name', 'Unknown')
                    spike['slug'] = concept.get('slug', '')
                    spike['entity_type'] = concept.get('entity_type', 'concept')
                    anomalies.append(spike)

        # Sort by Z-score descending
        anomalies.sort(key=lambda x: x['z_score'], reverse=True)

        return anomalies[:limit]

    def explain_anomaly(
        self,
        concept_id: str,
        spike_date: str
    ) -> Optional[str]:
        """
        Use LLM to explain why an anomaly might have occurred.

        Args:
            concept_id: The concept ObjectId string
            spike_date: Date of the spike (YYYY-MM-DD)

        Returns:
            Explanation string or None
        """
        try:
            from app.services.llm_manager import get_llm_manager

            from app.services.concept_only_tag_service import ConceptOnlyTagService
            svc = ConceptOnlyTagService()

            concept = svc.get_concept_by_id(concept_id)
            if not concept:
                return None

            display_name = concept.get('display_name', 'Unknown')

            # Get tagged content samples
            instances = svc.get_instances_by_concept_id(concept_id, limit=50)

            content_samples = []
            for inst in instances[:10]:
                content_type = inst.get('content_type')
                content_id = inst.get('content_id')
                doc_id = safe_object_id(content_id) or content_id

                if content_type == 'tweet':
                    tweet = self.db.tweets.find_one({'_id': doc_id})
                    if tweet:
                        content_samples.append(f"Tweet: {tweet.get('text', '')[:200]}")
                elif content_type == 'article':
                    article = self.db.articles.find_one({'_id': doc_id})
                    if article:
                        content_samples.append(f"Article: {article.get('title', '')}")

            if not content_samples:
                return "Insufficient content to explain the spike."

            # Generate explanation with LLM
            llm_manager = get_llm_manager()

            prompt = f"""Analyze why there might be a spike in discussions about "{display_name}" based on the following sample content:

{chr(10).join(content_samples)}

Provide a brief (2-3 sentences) explanation of what might have caused increased discussion about this topic. Focus on identifying any news, announcements, or events that could explain the spike."""

            messages = [{"role": "user", "content": prompt}]
            response = llm_manager.completion_sync(
                task_type='freeAnalysis',
                messages=messages,
                user_id='anomaly_detector'
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error explaining anomaly: {e}")
            return None


def get_concept_cooccurrence(
    db,
    days: int = 7,
    min_cooccurrence: int = 2,
    top_n: int = 30
) -> Dict[str, Any]:
    """
    Calculate concept co-occurrence matrix and pairs.

    Args:
        db: MongoDB database instance
        days: Number of days to analyze
        min_cooccurrence: Minimum co-occurrence count
        top_n: Number of top concepts to include

    Returns:
        Dict with concepts, matrix, and pairs
    """
    from app.services.analytics_helpers import (
        get_date_range, fetch_tweets_in_range,
        fetch_articles_in_range, fetch_papers_in_range
    )

    start_date, end_date = get_date_range(days)

    # Get all content
    tweets = fetch_tweets_in_range(db, start_date, end_date)
    articles = fetch_articles_in_range(db, start_date, end_date)
    papers = fetch_papers_in_range(db, start_date, end_date)

    # Build content -> concepts mapping using batch queries
    content_concepts = defaultdict(set)
    concept_counts = defaultdict(int)

    def process_content_batch(items, content_type):
        if not items:
            return
        content_ids = [str(item['_id']) for item in items]
        # Single batch query instead of N individual queries
        all_instances = list(db.tag_instances.find({
            'content_type': content_type,
            'content_id': {'$in': content_ids}
        }))
        for inst in all_instances:
            if inst.get('concept_id'):
                content_id = str(inst['content_id'])
                concept_id = str(inst['concept_id'])
                content_concepts[f"{content_type}:{content_id}"].add(concept_id)
                concept_counts[concept_id] += 1

    process_content_batch(tweets, 'tweet')
    process_content_batch(articles, 'article')
    process_content_batch(papers, 'paper')

    # Get top N concepts by count
    top_concept_ids = [cid for cid, _ in sorted(concept_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]]

    # Get concept info via service
    from app.services.concept_only_tag_service import ConceptOnlyTagService
    svc = ConceptOnlyTagService()
    concept_map = svc.get_concepts_by_ids(top_concept_ids)

    # Build co-occurrence matrix
    n = len(top_concept_ids)
    matrix = [[0] * n for _ in range(n)]
    cooccurrence_counts = defaultdict(int)

    for content_key, concepts in content_concepts.items():
        concept_list = [c for c in concepts if c in top_concept_ids]
        for i, c1 in enumerate(concept_list):
            for c2 in concept_list[i+1:]:
                # Order pair consistently
                pair = tuple(sorted([c1, c2]))
                cooccurrence_counts[pair] += 1

    # Fill matrix
    id_to_idx = {cid: idx for idx, cid in enumerate(top_concept_ids)}
    for (c1, c2), count in cooccurrence_counts.items():
        if count >= min_cooccurrence:
            i, j = id_to_idx[c1], id_to_idx[c2]
            matrix[i][j] = count
            matrix[j][i] = count

    # Build pairs list with Jaccard similarity
    pairs = []
    for (c1, c2), count in cooccurrence_counts.items():
        if count >= min_cooccurrence:
            # Jaccard = intersection / union
            count_c1 = concept_counts.get(c1, 1)
            count_c2 = concept_counts.get(c2, 1)
            jaccard = count / (count_c1 + count_c2 - count) if (count_c1 + count_c2 - count) > 0 else 0

            concept_a = concept_map.get(c1, {})
            concept_b = concept_map.get(c2, {})

            pairs.append({
                'concept_a': concept_a.get('display_name', 'Unknown'),
                'concept_a_id': c1,
                'concept_b': concept_b.get('display_name', 'Unknown'),
                'concept_b_id': c2,
                'count': count,
                'strength': round(jaccard, 3)
            })

    # Sort by strength
    pairs.sort(key=lambda x: x['strength'], reverse=True)

    # Get concept names for matrix
    concept_names = [
        concept_map.get(cid, {}).get('display_name', 'Unknown')
        for cid in top_concept_ids
    ]

    return {
        'concepts': concept_names,
        'concept_ids': top_concept_ids,
        'matrix': matrix,
        'pairs': pairs[:50],
        'total_documents': len(content_concepts)
    }


def get_concept_activity_by_day(
    db,
    concept_ids: List[str],
    days: int = 14
) -> Dict[str, List[int]]:
    """
    Get daily activity counts for multiple concepts.

    Args:
        db: MongoDB database instance
        concept_ids: List of concept ID strings
        days: Number of days

    Returns:
        Dict mapping concept_id to list of daily counts
    """
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)

    result = {}
    detector = AnomalyDetector(db)

    for concept_id in concept_ids:
        daily_counts = detector._get_daily_counts(concept_id, start_date, end_date)

        # Build ordered list
        counts = []
        current_date = start_date
        while current_date <= end_date:
            day_key = current_date.strftime('%Y-%m-%d')
            counts.append(daily_counts.get(day_key, 0))
            current_date += timedelta(days=1)

        result[concept_id] = counts

    return result
