"""
Analytics Helper Functions
Modular, reusable functions for analytics and trend analysis
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import Counter, defaultdict
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# PERIOD AND DATE HELPERS
# =============================================================================

def parse_period_to_days(period: str) -> int:
    """
    Convert period string to number of days.

    Args:
        period: Period string like 'today', 'week', '30days', 'all'

    Returns:
        Number of days as integer
    """
    period_mapping = {
        "today": 1,
        "3days": 3,
        "week": 7,
        "7days": 7,
        "14days": 14,
        "month": 30,
        "30days": 30,
        "60days": 60,
        "90days": 90,
        "120days": 120,
        "200days": 200,
        "365days": 365,
        "all": 3650,  # ~10 years - effectively all data
    }
    return period_mapping.get(period, 7)


def get_date_range(days: int, end_date: Optional[datetime] = None) -> Tuple[datetime, datetime]:
    """
    Calculate date range from number of days.

    Args:
        days: Number of days to look back
        end_date: End date (defaults to now)

    Returns:
        Tuple of (start_date, end_date)
    """
    if end_date is None:
        end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    return start_date, end_date


def get_previous_period_range(start_date: datetime, days: int) -> Tuple[datetime, datetime]:
    """
    Calculate the previous period date range for comparison.

    Args:
        start_date: Start of current period
        days: Number of days in period

    Returns:
        Tuple of (previous_start, previous_end)
    """
    previous_end = start_date
    previous_start = previous_end - timedelta(days=days)
    return previous_start, previous_end


# =============================================================================
# CONCEPT/TAG HELPERS
# =============================================================================

def get_concept_ids_from_tags(db, tags: List[str]) -> List[ObjectId]:
    """
    Convert tag display names to concept ObjectIds.

    Args:
        db: MongoDB database instance
        tags: List of tag display names

    Returns:
        List of concept ObjectIds
    """
    concept_ids = []
    for tag in tags:
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
    if not concept_ids:
        return []

    instances = db.tag_instances.find({
        'content_type': content_type,
        'concept_id': {'$in': concept_ids}
    })
    return [inst['content_id'] for inst in instances]


def get_concept_by_id(db, concept_id) -> Optional[Dict]:
    """
    Get concept document by ID.

    Args:
        db: MongoDB database instance
        concept_id: Concept ObjectId

    Returns:
        Concept document or None
    """
    return db.tag_concepts_v2.find_one({'_id': concept_id})


def get_concepts_by_ids(db, concept_ids: List) -> Dict[str, Dict]:
    """
    Get multiple concepts by IDs and return as a map.

    Args:
        db: MongoDB database instance
        concept_ids: List of concept ObjectIds

    Returns:
        Dict mapping string ID to concept document
    """
    concepts = list(db.tag_concepts_v2.find({'_id': {'$in': concept_ids}}))
    return {str(c['_id']): c for c in concepts}


# =============================================================================
# TAG COUNTING HELPERS
# =============================================================================

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
        date_key = item.get(date_field, datetime.now()).strftime('%Y-%m-%d') if timeline_dict else None

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


# =============================================================================
# CONTENT FETCHING HELPERS
# =============================================================================

def build_date_filter(
    start_date: datetime,
    end_date: datetime,
    date_field: str = 'created_at'
) -> Dict:
    """
    Build MongoDB date range filter.

    Args:
        start_date: Start datetime
        end_date: End datetime
        date_field: Field name for date

    Returns:
        MongoDB filter dict
    """
    return {date_field: {'$gte': start_date, '$lte': end_date}}


def fetch_tweets_in_range(
    db,
    start_date: datetime,
    end_date: datetime,
    author: Optional[str] = None,
    content_ids: Optional[List[str]] = None,
    limit: Optional[int] = None
) -> List[Dict]:
    """
    Fetch tweets within date range with optional filters.

    Args:
        db: MongoDB database instance
        start_date: Start datetime
        end_date: End datetime
        author: Optional author username filter
        content_ids: Optional list of specific tweet IDs
        limit: Optional maximum number to return

    Returns:
        List of tweet documents
    """
    query = {'created_at': {'$gte': start_date, '$lte': end_date}}

    if author:
        query['author_username'] = author

    if content_ids is not None:
        query['_id'] = {'$in': content_ids}

    cursor = db.tweets.find(query).sort('created_at', -1)

    if limit:
        cursor = cursor.limit(limit)

    return list(cursor)


def fetch_articles_in_range(
    db,
    start_date: datetime,
    end_date: datetime,
    author_name: Optional[str] = None,
    content_ids: Optional[List[ObjectId]] = None,
    limit: Optional[int] = None
) -> List[Dict]:
    """
    Fetch articles within date range with optional filters.

    Args:
        db: MongoDB database instance
        start_date: Start datetime
        end_date: End datetime
        author_name: Optional author name filter (Substack author)
        content_ids: Optional list of specific article ObjectIds
        limit: Optional maximum number to return

    Returns:
        List of article documents
    """
    query = {'published_at': {'$gte': start_date, '$lte': end_date}}

    if author_name:
        query['author_name'] = author_name

    if content_ids is not None:
        query['_id'] = {'$in': content_ids}

    cursor = db.articles.find(query).sort('published_at', -1)

    if limit:
        cursor = cursor.limit(limit)

    return list(cursor)


def fetch_papers_in_range(
    db,
    start_date: datetime,
    end_date: datetime,
    content_ids: Optional[List[ObjectId]] = None,
    limit: Optional[int] = None,
    date_type: str = "created"
) -> List[Dict]:
    """
    Fetch papers within date range with optional filters.

    Args:
        db: MongoDB database instance
        start_date: Start datetime
        end_date: End datetime
        content_ids: Optional list of specific paper ObjectIds
        limit: Optional maximum number to return
        date_type: "created" for import date, "published" for publication date

    Returns:
        List of paper documents
    """
    if date_type == "published":
        # Use publication_date (canonical field) with published_date and year fallbacks
        # publication_date is the standard field; published_date kept for backwards compatibility
        query = {
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
                # Has published_date as ISO string in range (legacy/backwards compatibility)
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
        sort_field = 'created_at'  # Sort by created_at since published dates may be in different formats
    else:
        # Default: use created_at (import date)
        query = {'created_at': {'$gte': start_date, '$lte': end_date}}
        sort_field = 'created_at'

    if content_ids is not None:
        query['_id'] = {'$in': content_ids}

    cursor = db.papers.find(query).sort(sort_field, -1)

    if limit:
        cursor = cursor.limit(limit)

    return list(cursor)


def fetch_all_content_in_range(
    db,
    start_date: datetime,
    end_date: datetime,
    include_tweets: bool = True,
    include_articles: bool = True,
    include_papers: bool = True,
    author: Optional[str] = None,
    article_author: Optional[str] = None,
    concept_ids: Optional[List[ObjectId]] = None,
    max_tweets: int = 100,
    max_articles: int = 50,
    max_papers: int = 50,
    paper_date_type: str = "created"
) -> Dict[str, List[Dict]]:
    """
    Fetch all content types within date range with filters.

    Args:
        db: MongoDB database instance
        start_date: Start datetime
        end_date: End datetime
        include_tweets: Whether to include tweets
        include_articles: Whether to include articles
        include_papers: Whether to include papers
        author: Optional author filter for tweets (Twitter username)
        article_author: Optional author filter for articles (Substack author name)
        concept_ids: Optional concept IDs to filter by
        max_tweets: Maximum tweets to return
        max_articles: Maximum articles to return
        max_papers: Maximum papers to return
        paper_date_type: "created" for import date, "published" for publication date

    Returns:
        Dict with 'tweets', 'articles', 'papers' keys
    """
    result = {
        'tweets': [],
        'articles': [],
        'papers': []
    }

    # Get tagged content IDs if filtering by concepts
    tweet_ids = None
    article_ids = None
    paper_ids = None

    if concept_ids:
        tweet_ids = get_tagged_content_ids(db, concept_ids, 'tweet')
        article_ids = [ObjectId(aid) for aid in get_tagged_content_ids(db, concept_ids, 'article') if len(aid) == 24]
        paper_ids = [ObjectId(pid) for pid in get_tagged_content_ids(db, concept_ids, 'paper') if len(pid) == 24]

        # If no content found for any type with tags, set to empty list to return no results
        if not tweet_ids:
            tweet_ids = []
        if not article_ids:
            article_ids = []
        if not paper_ids:
            paper_ids = []

    if include_tweets:
        result['tweets'] = fetch_tweets_in_range(
            db, start_date, end_date,
            author=author,
            content_ids=tweet_ids,
            limit=max_tweets
        )

    if include_articles:
        result['articles'] = fetch_articles_in_range(
            db, start_date, end_date,
            author_name=article_author,
            content_ids=article_ids,
            limit=max_articles
        )

    if include_papers:
        result['papers'] = fetch_papers_in_range(
            db, start_date, end_date,
            content_ids=paper_ids,
            limit=max_papers,
            date_type=paper_date_type
        )

    return result


# =============================================================================
# TIMELINE HELPERS
# =============================================================================

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


# =============================================================================
# STATISTICS HELPERS
# =============================================================================

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


# =============================================================================
# AGGREGATION HELPERS
# =============================================================================

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


# =============================================================================
# SUMMARIZATION HELPERS
# =============================================================================

def collect_key_topics(
    db,
    tweets: List[Dict],
    sample_size: int = 20
) -> Counter:
    """
    Collect key topics from tweet samples.

    Args:
        db: MongoDB database instance
        tweets: List of tweet documents
        sample_size: Number of tweets to sample

    Returns:
        Counter of topic display names
    """
    key_topics = Counter()

    for tweet in tweets[:sample_size]:
        instances = db.tag_instances.find({
            'content_type': 'tweet',
            'content_id': str(tweet['_id'])
        })
        for instance in instances:
            if instance.get('concept_id'):
                concept = db.tag_concepts_v2.find_one({'_id': instance['concept_id']})
                if concept:
                    key_topics[concept.get('display_name')] += 1

    return key_topics


def prepare_content_sample(
    tweets: List[Dict],
    articles: List[Dict],
    papers: List[Dict],
    tweet_limit: int = 10,
    article_limit: int = 5,
    paper_limit: int = 5
) -> List[str]:
    """
    Prepare content samples for summarization prompt.

    Args:
        tweets: List of tweet documents
        articles: List of article documents
        papers: List of paper documents
        tweet_limit: Max tweets to include
        article_limit: Max articles to include
        paper_limit: Max papers to include

    Returns:
        List of content description strings
    """
    content_sample = []

    for tweet in tweets[:tweet_limit]:
        content_sample.append(
            f"Tweet by @{tweet.get('author_username', 'unknown')}: {tweet.get('text', '')[:200]}"
        )

    for article in articles[:article_limit]:
        content_sample.append(f"Article: {article.get('title', 'Untitled')}")

    for paper in papers[:paper_limit]:
        content_sample.append(f"Paper: {paper.get('title', 'Untitled')}")

    return content_sample


def build_summarization_prompt(
    content_sample: List[str],
    key_topics: Counter,
    stats: Dict[str, Any],
    date_range_str: str,
    days: int
) -> str:
    """
    Build the summarization prompt for LLM.

    Args:
        content_sample: List of content descriptions
        key_topics: Counter of key topics
        stats: Statistics dict
        date_range_str: Human-readable date range
        days: Number of days

    Returns:
        Formatted prompt string
    """
    return f"""You are an AI research analyst. Analyze the following AI/ML content {date_range_str} (the past {days} day(s)) and provide a comprehensive summary.

