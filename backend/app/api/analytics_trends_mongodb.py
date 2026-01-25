"""
MongoDB-based Analytics Trends API
Provides analytical trend visualization data
"""

from fastapi import APIRouter, Query, HTTPException
from app.database.mongodb import get_database
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import logging


def normalize_datetime(dt_value: Any) -> Optional[datetime]:
    """
    Normalize various datetime representations to a datetime object.
    Handles: datetime objects, ISO strings, timestamps (int/float).
    Returns None if conversion fails.
    """
    if dt_value is None:
        return None
    if isinstance(dt_value, datetime):
        return dt_value
    if isinstance(dt_value, str):
        try:
            # Try ISO format first
            return datetime.fromisoformat(dt_value.replace('Z', '+00:00'))
        except ValueError:
            try:
                # Try common formats
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S']:
                    try:
                        return datetime.strptime(dt_value, fmt)
                    except ValueError:
                        continue
            except Exception:
                pass
        return None
    if isinstance(dt_value, (int, float)):
        try:
            return datetime.fromtimestamp(dt_value)
        except (ValueError, OSError):
            return None
    return None

# Import helper functions
from app.services.analytics_helpers import (
    parse_period_to_days,
    get_date_range,
    get_previous_period_range,
    get_concept_ids_from_tags,
    get_tagged_content_ids,
    get_concept_by_id,
    get_concepts_by_ids,
    count_tags_for_content,
    calculate_tag_velocity,
    determine_trend,
    fetch_tweets_in_range,
    fetch_articles_in_range,
    fetch_papers_in_range,
    fetch_all_content_in_range,
    initialize_timeline_dict,
    initialize_hourly_dict,
    populate_timeline_from_content,
    calculate_content_statistics,
    find_peak_and_lowest,
    aggregate_concept_usage,
    collect_key_topics,
    prepare_content_sample,
    build_summarization_prompt,
    build_fallback_summary,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# MongoDB connection
db = get_database()


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


@router.get("/heatmap")
def get_trends_heatmap(
    days: int = Query(30, ge=7, le=365, description="Number of days to analyze")
):
    """
    Get heatmap data for activity visualization
    """
    start_date, end_date = get_date_range(days)

    # Generate heatmap structure (7 days x 24 hours)
    heatmap_data = []
    for day in range(7):
        day_data = []
        for hour in range(24):
            day_data.append({
                "hour": hour,
                "day": day,
                "value": 0,
                "content_types": []
            })
        heatmap_data.append({
            "day_name": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][day],
            "hours": day_data
        })

    return {
        "period_days": days,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "heatmap": heatmap_data,
        "peak_times": {
            "most_active_day": None,
            "most_active_hour": None,
            "least_active_day": None,
            "least_active_hour": None
        }
    }


@router.get("/network")
def get_concept_network(
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze"),
    min_connections: int = Query(2, ge=1, le=10, description="Minimum connections to include")
):
    """
    Get network graph data for concept relationships
    """
    start_date, end_date = get_date_range(days)

    return {
        "period_days": days,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "nodes": [],
        "edges": [],
        "clusters": [],
        "statistics": {
            "total_nodes": 0,
            "total_edges": 0,
            "avg_connections": 0,
            "max_connections": 0,
            "isolated_nodes": 0
        }
    }


@router.get("/bubble-chart")
def get_bubble_chart_data(
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze")
):
    """
    Get bubble chart data for concept importance and growth
    """
    start_date, end_date = get_date_range(days)

    return {
        "period_days": days,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "bubbles": [],
        "axes": {
            "x": "usage_frequency",
            "y": "growth_rate"
        },
        "legend": {
            "size": "total_mentions",
            "color": "content_type"
        }
    }


@router.get("/sankey")
def get_sankey_diagram_data(
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze")
):
    """
    Get Sankey diagram data for content flow between sources and concepts
    """
    start_date, end_date = get_date_range(days)

    return {
        "period_days": days,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "nodes": [
            {"id": 0, "name": "Tweets"},
            {"id": 1, "name": "Articles"},
            {"id": 2, "name": "Papers"}
        ],
        "links": [],
        "total_flow": 0
    }


