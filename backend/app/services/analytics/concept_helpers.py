"""
Concept/tag helper and tag counting functions for analytics.
"""

from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from collections import Counter, defaultdict
from bson import ObjectId


def _concept_service():
    """Lazy accessor for the singleton ConceptOnlyTagService."""
    from app.services.concept_only_tag_service import ConceptOnlyTagService
    return ConceptOnlyTagService()


def get_concept_ids_from_tags(db, tags: List[str]) -> List[ObjectId]:
    """
    Convert tag display names to concept ObjectIds.

    Args:
        db: MongoDB database instance
        tags: List of tag display names

    Returns:
        List of concept ObjectIds
    """
    svc = _concept_service()
    concept_ids = []
    for tag in tags:
        concept = svc._find_concept_by_slug_or_alias(tag)
        if not concept:
            # Fallback to direct display_name lookup
            concept = db.tag_concepts_v2.find_one({'display_name': tag})
        if concept:
            concept_ids.append(concept['_id'])
    return concept_ids


def get_tagged_content_ids(
    db,
    concept_ids: List[ObjectId],
    content_type: str
) -> List[str]:
    """
    Get content IDs that are tagged with any of the given concepts.

    Args:
        db: MongoDB database instance
        concept_ids: List of concept ObjectIds
        content_type: 'tweet', 'article', or 'paper'

    Returns:
        List of content ID strings
    """
    return _concept_service().get_tagged_content_ids(concept_ids, content_type)


def get_concept_by_id(db, concept_id) -> Optional[Dict]:
    """
    Get concept document by ID.

    Args:
        db: MongoDB database instance
        concept_id: Concept ObjectId

    Returns:
        Concept document or None
    """
    return _concept_service().get_concept_by_id(concept_id)


def get_concepts_by_ids(db, concept_ids: List) -> Dict[str, Dict]:
    """
    Get multiple concepts by IDs and return as a map.

    Args:
        db: MongoDB database instance
        concept_ids: List of concept ObjectIds

    Returns:
        Dict mapping string ID to concept document
    """
    return _concept_service().get_concepts_by_ids(concept_ids)


def count_tags_for_content(
    db,
    content_items: List[Dict],
    content_type: str,
    tag_counter: Optional[Counter] = None,
    timeline_dict: Optional[Dict] = None,
    date_field: str = 'created_at'
) -> Counter:
    """
    Count tags for a list of content items.

    Args:
        db: MongoDB database instance
        content_items: List of content documents
        content_type: 'tweet', 'article', or 'paper'
        tag_counter: Optional existing Counter to update
        timeline_dict: Optional timeline dict to update {date_key: {concept_id: count}}
        date_field: Field name for date (created_at or published_at)

    Returns:
        Counter with concept_id -> count
    """
    if tag_counter is None:
        tag_counter = Counter()

    for item in content_items:
        date_key = item.get(date_field, datetime.now(timezone.utc)).strftime('%Y-%m-%d') if timeline_dict else None

        instances = db.tag_instances.find({
            'content_type': content_type,
            'content_id': str(item['_id'])
        })

        for instance in instances:
            if instance.get('concept_id'):
                concept_id = instance['concept_id']
                tag_counter[concept_id] += 1

                if timeline_dict is not None and date_key:
                    if date_key not in timeline_dict:
                        timeline_dict[date_key] = defaultdict(int)
                    timeline_dict[date_key][concept_id] += 1

    return tag_counter


def calculate_tag_velocity(current_count: int, previous_count: int) -> float:
    """
    Calculate tag velocity (percentage change).

    Args:
        current_count: Count in current period
        previous_count: Count in previous period

    Returns:
        Velocity as percentage
    """
    if previous_count > 0:
        return ((current_count - previous_count) / previous_count) * 100
    elif current_count > 0:
        return 100.0
    else:
        return 0.0


def determine_trend(velocity: float, rising_threshold: float = 20, declining_threshold: float = -20) -> str:
    """
    Determine trend direction based on velocity.

    Args:
        velocity: Tag velocity percentage
        rising_threshold: Threshold for 'rising' (default 20%)
        declining_threshold: Threshold for 'declining' (default -20%)

    Returns:
        'rising', 'declining', or 'stable'
    """
    if velocity > rising_threshold:
        return 'rising'
    elif velocity < declining_threshold:
        return 'declining'
    else:
        return 'stable'
