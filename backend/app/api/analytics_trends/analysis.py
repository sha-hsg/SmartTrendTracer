"""
Complex analysis and LLM-powered endpoints for analytics trends.
Contains summarization and at-a-glance routes.
Split from analytics_trends_mongodb.py.
"""

from fastapi import APIRouter, Query
from typing import List, Optional
from datetime import datetime, timedelta, timezone

from .utils import (
    logger,
    db,
    parse_period_to_days,
    get_date_range,
    get_concept_ids_from_tags,
    get_tagged_content_ids,
    fetch_all_content_in_range,
    calculate_content_statistics,
    collect_key_topics,
    prepare_content_sample,
    build_summarization_prompt,
    build_fallback_summary,
)
from app.repositories import analytics_trends_analysis_queries as queries

router = APIRouter()


@router.post("/summarize")
def generate_summary(
    period: Optional[str] = Query("7days", description="Time period (today, week, month, 7days, 30days, all)"),
    author: Optional[str] = Query(None, description="Filter by author username"),
    tags: List[str] = Query([], description="Filter by concept tags"),
    model: Optional[str] = Query(None, description="LLM model to use for summarization"),
    include_tweets: bool = Query(True, description="Include tweets in summary"),
    include_articles: bool = Query(True, description="Include articles in summary"),
    include_papers: bool = Query(True, description="Include papers in summary"),
    max_tweets: int = Query(1000, ge=10, le=5000, description="Maximum tweets to include"),
    max_articles: int = Query(50, ge=5, le=200, description="Maximum articles to include"),
    max_papers: int = Query(50, ge=5, le=200, description="Maximum papers to include"),
    paper_date_type: str = Query("created", description="Date type for papers: 'created' (import date) or 'published' (publication date)"),
    detail_level: str = Query("standard", description="Detail level: brief, standard, detailed, executive"),
    full_content: bool = Query(False, description="If true, include ALL loaded content in the prompt (no per-detail-level slicing). The fetch is still capped by max_tweets/articles/papers.")
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
                        '$nin': [None, ''],
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

    total_tweets_available = queries.tweets_count_documents__generate_summary(tweet_filter) if include_tweets else 0
    total_articles_available = queries.articles_count_documents__generate_summary(article_filter) if include_articles else 0
    total_papers_available = queries.papers_count_documents__generate_summary(paper_filter) if include_papers else 0

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

    # Validate detail_level
    if detail_level not in ('brief', 'standard', 'detailed', 'executive'):
        detail_level = 'standard'

    # Collect key topics
    key_topics = collect_key_topics(db, tweets, sample_size=20, detail_level=detail_level, full_content=full_content)

    # Prepare content sample for LLM
    content_sample = prepare_content_sample(tweets, articles, papers, detail_level=detail_level, full_content=full_content)

    # Auto-fallback: if the selected window has no content, probe outside the
    # window and re-fetch over all time when matching data exists elsewhere.
    # This handles inactive accounts (e.g. last tweet > selected period ago).
    diagnostic: Optional[dict] = None

    if not content_sample:
        # Rebuild filters without the date constraint, preserving author/tag filters.
        any_tweet_filter = {k: v for k, v in tweet_filter.items() if k != 'created_at'}
        any_article_filter = {k: v for k, v in article_filter.items() if k != 'published_at'}
        any_paper_filter = {
            k: v for k, v in paper_filter.items()
            if k not in ('created_at', '$or')
        } if paper_date_type != "published" else {
            k: v for k, v in paper_filter.items() if k != '$or'
        }

        total_tweets_anytime = queries.tweets_count_documents__generate_summary_2(any_tweet_filter) if include_tweets else 0
        total_articles_anytime = queries.articles_count_documents__generate_summary_2(any_article_filter) if include_articles else 0
        total_papers_anytime = queries.papers_count_documents__generate_summary_2(any_paper_filter) if include_papers else 0

        if (total_tweets_anytime + total_articles_anytime + total_papers_anytime) > 0:
            # Find the single most-recent item across the enabled sources
            most_recent_date = None
            if total_tweets_anytime > 0:
                latest = queries.tweets_find__generate_summary(any_tweet_filter)
                for t in latest:
                    most_recent_date = t.get('created_at')
            if total_articles_anytime > 0:
                latest = queries.articles_find__generate_summary(any_article_filter)
                for a in latest:
                    pub = a.get('published_at')
                    if pub and (most_recent_date is None or pub > most_recent_date):
                        most_recent_date = pub

            # Extend to all-time and refetch
            extended_start = end_date - timedelta(days=3650)
            content = fetch_all_content_in_range(
                db, extended_start, end_date,
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

            stats = calculate_content_statistics(tweets, articles, papers)
            key_topics = collect_key_topics(db, tweets, sample_size=20, detail_level=detail_level, full_content=full_content)
            content_sample = prepare_content_sample(tweets, articles, papers, detail_level=detail_level, full_content=full_content)

            # Reflect the extended range and totals in the response
            start_date = extended_start
            total_tweets_available = total_tweets_anytime
            total_articles_available = total_articles_anytime
            total_papers_available = total_papers_anytime

            # Build human-readable diagnostic
            now = datetime.now(timezone.utc)
            days_since = None
            date_str = "unknown"
            if most_recent_date is not None:
                if most_recent_date.tzinfo is None:
                    most_recent_date = most_recent_date.replace(tzinfo=timezone.utc)
                days_since = (now - most_recent_date).days
                date_str = most_recent_date.strftime('%b %d, %Y')

            total_items = total_tweets_anytime + total_articles_anytime + total_papers_anytime
            if author:
                msg = (
                    f"@{author} has {total_items} item(s) in the database but none in the last {days} days. "
                    f"Most recent activity: {date_str}"
                    f"{f' (~{days_since} days ago)' if days_since is not None else ''}. "
                    f"Showing summary of all available content instead."
                )
            else:
                msg = (
                    f"No content in the last {days} days. "
                    f"Most recent: {date_str}"
                    f"{f' (~{days_since} days ago)' if days_since is not None else ''}. "
                    f"Showing summary of all available content instead."
                )

            diagnostic = {
                'auto_extended': True,
                'original_period_days': days,
                'most_recent_date': most_recent_date.isoformat() if most_recent_date else None,
                'days_since_most_recent': days_since,
                'total_in_db': {
                    'tweets': total_tweets_anytime,
                    'articles': total_articles_anytime,
                    'papers': total_papers_anytime,
                },
                'message': msg,
            }

    # Generate summary using LLM
    summary_text = ""
    model_used = model or "articleSummarization"

    if content_sample:
        try:
            llm_manager = get_llm_manager()
            date_range_str = f"from {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}"
            prompt = build_summarization_prompt(
                content_sample, key_topics, stats, date_range_str, days,
                detail_level=detail_level,
                full_content=full_content,
                # Only frame as single-author when the filter was actually applied
                # (i.e. only tweets selected and author given).
                author=author_filter_for_tweets,
            )

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
        # No content even after auto-extending — truly empty for this filter combo
        if author:
            summary_text = (
                f"No content found for @{author} with the specified filters. "
                f"This account/author has no items in the database matching your filters."
            )
        else:
            summary_text = "No content found for the specified filters. Try adjusting the time period or removing some filters."
        if diagnostic is None:
            diagnostic = {
                'auto_extended': False,
                'original_period_days': days,
                'most_recent_date': None,
                'days_since_most_recent': None,
                'total_in_db': {'tweets': 0, 'articles': 0, 'papers': 0},
                'message': summary_text,
            }

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
        },
        "detail_level": detail_level,
        "diagnostic": diagnostic
    }


@router.get("/at-a-glance")
def get_trends_at_a_glance(
    hours: int = Query(48, ge=24, le=168, description="Time window in hours"),
    anomaly_threshold: float = Query(2.5, ge=1.0, le=5.0, description="Z-score threshold for anomalies"),
    limit: int = Query(10, ge=5, le=25, description="Max items per category")
):
    """
    Get at-a-glance trend summary with hot topics, declining topics, stable evergreens, and anomalies.

    Hot Topics: >50% increase in activity
    Declining: >30% decrease in activity
    Stable: Consistent activity with <20% change
    Anomalies: Z-score > threshold indicating spikes
    """
    from app.services.trend_overview_service import compute_at_a_glance
    return compute_at_a_glance(hours=hours, anomaly_threshold=anomaly_threshold, limit=limit)
