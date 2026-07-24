"""
Timeline and statistics helper functions for analytics.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple


def initialize_timeline_dict(
    start_date: datetime,
    end_date: datetime
) -> Dict[str, Dict]:
    """
    Initialize a timeline dictionary with empty entries for each day.

    Args:
        start_date: Start datetime
        end_date: End datetime

    Returns:
        Dict mapping date string to entry dict
    """
    timeline_dict = {}
    current_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)

    while current_date <= end_date:
        date_key = current_date.strftime('%Y-%m-%d')
        timeline_dict[date_key] = {
            "date": current_date.isoformat(),
            "tweets": 0,
            "articles": 0,
            "papers": 0,
            "total": 0,
            "concepts": set()
        }
        current_date += timedelta(days=1)

    return timeline_dict


def initialize_hourly_dict(
    start_time: datetime,
    hours: int
) -> Dict[str, Dict]:
    """
    Initialize an hourly dictionary with empty entries.

    Args:
        start_time: Start datetime
        hours: Number of hours

    Returns:
        Dict mapping hour string to entry dict
    """
    hourly_dict = {}

    for i in range(hours):
        hour_time = start_time + timedelta(hours=i)
        hour_key = hour_time.strftime('%Y-%m-%d %H:00')
        hourly_dict[hour_key] = {
            "hour": hour_key,
            "count": 0,
            "tweets": 0,
            "articles": 0,
            "papers": 0
        }

    return hourly_dict


def populate_timeline_from_content(
    db,
    timeline_dict: Dict[str, Dict],
    tweets: List[Dict],
    articles: List[Dict],
    papers: List[Dict],
    track_concepts: bool = True
) -> Tuple[int, int, int]:
    """
    Populate timeline dict with content counts.

    Args:
        db: MongoDB database instance
        timeline_dict: Timeline dict to populate
        tweets: List of tweet documents
        articles: List of article documents
        papers: List of paper documents
        track_concepts: Whether to track concepts per day

    Returns:
        Tuple of (total_tweets, total_articles, total_papers)
    """
    total_tweets = 0
    total_articles = 0
    total_papers = 0

    # Process tweets
    for tweet in tweets:
        date_key = tweet['created_at'].strftime('%Y-%m-%d')
        if date_key in timeline_dict:
            timeline_dict[date_key]["tweets"] += 1
            total_tweets += 1

            if track_concepts:
                instances = db.tag_instances.find({
                    'content_type': 'tweet',
                    'content_id': str(tweet['_id'])
                })
                for instance in instances:
                    if instance.get('concept_id'):
                        timeline_dict[date_key]["concepts"].add(str(instance['concept_id']))

    # Process articles
    for article in articles:
        date_key = article['published_at'].strftime('%Y-%m-%d')
        if date_key in timeline_dict:
            timeline_dict[date_key]["articles"] += 1
            total_articles += 1

            if track_concepts:
                instances = db.tag_instances.find({
                    'content_type': 'article',
                    'content_id': str(article['_id'])
                })
                for instance in instances:
                    if instance.get('concept_id'):
                        timeline_dict[date_key]["concepts"].add(str(instance['concept_id']))

    # Process papers
    for paper in papers:
        date_key = paper['created_at'].strftime('%Y-%m-%d')
        if date_key in timeline_dict:
            timeline_dict[date_key]["papers"] += 1
            total_papers += 1

            if track_concepts:
                instances = db.tag_instances.find({
                    'content_type': 'paper',
                    'content_id': str(paper['_id'])
                })
                for instance in instances:
                    if instance.get('concept_id'):
                        timeline_dict[date_key]["concepts"].add(str(instance['concept_id']))

    return total_tweets, total_articles, total_papers


def calculate_content_statistics(
    tweets: List[Dict],
    articles: List[Dict] = None,
    papers: List[Dict] = None
) -> Dict[str, Any]:
    """
    Calculate statistics from content items.

    Args:
        tweets: List of tweet documents
        articles: List of article documents (optional)
        papers: List of paper documents (optional)

    Returns:
        Dict with statistics
    """
    unique_authors = set()
    total_likes = 0
    total_retweets = 0

    for tweet in tweets:
        unique_authors.add(tweet.get('author_username', ''))
        metrics = tweet.get('metrics', {})
        total_likes += metrics.get('like_count', 0)
        total_retweets += metrics.get('retweet_count', 0)

    return {
        'unique_authors': len(unique_authors),
        'unique_author_list': list(unique_authors),
        'total_likes': total_likes,
        'total_retweets': total_retweets,
        'tweet_count': len(tweets),
        'article_count': len(articles) if articles else 0,
        'paper_count': len(papers) if papers else 0
    }


def find_peak_and_lowest(timeline_data: List[Dict]) -> Dict[str, Any]:
    """
    Find peak and lowest activity days from timeline data.

    Args:
        timeline_data: List of timeline entries with 'total' field

    Returns:
        Dict with peak and lowest info
    """
    peak_day = None
    peak_count = 0
    lowest_day = None
    lowest_count = float('inf')

    for entry in timeline_data:
        total = entry.get('total', 0)
        date = entry.get('date', '')

        if total > peak_count:
            peak_count = total
            peak_day = date
        if total < lowest_count:
            lowest_count = total
            lowest_day = date

    return {
        'peak_day': peak_day,
        'peak_count': peak_count,
        'lowest_day': lowest_day,
        'lowest_count': lowest_count if lowest_count != float('inf') else 0
    }


def aggregate_concept_usage(
    db,
    content_type: Optional[str] = None,
    limit: int = 100
) -> List[Dict]:
    """
    Aggregate concept usage counts using MongoDB aggregation.

    Args:
        db: MongoDB database instance
        content_type: Optional filter by content type
        limit: Maximum results

    Returns:
        List of {_id: concept_id, count: usage_count}
    """
    match_filter = {}
    if content_type:
        match_filter['content_type'] = content_type

    pipeline = [
        {'$match': match_filter} if match_filter else {'$match': {}},
        {'$group': {
            '_id': '$concept_id',
            'count': {'$sum': 1}
        }},
        {'$match': {'_id': {'$ne': None}}},
        {'$sort': {'count': -1}},
        {'$limit': limit}
    ]

    return list(db.tag_instances.aggregate(pipeline))