@router.get("/wordcloud")
def get_wordcloud_data(
    days: int = Query(365, ge=1, le=3650, description="Number of days to analyze"),
    content_type: Optional[str] = Query(None, description="Filter by content type (tweet, article, paper)"),
    limit: int = Query(100, ge=10, le=500, description="Maximum number of words")
):
    """
    Get word cloud data for concept visualization.
    Returns concepts with their usage counts for rendering as a word cloud.
    """
    try:
        start_date, end_date = get_date_range(days)

        # Aggregate concept usage
        results = aggregate_concept_usage(db, content_type, limit)

        if not results:
            return {
                "period_days": days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "content_type": content_type,
                "words": [],
                "max_value": 0,
                "min_value": 0,
                "total_words": 0
            }

        # Get concept details
        concept_ids = [r['_id'] for r in results]
        concept_map = get_concepts_by_ids(db, concept_ids)

        # Color palette
        colors = [
            "#2563eb", "#dc2626", "#16a34a", "#9333ea", "#ea580c",
            "#0891b2", "#c026d3", "#84cc16", "#f59e0b", "#6366f1"
        ]

        # Build words list
        words = []
        for i, r in enumerate(results):
            concept_id = str(r['_id'])
            concept = concept_map.get(concept_id)
            if concept:
                words.append({
                    "text": concept.get('display_name', concept.get('name', 'Unknown')),
                    "value": r['count'],
                    "color": colors[i % len(colors)],
                    "concept_id": concept_id,
                    "entity_type": concept.get('entity_type', 'concept')
                })

        max_value = max(w['value'] for w in words) if words else 0
        min_value = min(w['value'] for w in words) if words else 0

        return {
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "content_type": content_type,
            "words": words,
            "max_value": max_value,
            "min_value": min_value,
            "total_words": len(words)
        }
    except Exception as e:
        logger.error(f"Error getting wordcloud data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/treemap")
def get_treemap_data(
    days: int = Query(365, ge=1, le=3650, description="Number of days to analyze"),
    content_type: Optional[str] = Query(None, description="Filter by content type")
):
    """
    Get treemap data for hierarchical concept visualization.
    Shows concept hierarchy with usage counts at each level.
    """
    try:
        start_date, end_date = get_date_range(days)

        # Get usage counts per concept
        usage_results = aggregate_concept_usage(db, content_type, limit=1000)
        usage_map = {str(r['_id']): r['count'] for r in usage_results}

        # Get all concepts with their hierarchy
        concepts = list(db.tag_concepts_v2.find({}))
        concept_map = {str(c['_id']): c for c in concepts}

        # Build parent -> children mapping
        children_map = {}
        root_concepts = []

        for concept in concepts:
            cid = str(concept['_id'])
            parents = concept.get('parents', [])

            if not parents:
                root_concepts.append(concept)
            else:
                for parent_id in parents:
                    pid = str(parent_id)
                    if pid not in children_map:
                        children_map[pid] = []
                    children_map[pid].append(concept)

        # Color palette
        colors = [
            "#2563eb", "#dc2626", "#16a34a", "#9333ea", "#ea580c",
            "#0891b2", "#c026d3", "#84cc16", "#f59e0b", "#6366f1"
        ]

        # Recursive function to build tree
        def build_tree(concept, depth=0, color_idx=0):
            cid = str(concept['_id'])
            node = {
                "name": concept.get('display_name', concept.get('name', 'Unknown')),
                "concept_id": cid,
                "value": usage_map.get(cid, 0),
                "color": colors[color_idx % len(colors)],
                "entity_type": concept.get('entity_type', 'concept')
            }

            children = children_map.get(cid, [])
            if children:
                node["children"] = [
                    build_tree(child, depth + 1, color_idx + i)
                    for i, child in enumerate(sorted(children, key=lambda x: usage_map.get(str(x['_id']), 0), reverse=True))
                ]
            return node

        # Build hierarchy from root concepts
        hierarchy = {
            "name": "All Concepts",
            "children": [
                build_tree(c, 0, i)
                for i, c in enumerate(sorted(root_concepts, key=lambda x: usage_map.get(str(x['_id']), 0), reverse=True))
            ]
        }

        total_value = sum(usage_map.values())

        return {
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "content_type": content_type,
            "hierarchy": hierarchy,
            "total_value": total_value,
            "depth": 3
        }
    except Exception as e:
        logger.error(f"Error getting treemap data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/radar")
