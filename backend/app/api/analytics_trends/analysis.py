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
    fit_to_token_budget,
    build_summarization_prompt,
    build_fallback_summary,
)
from app.repositories import analytics_trends_analysis_queries as queries

router = APIRouter()

AUTO_MAX_TWEETS = 20000          # fetch ceiling without Data Limits (the model budget trims further)
AUTO_MAX_DOCS = 1000
PROMPT_CONTEXT_SHARE = 0.5       # rest stays free for instructions, output and reasoning tokens


@router.post("/summarize")
def generate_summary(
    period: Optional[str] = Query("7days", description="Time period (today, week, month, 7days, 30days, all)"),
    author: Optional[str] = Query(None, description="Filter by author username"),
    tags: List[str] = Query([], description="Filter by concept tags"),
    model: Optional[str] = Query(None, description="LLM model to use for summarization"),
    include_tweets: bool = Query(True, description="Include tweets in summary"),
    include_articles: bool = Query(True, description="Include articles in summary"),
    include_papers: bool = Query(True, description="Include papers in summary"),
    max_tweets: Optional[int] = Query(None, ge=10, le=AUTO_MAX_TWEETS, description="Cap on tweets; omit = all that fit the model"),
    max_articles: Optional[int] = Query(None, ge=5, le=AUTO_MAX_DOCS, description="Cap on articles; omit = all that fit the model"),
    max_papers: Optional[int] = Query(None, ge=5, le=AUTO_MAX_DOCS, description="Cap on papers; omit = all that fit the model"),
    paper_date_type: str = Query("created", description="Date type for papers: 'created' (import date) or 'published' (publication date)"),
    detail_level: str = Query("standard", description="Detail level: brief, standard, detailed, executive (depth and length of the answer)"),
):
    """
    Generate an AI-powered summary of content based on filters.

    Everything in the period goes into the prompt as long as it fits the input
    context of the model that will answer (PROMPT_CONTEXT_SHARE of it); beyond
    that an evenly spaced tweet sample keeps the whole period covered. Was: a
    fixed 1000/50/50 fetch cap and only 10-40 items in the prompt.
    """
    from app.services.llm_manager import get_llm_manager
    llm_manager = get_llm_manager()
    context = llm_manager.context_window('articleSummarization', model)
    token_budget = int(context['max_input_tokens'] * PROMPT_CONTEXT_SHARE)
    fetch_tweets = max_tweets or AUTO_MAX_TWEETS
    fetch_articles = max_articles or AUTO_MAX_DOCS
    fetch_papers = max_papers or AUTO_MAX_DOCS

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
        # publication_date is an ISO string (repositories.paper_dates), so a string range works
        paper_filter = {'publication_date': {'$gte': start_date.date().isoformat(), '$lte': end_date.date().isoformat()}}
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
        max_tweets=fetch_tweets,
        max_articles=fetch_articles,
        max_papers=fetch_papers,
        paper_date_type=paper_date_type
    )

    tweets = content['tweets']
    articles = content['articles']
    papers = content['papers']


    # Calculate statistics
    stats = calculate_content_statistics(tweets, articles, papers)

    # Validate detail_level
    if detail_level not in ('brief', 'standard', 'detailed', 'executive'):
        detail_level = 'standard'

    # Collect key topics
    key_topics = collect_key_topics(db, tweets, detail_level=detail_level, full_content=True)

    # Prompt content: everything that fits the model's context budget
    prompt_tweets = fit_to_token_budget(tweets, articles, papers, token_budget)
    content_sample = prepare_content_sample(prompt_tweets, articles, papers, detail_level=detail_level, full_content=True)

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
                max_tweets=fetch_tweets,
                max_articles=fetch_articles,
                max_papers=fetch_papers,
                paper_date_type=paper_date_type
            )
            tweets = content['tweets']
            articles = content['articles']
            papers = content['papers']

            stats = calculate_content_statistics(tweets, articles, papers)
            key_topics = collect_key_topics(db, tweets, detail_level=detail_level, full_content=True)
            prompt_tweets = fit_to_token_budget(tweets, articles, papers, token_budget)
            content_sample = prepare_content_sample(prompt_tweets, articles, papers, detail_level=detail_level, full_content=True)

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
    summary_error = None

    if content_sample:
        try:
            date_range_str = f"from {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}"
            prompt = build_summarization_prompt(
                content_sample, key_topics, stats, date_range_str, days,
                prompt=llm_manager.get_prompt('trend_summarization'),
                detail_level=detail_level,
                full_content=True,
                # Only frame as single-author when the filter was actually applied
                # (i.e. only tweets selected and author given).
                author=author_filter_for_tweets,
            )
            # a UI model choice is a model, not a task: route it via the central resolver
            routed = llm_manager.resolve_model_override(model)
            response = llm_manager.completion_sync(
                task_type='articleSummarization',
                messages=[{"role": "user", "content": prompt}],
                user_id='default',
                override_params={'model': routed} if routed else None,
            )
            summary_text = response.choices[0].message.content
            model_used = getattr(response, 'model', None) or model_used
            logger.info(f"Successfully generated summary using model: {model_used}")

        except Exception as e:
            logger.exception(f"Error generating LLM summary with model '{model_used}'")
            summary_error = f"{type(e).__name__}: {e}"[:300]
            summary_text = build_fallback_summary(key_topics, stats, days)
            model_used = None          # the text below is the statistical fallback, not an LLM answer
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

    # Truncation: a fetch cap below what the period holds, or the model context
    capped = [f"{n} {kind}" for n, cap, total, kind in (
        (fetch_tweets, fetch_tweets, total_tweets_available, 'tweets'),
        (fetch_articles, fetch_articles, total_articles_available, 'articles'),
        (fetch_papers, fetch_papers, total_papers_available, 'papers')) if total > cap]
    sampled = len(prompt_tweets) < len(tweets)
    data_truncated = bool(capped) or sampled
    truncation_warning = None
    if capped:
        truncation_warning = (f"Loaded at most {', '.join(capped)} (your Data Limits). Available in this period: "
                              f"{total_tweets_available} tweets, {total_articles_available} articles, "
                              f"{total_papers_available} papers.")
    if sampled:
        truncation_warning = ((truncation_warning + ' ') if truncation_warning else '') + (
            f"{len(tweets)} tweets exceed the context of {context['model']} "
            f"({context['max_input_tokens'] // 1000}k tokens); an evenly spaced sample of "
            f"{len(prompt_tweets)} tweets covering the whole period went into the prompt.")

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
        "summary_error": summary_error,
        "data_truncated": data_truncated,
        "truncation_warning": truncation_warning,
        "limits_used": {
            "max_tweets": max_tweets,          # None = automatic (fits the model)
            "max_articles": max_articles,
            "max_papers": max_papers,
            "context_model": context['model'],
            "context_tokens": context['max_input_tokens'],
            "tweets_in_prompt": len(prompt_tweets),
        },
        "detail_level": detail_level,
        "diagnostic": diagnostic
    }


@router.get("/at-a-glance")
def get_trends_at_a_glance(
    hours: int = Query(48, ge=24, le=168, description="Time window in hours (whole days)"),
    anomaly_threshold: float = Query(2.5, ge=1.0, le=5.0, description="Z-score threshold for day-level spikes"),
    limit: int = Query(10, ge=5, le=25, description="Max items per category")
):
    """
    Hot / declining / stable concepts and spikes for the last `hours`, each
    judged against the concept's own baseline (median of the 8 preceding
    windows, volume-normalised, Poisson z-score with minimum counts).
    """
    from app.services import trend_core
    return trend_core.overview(hours=hours, anomaly_threshold=anomaly_threshold, limit=limit)