## Content to Analyze

### Tweets ({stats.get('tweet_count', 0)} total)
{chr(10).join(content_sample[:15])}

### Key Topics (by frequency)
{', '.join([f"**{topic}** ({count})" for topic, count in key_topics.most_common(10)])}

### Statistics
- Total tweets analyzed: {stats.get('tweet_count', 0)}
- Total articles analyzed: {stats.get('article_count', 0)}
- Total papers analyzed: {stats.get('paper_count', 0)}
- Unique authors: {stats.get('unique_authors', 0)}
- Total engagement: {stats.get('total_likes', 0):,} likes, {stats.get('total_retweets', 0):,} retweets

## Your Task

Please provide a comprehensive summary including:

### 1. Executive Summary
A 3-4 sentence overview of the main themes, trends, and notable developments in the AI/ML space based on this content.

### 2. Key Insights
- What are the most important developments or announcements?
- What topics are generating the most discussion?
- Are there any emerging trends or shifts in focus?

### 3. Notable Highlights
- Any significant product launches, research breakthroughs, or industry news
- Influential voices or perspectives that stood out
- Controversial or debated topics

### 4. Engagement Analysis
Brief analysis of what content resonated most with the audience based on engagement metrics.

Write in a professional, analytical tone. Be specific and cite examples from the content when possible."""


def build_fallback_summary(
    key_topics: Counter,
    stats: Dict[str, Any],
    days: int
) -> str:
    """
    Build fallback summary when LLM is unavailable.

    Args:
        key_topics: Counter of key topics
        stats: Statistics dict
        days: Number of days

    Returns:
        Fallback summary text
    """
    top_topics = [topic for topic, _ in key_topics.most_common(5)]

    return f"""## Summary (Auto-generated)

During the past {days} day(s), the AI/ML community has been actively discussing **{', '.join(top_topics) if top_topics else 'various topics'}**.

### Content Analyzed
- **{stats.get('tweet_count', 0)}** tweets from {stats.get('unique_authors', 0)} unique authors
- **{stats.get('article_count', 0)}** articles
- **{stats.get('paper_count', 0)}** research papers

### Engagement
The content showed {'strong' if stats.get('total_likes', 0) > 1000 else 'moderate'} engagement with **{stats.get('total_likes', 0):,}** total likes and **{stats.get('total_retweets', 0):,}** retweets.

*Note: Full AI analysis was unavailable. This is a basic statistical summary.*"""
