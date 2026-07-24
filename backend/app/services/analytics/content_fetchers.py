"""
Content fetching helper functions for analytics.
"""

from datetime import datetime
from typing import Dict, List, Optional
from bson import ObjectId

from app.services.analytics.concept_helpers import get_tagged_content_ids


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
    # Exclude review papers from analytics
    review_filter = {'paper_type': {'$ne': 'review'}}

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

    query.update(review_filter)

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
