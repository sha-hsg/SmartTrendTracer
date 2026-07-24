"""
Visualization-focused routes for analytics trends.
Contains tags and timeline endpoints.
Split from analytics_trends_mongodb.py.
"""

from fastapi import APIRouter, Query
from datetime import timedelta
from collections import Counter, defaultdict

from .utils import (
    normalize_datetime,
    db,
    get_date_range,
    get_previous_period_range,
    get_concept_by_id,
    count_tags_for_content,
    calculate_tag_velocity,
    determine_trend,
    fetch_tweets_in_range,
    fetch_articles_in_range,
    fetch_papers_in_range,
    initialize_timeline_dict,
    initialize_hourly_dict,
    populate_timeline_from_content,
    find_peak_and_lowest,
)

router = APIRouter()


@router.get("/tags")
def get_trends_tags(
    days: int = Query(7, ge=1, le=365, description="Number of days to analyze"),
    limit: int = Query(20, ge=5, le=100, description="Maximum number of tags to return")
):
    """
    Get tag trends for analytics visualization with real data
    Returns top tags and their usage patterns
    """
    # Calculate date ranges
    start_date, end_date = get_date_range(days)
    previous_start, previous_end = get_previous_period_range(start_date, days)

    # Initialize counters
    current_tags = Counter()
    previous_tags = Counter()
    tag_timeline = defaultdict(lambda: defaultdict(int))

    # Fetch content for current period
    tweets = fetch_tweets_in_range(db, start_date, end_date)
    articles = fetch_articles_in_range(db, start_date, end_date)
    papers = fetch_papers_in_range(db, start_date, end_date)

    # Count tags for current period
    count_tags_for_content(db, tweets, 'tweet', current_tags, tag_timeline, 'created_at')
    count_tags_for_content(db, articles, 'article', current_tags, tag_timeline, 'published_at')
    count_tags_for_content(db, papers, 'paper', current_tags, tag_timeline, 'created_at')

    # Fetch and count tags for previous period
    prev_tweets = fetch_tweets_in_range(db, previous_start, previous_end)
    prev_articles = fetch_articles_in_range(db, previous_start, previous_end)
    prev_papers = fetch_papers_in_range(db, previous_start, previous_end)

    count_tags_for_content(db, prev_tweets, 'tweet', previous_tags)
    count_tags_for_content(db, prev_articles, 'article', previous_tags)
    count_tags_for_content(db, prev_papers, 'paper', previous_tags)

    # Calculate trends
    rising_tags = []
    declining_tags = []
    top_tags = []

    # Get top tags with velocity calculations
    for concept_id, count in current_tags.most_common(limit):
        concept = get_concept_by_id(db, concept_id)
        if concept:
            previous_count = previous_tags.get(concept_id, 0)
            velocity = calculate_tag_velocity(count, previous_count)
            trend = determine_trend(velocity)

            tag_data = {
                'tag': concept.get('display_name'),
                'slug': concept.get('slug'),
                'count': count,
                'previous_count': previous_count,
                'velocity': round(velocity, 1),
                'trend': trend
            }

            top_tags.append(tag_data)

            if trend == 'rising':
                rising_tags.append(tag_data)
            elif trend == 'declining':
                declining_tags.append(tag_data)

    # Sort rising and declining
    rising_tags.sort(key=lambda x: x['velocity'], reverse=True)
    declining_tags.sort(key=lambda x: x['velocity'])

    # Build timeline
    timeline_data = []
    for date in sorted(tag_timeline.keys()):
        date_tags = []
        for tag_id, count in tag_timeline[date].items():
            concept = get_concept_by_id(db, tag_id)
            if concept:
                date_tags.append({
                    'tag': concept.get('display_name'),
                    'count': count
                })
        timeline_data.append({
            'date': date,
            'tags': sorted(date_tags, key=lambda x: x['count'], reverse=True)[:5]
        })

    # Find statistics
    most_used = top_tags[0] if top_tags else None
    fastest_growing = rising_tags[0] if rising_tags else None
    highest_velocity = max(top_tags, key=lambda x: abs(x['velocity'])) if top_tags else None

    return {
        "period_days": days,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "tags": top_tags,
        "top_tags": top_tags[:10],
        "rising_tags": rising_tags[:5],
        "declining_tags": declining_tags[:5],
        "tag_statistics": {
            "total_unique": len(current_tags),
            "most_used": most_used['tag'] if most_used else None,
            "fastest_growing": fastest_growing['tag'] if fastest_growing else None,
            "highest_velocity": highest_velocity['tag'] if highest_velocity else None
        },
        "tag_correlations": [],
        "tag_timeline": timeline_data
    }


