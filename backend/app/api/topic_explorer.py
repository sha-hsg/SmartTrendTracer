"""
Topic Explorer API
Provides topic frequency over time and correlation analysis
"""

from fastapi import APIRouter, Query, HTTPException
from app.database.mongodb import get_database, concept_id_query_variants
from bson import ObjectId
from typing import Optional
from datetime import datetime, timezone, timedelta
from collections import defaultdict, Counter
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# MongoDB connection
db = get_database()

# Color palette for topics
TOPIC_COLORS = [
    "#2563eb",  # Blue
    "#dc2626",  # Red
    "#16a34a",  # Green
    "#9333ea",  # Purple
    "#ea580c",  # Orange
    "#0891b2",  # Cyan
    "#c026d3",  # Magenta
    "#84cc16",  # Lime
    "#f59e0b",  # Amber
    "#6366f1",  # Indigo
]


def ensure_aware(dt: Optional[datetime]) -> Optional[datetime]:
    """Normalize a datetime to timezone-aware UTC (DB values are naive UTC)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse date string to timezone-aware datetime object (UTC)"""
    if not date_str:
        return None
    try:
        return ensure_aware(datetime.fromisoformat(date_str.replace('Z', '+00:00')))
    except ValueError:
        try:
            return ensure_aware(datetime.strptime(date_str, '%Y-%m-%d'))
        except ValueError:
            return None


def get_date_from_content(content: dict, content_type: str) -> Optional[datetime]:
    """Extract date from content based on content type"""
    date_field = content.get('created_at') or content.get('publication_date') or content.get('published_date') or content.get('date')
    if not date_field:
        return None

    if isinstance(date_field, datetime):
        return date_field
    elif isinstance(date_field, str):
        return parse_date(date_field)
    return None


def group_by_granularity(date: datetime, granularity: str) -> str:
    """Group date by specified granularity"""
    if granularity == 'day':
        return date.strftime('%Y-%m-%d')
    elif granularity == 'week':
        # Get start of week (Monday)
        start_of_week = date - timedelta(days=date.weekday())
        return start_of_week.strftime('%Y-%m-%d')
    elif granularity == 'month':
        return date.strftime('%Y-%m')
    else:
        return date.strftime('%Y-%m-%d')


