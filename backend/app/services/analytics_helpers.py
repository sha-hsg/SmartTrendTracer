"""
Analytics Helper Functions - Re-export shim.

All functions have been moved to app.services.analytics submodules.
This file re-exports them for backwards compatibility.
"""

from app.services.analytics.date_helpers import (  # noqa: F401
    parse_period_to_days,
    get_date_range,
    get_previous_period_range,
)

from app.services.analytics.concept_helpers import (  # noqa: F401
    get_concept_ids_from_tags,
    get_tagged_content_ids,
    get_concept_by_id,
    get_concepts_by_ids,
    count_tags_for_content,
    calculate_tag_velocity,
    determine_trend,
)

from app.services.analytics.content_fetchers import (  # noqa: F401
    build_date_filter,
    fetch_tweets_in_range,
    fetch_articles_in_range,
    fetch_papers_in_range,
    fetch_all_content_in_range,
)

from app.services.analytics.timeline_helpers import (  # noqa: F401
    initialize_timeline_dict,
    initialize_hourly_dict,
    populate_timeline_from_content,
    calculate_content_statistics,
    find_peak_and_lowest,
    aggregate_concept_usage,
)

from app.services.analytics.summarization_helpers import (  # noqa: F401
    collect_key_topics,
    prepare_content_sample,
    build_summarization_prompt,
    build_fallback_summary,
)