def get_radar_chart_data(
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze"),
    compare_periods: bool = Query(False, description="Compare with previous period")
):
    """
    Get radar chart data for multi-dimensional trend analysis
    """
    start_date, end_date = get_date_range(days)

    data = {
        "period_days": days,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "dimensions": [
            "Activity Volume",
            "Concept Diversity",
            "User Engagement",
            "Content Quality",
            "Trend Velocity",
            "Topic Coherence"
        ],
        "current_values": [0, 0, 0, 0, 0, 0],
        "max_values": [100, 100, 100, 100, 100, 100]
    }

    if compare_periods:
        previous_start, previous_end = get_previous_period_range(start_date, days)
        data["previous_period"] = {
            "start_date": previous_start.isoformat(),
            "end_date": previous_end.isoformat(),
            "values": [0, 0, 0, 0, 0, 0]
        }

    return data


@router.get("/sparklines")
def get_sparkline_data(
    hours: int = Query(24, ge=1, le=168, description="Number of hours to analyze")
):
    """
    Get sparkline data for mini trend visualizations
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(hours=hours)

    # Generate hourly data points
    sparkline_data = []
    for i in range(hours):
        sparkline_data.append({
            "hour": i,
            "tweets": 0,
            "articles": 0,
            "papers": 0,
            "total": 0
        })

    return {
        "period_hours": hours,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "sparklines": {
            "tweets": [d["tweets"] for d in sparkline_data],
            "articles": [d["articles"] for d in sparkline_data],
            "papers": [d["papers"] for d in sparkline_data],
            "total": [d["total"] for d in sparkline_data]
        },
        "statistics": {
            "min": 0,
            "max": 0,
            "avg": 0,
            "trend": "stable"
        }
    }


@router.get("/forecast")
def get_trend_forecast(
    days_ahead: int = Query(7, ge=1, le=30, description="Days to forecast ahead"),
    confidence_level: float = Query(0.95, ge=0.5, le=0.99, description="Confidence level")
):
    """
    Get trend forecast data based on historical patterns using moving averages
    """
    import numpy as np

    end_date = datetime.now()
    forecast_start = end_date
    forecast_end = forecast_start + timedelta(days=days_ahead)
    historical_start = end_date - timedelta(days=30)

    # Collect historical data
    daily_counts = defaultdict(lambda: {'tweets': 0, 'articles': 0, 'papers': 0, 'total': 0})

    tweets = fetch_tweets_in_range(db, historical_start, end_date)
    for tweet in tweets:
        day_key = tweet['created_at'].strftime('%Y-%m-%d')
        daily_counts[day_key]['tweets'] += 1

    articles = fetch_articles_in_range(db, historical_start, end_date)
    for article in articles:
        day_key = article['published_at'].strftime('%Y-%m-%d')
        daily_counts[day_key]['articles'] += 1

    papers = fetch_papers_in_range(db, historical_start, end_date)
    for paper in papers:
        day_key = paper['created_at'].strftime('%Y-%m-%d')
        daily_counts[day_key]['papers'] += 1

    # Calculate totals and convert to array
    historical_values = []
    for i in range(30):
        date = historical_start + timedelta(days=i)
        day_key = date.strftime('%Y-%m-%d')
        if day_key in daily_counts:
            daily_counts[day_key]['total'] = (
                daily_counts[day_key]['tweets'] +
                daily_counts[day_key]['articles'] +
                daily_counts[day_key]['papers']
            )
            historical_values.append(daily_counts[day_key]['total'])
        else:
            historical_values.append(0)

    # Calculate moving averages and standard deviation
    if historical_values:
        window_size = min(7, len(historical_values))
        recent_values = historical_values[-window_size:]
        avg_value = np.mean(recent_values) if recent_values else 0
        std_dev = np.std(recent_values) if len(recent_values) > 1 else 1

        # Calculate trend
        if len(recent_values) >= 3:
            x = np.arange(len(recent_values))
            coefficients = np.polyfit(x, recent_values, 1)
            trend_slope = coefficients[0]
        else:
            trend_slope = 0

        # Weekly pattern detection
        weekly_pattern = [1.0] * 7
        if len(historical_values) >= 14:
            for dow in range(7):
                dow_values = [historical_values[i] for i in range(dow, len(historical_values), 7)]
                if dow_values:
                    weekly_pattern[dow] = np.mean(dow_values) / max(avg_value, 1)
    else:
        avg_value = 10
        std_dev = 3
        trend_slope = 0
        weekly_pattern = [1.0] * 7

    # Generate forecast
    forecast_data = []
    current_date = forecast_start
    day_offset = 0

    z_score = {0.95: 1.96, 0.9: 1.645, 0.8: 1.28, 0.7: 1.04, 0.6: 0.84, 0.5: 0.67}
    z = z_score.get(confidence_level, 1.96)

    while current_date <= forecast_end:
        base_prediction = avg_value + (trend_slope * day_offset)
        day_of_week = current_date.weekday()
        predicted_value = max(0, base_prediction * weekly_pattern[day_of_week])

        uncertainty = std_dev * (1 + day_offset * 0.1)
        lower_bound = max(0, predicted_value - z * uncertainty)
        upper_bound = predicted_value + z * uncertainty

        forecast_data.append({
            "date": current_date.strftime('%Y-%m-%d'),
            "predicted_value": round(predicted_value, 1),
            "lower_bound": round(lower_bound, 1),
            "upper_bound": round(upper_bound, 1),
            "confidence": confidence_level
        })

        current_date += timedelta(days=1)
        day_offset += 1

    # Get trending concepts
    trending_concepts = []
    concept_counts = defaultdict(int)

    recent_start = end_date - timedelta(days=7)
    recent_tweets = fetch_tweets_in_range(db, recent_start, end_date)
    for tweet in recent_tweets:
        instances = db.tag_instances.find({
            'content_type': 'tweet',
            'content_id': str(tweet['_id'])
        })
        for instance in instances:
            if instance.get('concept_id'):
                concept_counts[str(instance['concept_id'])] += 1

    for concept_id, count in sorted(concept_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
        concept = get_concept_by_id(db, concept_id)
        if concept:
            trending_concepts.append({
                'name': concept.get('display_name'),
                'current_momentum': count
            })

    return {
        "forecast_days": days_ahead,
        "start_date": forecast_start.isoformat(),
        "end_date": forecast_end.isoformat(),
        "confidence_level": confidence_level,
        "forecast": forecast_data,
        "historical_context": {
            "avg_daily_content": round(avg_value, 1),
            "trend_direction": "increasing" if trend_slope > 0.5 else "decreasing" if trend_slope < -0.5 else "stable",
            "trend_strength": abs(round(trend_slope, 2)),
            "volatility": round(std_dev, 1)
        },
        "trending_concepts": trending_concepts,
        "methodology": "Moving average with trend analysis and weekly patterns",
        "accuracy_note": "Based on 30-day historical patterns. Accuracy decreases for longer forecasts."
    }


@router.post("/summarize")
def generate_summary(
    period: Optional[str] = Query("7days", description="Time period (today, week, month, 7days, 30days, all)"),
    author: Optional[str] = Query(None, description="Filter by author username"),
    tags: List[str] = Query([], description="Filter by concept tags"),
    model: Optional[str] = Query(None, description="LLM model to use for summarization"),
    include_tweets: bool = Query(True, description="Include tweets in summary"),
    include_articles: bool = Query(True, description="Include articles in summary"),
    include_papers: bool = Query(True, description="Include papers in summary"),
    max_tweets: int = Query(100, ge=10, le=500, description="Maximum tweets to include"),
    max_articles: int = Query(50, ge=5, le=200, description="Maximum articles to include"),
    max_papers: int = Query(50, ge=5, le=200, description="Maximum papers to include"),
    paper_date_type: str = Query("created", description="Date type for papers: 'created' (import date) or 'published' (publication date)")
):
    """
    Generate an AI-powered summary of content based on filters
    """
    from app.services.llm_manager import get_llm_manager

    # Parse period and get date range
    days = parse_period_to_days(period)
    start_date, end_date = get_date_range(days)

    # Get concept IDs if filtering by tags
    concept_ids = get_concept_ids_from_tags(db, tags) if tags else None

    # Author filter handling - depends on which sources are selected
    # If only tweets are selected: author = Twitter username
    # If only articles are selected: author = Substack author name
    # If multiple sources or no specific source: ignore author filter (would be ambiguous)
    author_filter_for_tweets = None
    author_filter_for_articles = None

    if author:
        if include_tweets and not include_articles and not include_papers:
            # Only tweets selected - author is Twitter username
            author_filter_for_tweets = author
            logger.info(f"Author filter '{author}' applied for Twitter")
        elif include_articles and not include_tweets and not include_papers:
            # Only articles selected - author is Substack author name
            author_filter_for_articles = author
            logger.info(f"Author filter '{author}' applied for Articles")
        else:
            # Multiple sources selected - ignore author filter (would be ambiguous)
            logger.info(f"Author filter '{author}' ignored - multiple sources selected (would be ambiguous)")

    # Count total available before limits
    tweet_filter = {'created_at': {'$gte': start_date, '$lte': end_date}}
    article_filter = {'published_at': {'$gte': start_date, '$lte': end_date}}

    # Paper filter based on date type selection
    if paper_date_type == "published":
        # Use publication_date (canonical field) with published_date and year fallbacks
        # publication_date is the standard field; published_date kept for backwards compatibility
        paper_filter = {
            '$or': [
                # Has publication_date in range (canonical field)
                {
                    'publication_date': {
                        '$exists': True,
                        '$ne': None,
                        '$ne': '',
                        '$gte': start_date.isoformat(),
                        '$lte': end_date.isoformat()
                    }
                },
                # Has published_date as ISO string (legacy/backwards compatibility)
                {
                    'published_date': {
                        '$exists': True,
                        '$ne': None,
                        '$gte': start_date.isoformat(),
                        '$lte': end_date.isoformat()
                    }
                },
                # No publication_date/published_date but has year in range
                {
                    '$and': [
                        {'$or': [
                            {'publication_date': {'$exists': False}},
                            {'publication_date': None},
                            {'publication_date': ''}
                        ]},
                        {'$or': [
                            {'published_date': {'$exists': False}},
                            {'published_date': None}
                        ]},
                        {'year': {'$gte': start_date.year, '$lte': end_date.year}}
                    ]
                }
            ]
        }
        logger.info(f"Using publication date filter for papers (years {start_date.year}-{end_date.year})")
    else:
        # Default: use created_at (import date)
        paper_filter = {'created_at': {'$gte': start_date, '$lte': end_date}}

    # Apply author filters
    if author_filter_for_tweets:
        tweet_filter['author_username'] = author_filter_for_tweets
    if author_filter_for_articles:
        article_filter['author_name'] = author_filter_for_articles

    # Apply tag filters to counts
    if concept_ids:
        from bson import ObjectId as BsonObjectId
        tweet_ids = get_tagged_content_ids(db, concept_ids, 'tweet')
        article_ids = [BsonObjectId(aid) for aid in get_tagged_content_ids(db, concept_ids, 'article') if len(aid) == 24]
        paper_ids = [BsonObjectId(pid) for pid in get_tagged_content_ids(db, concept_ids, 'paper') if len(pid) == 24]

        tweet_filter['_id'] = {'$in': tweet_ids} if tweet_ids else {'$in': []}
        article_filter['_id'] = {'$in': article_ids} if article_ids else {'$in': []}
        paper_filter['_id'] = {'$in': paper_ids} if paper_ids else {'$in': []}

    total_tweets_available = db.tweets.count_documents(tweet_filter) if include_tweets else 0
    total_articles_available = db.articles.count_documents(article_filter) if include_articles else 0
    total_papers_available = db.papers.count_documents(paper_filter) if include_papers else 0

    # Fetch content using helpers
    content = fetch_all_content_in_range(
        db, start_date, end_date,
        include_tweets=include_tweets,
        include_articles=include_articles,
        include_papers=include_papers,
        author=author_filter_for_tweets,
        article_author=author_filter_for_articles,
        concept_ids=concept_ids,
        max_tweets=max_tweets,
        max_articles=max_articles,
        max_papers=max_papers,
        paper_date_type=paper_date_type
    )

    tweets = content['tweets']
    articles = content['articles']
    papers = content['papers']

    # Check if data was truncated
    data_truncated = (
        total_tweets_available > max_tweets or
        total_articles_available > max_articles or
        total_papers_available > max_papers
    )

    # Calculate statistics
    stats = calculate_content_statistics(tweets, articles, papers)

    # Collect key topics
    key_topics = collect_key_topics(db, tweets, sample_size=20)

    # Prepare content sample for LLM
    content_sample = prepare_content_sample(tweets, articles, papers)

    # Generate summary using LLM
    summary_text = ""
    model_used = model or "articleSummarization"

    if content_sample:
        try:
            llm_manager = get_llm_manager()
            date_range_str = f"from {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}"
            prompt = build_summarization_prompt(content_sample, key_topics, stats, date_range_str, days)

            messages = [{"role": "user", "content": prompt}]

            if model:
                logger.info(f"Using selected model for summarization: {model}")
                response = llm_manager.completion_sync(
                    task_type=model,
                    messages=messages,
                    user_id='default'
                )
            else:
                response = llm_manager.completion_sync(
                    task_type='articleSummarization',
                    messages=messages,
                    user_id='default'
                )

            summary_text = response.choices[0].message.content
            logger.info(f"Successfully generated summary using model: {model_used}")

        except Exception as e:
            logger.error(f"Error generating LLM summary with model '{model_used}': {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            summary_text = build_fallback_summary(key_topics, stats, days)
    else:
        summary_text = "No content found for the specified filters. Try adjusting the time period or removing some filters."

    # Build truncation warning
    truncation_warning = None
    if data_truncated:
        truncation_warning = (
            f"Note: Data was limited to {max_tweets} tweets, {max_articles} articles, {max_papers} papers. "
            f"Total available in this period: {total_tweets_available} tweets, {total_articles_available} articles, {total_papers_available} papers."
        )

    return {
        "summary": summary_text,
        "stats": {
            "tweet_count": len(tweets),
            "article_count": len(articles),
            "paper_count": len(papers),
            "unique_authors": stats['unique_authors'],
            "total_likes": stats['total_likes'],
            "total_retweets": stats['total_retweets'],
            "time_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_available": {
                "tweets": total_tweets_available,
                "articles": total_articles_available,
                "papers": total_papers_available
            }
        },
        "top_topics": [{"topic": topic, "count": count} for topic, count in key_topics.most_common(10)],
        "filters": {
            "period": period,
            "tags": tags,
            "author": author
        },
        "model_used": model_used,
        "data_truncated": data_truncated,
        "truncation_warning": truncation_warning,
        "limits_used": {
            "max_tweets": max_tweets,
            "max_articles": max_articles,
            "max_papers": max_papers
        }
    }