@router.get("/frequency")
async def get_topic_frequency(
    concept_ids: str = Query(..., description="Comma-separated concept IDs"),
    source_types: str = Query("tweet,article,paper", description="Comma-separated content types"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format or YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format or YYYY-MM-DD)"),
    granularity: str = Query("week", description="Time granularity: day, week, month")
):
    """
    Get topic frequency over time for selected concepts.
    Returns time series data suitable for line charts.
    """
    try:
        # Parse concept IDs
        concept_id_list = [cid.strip() for cid in concept_ids.split(',') if cid.strip()]
        if not concept_id_list:
            raise HTTPException(status_code=400, detail="At least one concept_id is required")

        if len(concept_id_list) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 concepts allowed")

        # concept_id may be an ObjectId string or a legacy slug id — build all
        # storage variants (see concept_id_query_variants)
        id_variants = []
        for cid in concept_id_list:
            id_variants.extend(concept_id_query_variants(cid))

        # Get concept names (covers ObjectId and string _id concepts)
        concepts = list(db.tag_concepts_v2.find({'_id': {'$in': id_variants}}))
        concept_map = {str(c['_id']): c.get('display_name', c.get('name', 'Unknown')) for c in concepts}

        # Parse source types
        source_type_list = [s.strip() for s in source_types.split(',') if s.strip()]

        # Parse dates
        start_dt = parse_date(start_date) if start_date else datetime.now(timezone.utc) - timedelta(days=365)
        end_dt = parse_date(end_date) if end_date else datetime.now(timezone.utc)

        # Build query filter for tag_instances
        instance_filter = {
            'concept_id': {'$in': id_variants}
        }
        if source_type_list:
            instance_filter['content_type'] = {'$in': source_type_list}

        # Get all matching tag instances
        instances = list(db.tag_instances.find(instance_filter))

        # Group instances by concept and content
        content_by_concept = defaultdict(set)
        for inst in instances:
            concept_id = str(inst['concept_id'])
            content_id = inst.get('content_id')
            content_type = inst.get('content_type')
            if content_id and content_type:
                content_by_concept[concept_id].add((content_id, content_type))

        # Get dates for each content item
        series = []
        color_idx = 0

        for concept_id, content_items in content_by_concept.items():
            if concept_id not in concept_map:
                continue

            date_counts = defaultdict(int)

            # Group by content type for efficient querying
            by_type = defaultdict(list)
            for content_id, content_type in content_items:
                by_type[content_type].append(content_id)

            # Query each content type
            for content_type, content_ids in by_type.items():
                collection = None
                if content_type == 'tweet':
                    collection = db.tweets
                elif content_type == 'article':
                    collection = db.articles
                elif content_type == 'paper':
                    collection = db.papers

                if collection is not None:
                    # Handle different ID types per collection
                    # Tweets use string IDs (Twitter IDs), articles/papers use ObjectIds
                    if content_type == 'tweet':
                        # Tweets have string _ids - use as-is
                        id_list = [str(cid) for cid in content_ids]
                    else:
                        # Articles and papers have ObjectId _ids
                        id_list = []
                        for cid in content_ids:
                            if isinstance(cid, ObjectId):
                                id_list.append(cid)
                            else:
                                try:
                                    id_list.append(ObjectId(cid))
                                except Exception:
                                    pass

                    contents = list(collection.find({'_id': {'$in': id_list}}))

                    for content in contents:
                        content_date = ensure_aware(get_date_from_content(content, content_type))
                        if content_date and start_dt <= content_date <= end_dt:
                            date_key = group_by_granularity(content_date, granularity)
                            date_counts[date_key] += 1

            # Convert to sorted list
            data_points = [
                {'date': date, 'count': count}
                for date, count in sorted(date_counts.items())
            ]

            series.append({
                'concept_id': concept_id,
                'concept_name': concept_map.get(concept_id, 'Unknown'),
                'color': TOPIC_COLORS[color_idx % len(TOPIC_COLORS)],
                'data': data_points,
                'total': sum(d['count'] for d in data_points)
            })
            color_idx += 1

        # Sort series by total count (most popular first)
        series.sort(key=lambda x: x['total'], reverse=True)

        return {
            'series': series,
            'time_range': {
                'start': start_dt.strftime('%Y-%m-%d'),
                'end': end_dt.strftime('%Y-%m-%d')
            },
            'granularity': granularity,
            'source_types': source_type_list
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting topic frequency: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/correlation")
async def get_topic_correlation(
    source_types: str = Query("tweet,article,paper", description="Comma-separated content types"),
    min_count: int = Query(5, ge=1, le=100, description="Minimum occurrences to include topic"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format or YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format or YYYY-MM-DD)"),
    limit: int = Query(30, ge=5, le=100, description="Maximum number of topics to analyze")
):
    """
    Get topic co-occurrence correlation data.
    Returns data suitable for scatter plots showing topic relationships.
    """
    try:
        # Parse source types
        source_type_list = [s.strip() for s in source_types.split(',') if s.strip()]

        # Parse dates
        start_dt = parse_date(start_date) if start_date else datetime.now(timezone.utc) - timedelta(days=365)
        end_dt = parse_date(end_date) if end_date else datetime.now(timezone.utc)

        # Build query filter
        instance_filter = {}
        if source_type_list:
            instance_filter['content_type'] = {'$in': source_type_list}

        # Apply date range filter (tag_instances.created_at is a native BSON datetime)
        instance_filter['created_at'] = {'$gte': start_dt, '$lte': end_dt}

        # Get all tag instances
        instances = list(db.tag_instances.find(instance_filter))

        # Group by content item (content_id + content_type)
        content_concepts = defaultdict(set)
        concept_counts = Counter()

        for inst in instances:
            concept_id = inst.get('concept_id')
            content_id = inst.get('content_id')
            content_type = inst.get('content_type')

            if concept_id and content_id and content_type:
                content_key = f"{content_type}:{content_id}"
                content_concepts[content_key].add(str(concept_id))
                concept_counts[str(concept_id)] += 1

        # Filter to top concepts by count
        top_concepts = [cid for cid, count in concept_counts.most_common(limit) if count >= min_count]

        if not top_concepts:
            return {
                'topics': [],
                'correlations': [],
                'matrix': []
            }

        # Get concept details
        top_concept_oids = [ObjectId(cid) for cid in top_concepts if ObjectId.is_valid(cid)]
        concepts = list(db.tag_concepts_v2.find({'_id': {'$in': top_concept_oids}}))
        concept_map = {str(c['_id']): c for c in concepts}

        # Build co-occurrence matrix
        co_occurrence = defaultdict(int)
        for content_key, concepts_set in content_concepts.items():
            # Filter to only top concepts
            filtered = concepts_set & set(top_concepts)
            # Count pairs
            concept_list = list(filtered)
            for i in range(len(concept_list)):
                for j in range(i + 1, len(concept_list)):
                    pair = tuple(sorted([concept_list[i], concept_list[j]]))
                    co_occurrence[pair] += 1

        # Calculate correlation (Jaccard similarity)
        correlations = []
        for (cid1, cid2), co_count in co_occurrence.items():
            if co_count >= 2:  # At least 2 co-occurrences
                count1 = concept_counts[cid1]
                count2 = concept_counts[cid2]
                # Jaccard similarity: intersection / union
                union = count1 + count2 - co_count
                correlation = co_count / union if union > 0 else 0

                if cid1 in concept_map and cid2 in concept_map:
                    correlations.append({
                        'topic1_id': cid1,
                        'topic1_name': concept_map[cid1].get('display_name', concept_map[cid1].get('name', 'Unknown')),
                        'topic2_id': cid2,
                        'topic2_name': concept_map[cid2].get('display_name', concept_map[cid2].get('name', 'Unknown')),
                        'co_occurrence': co_count,
                        'correlation': round(correlation, 3),
                        'topic1_count': count1,
                        'topic2_count': count2
                    })

        # Sort by correlation strength
        correlations.sort(key=lambda x: x['correlation'], reverse=True)

        # Build topics list
        topics = []
        color_idx = 0
        for cid in top_concepts:
            if cid in concept_map:
                concept = concept_map[cid]
                topics.append({
                    'id': cid,
                    'name': concept.get('display_name', concept.get('name', 'Unknown')),
                    'slug': concept.get('slug', ''),
                    'total_count': concept_counts[cid],
                    'entity_type': concept.get('entity_type', 'concept'),
                    'color': TOPIC_COLORS[color_idx % len(TOPIC_COLORS)]
                })
                color_idx += 1

        # Sort by count
        topics.sort(key=lambda x: x['total_count'], reverse=True)

        return {
            'topics': topics,
            'correlations': correlations[:100],  # Limit to top 100 correlations
            'source_types': source_type_list,
            'time_range': {
                'start': start_dt.strftime('%Y-%m-%d'),
                'end': end_dt.strftime('%Y-%m-%d')
            }
        }

    except Exception as e:
        logger.error(f"Error getting topic correlation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/popular")
async def get_popular_topics(
    source_types: str = Query("tweet,article,paper", description="Comma-separated content types"),
    days: int = Query(90, ge=1, le=3650, description="Number of days to look back"),
    limit: int = Query(50, ge=5, le=200, description="Maximum number of topics")
):
    """
    Get most popular topics for the topic selector.
    """
    try:
        # Parse source types
        source_type_list = [s.strip() for s in source_types.split(',') if s.strip()]

        # Calculate cutoff date
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        # Build aggregation pipeline
        match_criteria = {}
        if source_type_list:
            match_criteria['content_type'] = {'$in': source_type_list}
        match_criteria['created_at'] = {'$gte': cutoff}

        pipeline = [
            {'$match': match_criteria},
            {'$group': {
                '_id': '$concept_id',
                'count': {'$sum': 1},
                'content_types': {'$addToSet': '$content_type'}
            }},
            {'$sort': {'count': -1}},
            {'$limit': limit}
        ]

        results = list(db.tag_instances.aggregate(pipeline))

        # Get concept details
        concept_ids = [r['_id'] for r in results if r['_id']]
        concepts = list(db.tag_concepts_v2.find({'_id': {'$in': concept_ids}}))
        concept_map = {c['_id']: c for c in concepts}

        topics = []
        for r in results:
            cid = r['_id']
            if cid and cid in concept_map:
                concept = concept_map[cid]
                topics.append({
                    'id': str(cid),
                    'name': concept.get('display_name', concept.get('name', 'Unknown')),
                    'slug': concept.get('slug', ''),
                    'count': r['count'],
                    'content_types': r['content_types'],
                    'entity_type': concept.get('entity_type', 'concept')
                })

        return {
            'topics': topics,
            'days': days,
            'source_types': source_type_list
        }

    except Exception as e:
        logger.error(f"Error getting popular topics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
