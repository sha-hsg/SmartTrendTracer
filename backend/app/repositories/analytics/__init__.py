"""
Analytics helper package.

Re-exports all public functions for backwards compatibility.
"""

from app.repositories.analytics.date_helpers import (
    parse_period_to_days,
    get_date_range,
    get_previous_period_range,
)

from app.repositories.analytics.concept_helpers import (
    get_concept_ids_from_tags,
    get_tagged_content_ids,
    get_concept_by_id,
    get_concepts_by_ids,
    count_tags_for_content,
    calculate_tag_velocity,
    determine_trend,
)

from app.repositories.analytics.content_fetchers import (
    build_date_filter,
    fetch_tweets_in_range,
    fetch_articles_in_range,
    fetch_papers_in_range,
    fetch_all_content_in_range,
)

from app.repositories.analytics.timeline_helpers import (
    initialize_timeline_dict,
    initialize_hourly_dict,
    populate_timeline_from_content,
    calculate_content_statistics,
    find_peak_and_lowest,
    aggregate_concept_usage,
)

from app.repositories.analytics.summarization_helpers import (
    collect_key_topics,
    prepare_content_sample,
    build_summarization_prompt,
    build_fallback_summary,
)

__all__ = [
    # date_helpers
    'parse_period_to_days',
    'get_date_range',
    'get_previous_period_range',
    # concept_helpers
    'get_concept_ids_from_tags',
    'get_tagged_content_ids',
    'get_concept_by_id',
    'get_concepts_by_ids',
    'count_tags_for_content',
    'calculate_tag_velocity',
    'determine_trend',
    # content_fetchers
    'build_date_filter',
    'fetch_tweets_in_range',
    'fetch_articles_in_range',
    'fetch_papers_in_range',
    'fetch_all_content_in_range',
    # timeline_helpers
    'initialize_timeline_dict',
    'initialize_hourly_dict',
    'populate_timeline_from_content',
    'calculate_content_statistics',
    'find_peak_and_lowest',
    'aggregate_concept_usage',
    # summarization_helpers
    'collect_key_topics',
    'prepare_content_sample',
    'build_summarization_prompt',
    'build_fallback_summary',
]