@router.get("/timeline")
def get_trends_timeline(
    days: int = Query(7, ge=1, le=365, description="Number of days to analyze")
):
    """
    Get timeline data for trend visualization with real data
    Returns time-series data for charts and graphs
    """
    # Calculate date range
    start_date, end_date = get_date_range(days)

    # Initialize timeline
    timeline_dict = initialize_timeline_dict(start_date, end_date)

    # Fetch content
    tweets = fetch_tweets_in_range(db, start_date, end_date)
    articles = fetch_articles_in_range(db, start_date, end_date)
    papers = fetch_papers_in_range(db, start_date, end_date)

    # Populate timeline
    total_tweets, total_articles, total_papers = populate_timeline_from_content(
        db, timeline_dict, tweets, articles, papers, track_concepts=True
    )

    # Convert to list and calculate totals
    timeline_data = []
    for date_key in sorted(timeline_dict.keys()):
        entry = timeline_dict[date_key]
        entry["total"] = entry["tweets"] + entry["articles"] + entry["papers"]
        entry["count"] = entry["total"]  # Frontend compatibility

        # Get concept names for this day
        concept_names = []
        for concept_id in list(entry["concepts"])[:5]:
            concept = get_concept_by_id(db, concept_id)
            if concept:
                concept_names.append(concept.get('display_name'))
        entry["concepts"] = concept_names
        entry["concept_count"] = len(entry["concepts"])

        timeline_data.append(entry)

    # Find peak and lowest
    peak_lowest = find_peak_and_lowest(timeline_data)

    # Calculate averages
    total_content = total_tweets + total_articles + total_papers
    avg_per_day = round(total_content / max(len(timeline_data), 1), 1)

    result = {
        "period_days": days,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "timeline": timeline_data,
        "daily": timeline_data,
        "summary": {
            "total_content": total_content,
            "avg_per_day": avg_per_day,
            **peak_lowest
        },
        "content_distribution": {
            "tweets": total_tweets,
            "articles": total_articles,
            "papers": total_papers
        },
        "hourly": [],
        "by_account": {}
    }

    # Generate hourly data
    hourly_hours = min(48, days * 24) if days <= 2 else 24
    hourly_start = end_date - timedelta(hours=hourly_hours)
    hourly_dict = initialize_hourly_dict(hourly_start, hourly_hours)

    # Fill hourly data from recent content
    recent_tweets = fetch_tweets_in_range(db, hourly_start, end_date)
    for tweet in recent_tweets:
        dt = normalize_datetime(tweet.get('created_at'))
        if dt:
            hour_key = dt.strftime('%Y-%m-%d %H:00')
            if hour_key in hourly_dict:
                hourly_dict[hour_key]["tweets"] += 1
                hourly_dict[hour_key]["count"] += 1

    recent_articles = fetch_articles_in_range(db, hourly_start, end_date)
    for article in recent_articles:
        dt = normalize_datetime(article.get('published_at'))
        if dt:
            hour_key = dt.strftime('%Y-%m-%d %H:00')
            if hour_key in hourly_dict:
                hourly_dict[hour_key]["articles"] += 1
                hourly_dict[hour_key]["count"] += 1

    recent_papers = fetch_papers_in_range(db, hourly_start, end_date)
    for paper in recent_papers:
        dt = normalize_datetime(paper.get('created_at'))
        if dt:
            hour_key = dt.strftime('%Y-%m-%d %H:00')
            if hour_key in hourly_dict:
                hourly_dict[hour_key]["papers"] += 1
                hourly_dict[hour_key]["count"] += 1

    result["hourly"] = [hourly_dict[key] for key in sorted(hourly_dict.keys())]

    # Generate by_account timeline data
    account_timeline = {}
    for tweet in tweets:
        username = tweet.get('author_username', 'unknown')
        if username not in account_timeline:
            account_timeline[username] = {}

        date_key = tweet['created_at'].strftime('%Y-%m-%d')
        if date_key not in account_timeline[username]:
            account_timeline[username][date_key] = 0
        account_timeline[username][date_key] += 1

    for username, dates in account_timeline.items():
        account_timeline[username] = [
            {"date": date, "count": count}
            for date, count in sorted(dates.items())
        ]

    result["by_account"] = account_timeline

    return result

