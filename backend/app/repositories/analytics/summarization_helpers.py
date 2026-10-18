"""
Summarization prompt building helper functions for analytics.
"""

from typing import Dict, List, Any
from collections import Counter
from datetime import datetime


# Detail level configurations
DETAIL_LEVEL_CONFIG = {
    'brief': {
        'tweet_limit': 5, 'article_limit': 3, 'paper_limit': 3,
        'tweet_chars': 150, 'include_extras': False, 'sample_size': 10,
    },
    'standard': {
        'tweet_limit': 10, 'article_limit': 5, 'paper_limit': 5,
        'tweet_chars': 200, 'include_extras': False, 'sample_size': 20,
    },
    'detailed': {
        'tweet_limit': 25, 'article_limit': 10, 'paper_limit': 10,
        'tweet_chars': 400, 'include_extras': True, 'sample_size': 40,
    },
    'executive': {
        'tweet_limit': 40, 'article_limit': 15, 'paper_limit': 15,
        'tweet_chars': 500, 'include_extras': True, 'sample_size': 60,
    },
}


def collect_key_topics(
    db,
    tweets: List[Dict],
    sample_size: int = 20,
    detail_level: str = 'standard',
    full_content: bool = False,
) -> Counter:
    """
    Collect key topics from tweet samples.

    Args:
        db: MongoDB database instance
        tweets: List of tweet documents
        sample_size: Number of tweets to sample
        detail_level: Detail level for scaling sample size
        full_content: If True, scan ALL loaded tweets for topics.

    Returns:
        Counter of topic display names
    """
    config = DETAIL_LEVEL_CONFIG.get(detail_level, DETAIL_LEVEL_CONFIG['standard'])
    effective_sample = (
        len(tweets)
        if full_content
        else (config['sample_size'] if detail_level != 'standard' else sample_size)
    )

    key_topics = Counter()
    ids = [str(t['_id']) for t in tweets[:effective_sample]]
    if not ids:
        return key_topics
    per_concept = {row['_id']: row['n'] for row in db.tag_instances.aggregate([      # one query, not two per tag
        {'$match': {'content_type': 'tweet', 'content_id': {'$in': ids}, 'concept_id': {'$nin': [None, '']}}},
        {'$group': {'_id': '$concept_id', 'n': {'$sum': 1}}}])}
    for concept in db.tag_concepts_v2.find({'_id': {'$in': list(per_concept)}}, {'display_name': 1}):
        key_topics[concept.get('display_name')] += per_concept[concept['_id']]

    return key_topics


CHARS_PER_TOKEN = 3.5          # conservative for English tweets/abstracts


def fit_to_token_budget(tweets: List[Dict], articles: List[Dict], papers: List[Dict],
                        token_budget: int) -> List[Dict]:
    """Tweets that fit the prompt next to all articles and papers (full-content
    entries as prepare_content_sample(full_content=True) writes them). When not
    all fit, an evenly spaced sample keeps the whole period covered."""
    budget = int(token_budget * CHARS_PER_TOKEN)
    budget -= sum(len(a.get('title') or '') + 320 for a in articles)
    budget -= sum(len(p.get('title') or '') + 420 for p in papers)
    sizes = [min(len(t.get('text') or ''), 500) + 40 for t in tweets]   # + date/author prefix
    if sum(sizes) <= budget:
        return tweets
    if budget <= 0 or not tweets:
        return []
    keep = max(1, int(len(tweets) * budget / sum(sizes)))
    step = len(tweets) / keep
    return [tweets[int(i * step)] for i in range(keep)]


def prepare_content_sample(
    tweets: List[Dict],
    articles: List[Dict],
    papers: List[Dict],
    detail_level: str = 'standard',
    full_content: bool = False,
) -> List[str]:
    """
    Prepare content samples for summarization prompt.

    Args:
        tweets: List of tweet documents
        articles: List of article documents
        papers: List of paper documents
        detail_level: Controls sample size and content depth
        full_content: If True, include ALL loaded items (no per-detail slicing)
            and use the full tweet text. The detail_level still controls the
            *prompt structure* (headers, target length) via _get_task_instructions.

    Returns:
        List of content description strings
    """
    config = DETAIL_LEVEL_CONFIG.get(detail_level, DETAIL_LEVEL_CONFIG['standard'])

    if full_content:
        # Use everything the caller already loaded — the API's max_tweets caps
        # the upstream fetch, so the caller controls the volume.
        t_slice = tweets
        a_slice = articles
        p_slice = papers
        # 500 covers any tweet (max 280 chars, retweets can balloon with full_text).
        tweet_chars = 500
        # When asked for full content, always include article summaries/abstracts.
        include_extras = True
    else:
        t_slice = tweets[: config['tweet_limit']]
        a_slice = articles[: config['article_limit']]
        p_slice = papers[: config['paper_limit']]
        tweet_chars = config['tweet_chars']
        include_extras = config['include_extras']

    # Sort tweets oldest → newest so the LLM sees the timeline progress.
    # Fetch usually returns reverse-chronological; flip it for prompt order.
    t_slice = sorted(t_slice, key=lambda t: t.get('created_at') or '')

    content_sample = []

    for tweet in t_slice:
        text = tweet.get('text', '')[:tweet_chars]
        username = tweet.get('author_username', 'unknown')
        # Prefix with date for timeline context.
        created = tweet.get('created_at')
        date_prefix = created.strftime('[%Y-%m-%d] ') if isinstance(created, datetime) else ''
        # Mark retweets so the LLM doesn't misattribute the content to the column author.
        rt_marker = ' (retweet)' if text.startswith('RT @') else ''
        content_sample.append(f"{date_prefix}@{username}{rt_marker}: {text}")

    for article in a_slice:
        entry = f"Article: {article.get('title', 'Untitled')}"
        if include_extras:
            summary = article.get('summary') or article.get('preview') or ''
            if summary:
                entry += f"\n  Summary: {summary[:300]}"
        content_sample.append(entry)

    for paper in p_slice:
        entry = f"Paper: {paper.get('title', 'Untitled')}"
        if include_extras:
            abstract = paper.get('abstract') or ''
            if abstract:
                entry += f"\n  Abstract: {abstract[:400]}"
        content_sample.append(entry)

    return content_sample


def build_summarization_prompt(
    content_sample: List[str],
    key_topics: Counter,
    stats: Dict[str, Any],
    date_range_str: str,
    days: int,
    prompt: Dict[str, Any],
    detail_level: str = 'standard',
    full_content: bool = False,
    author: str | None = None,
) -> str:
    """
    Build the summarization prompt from the texts in prompts_config.json
    (key trend_summarization, passed in as `prompt` by the caller).

    full_content: do not cap the content list (else the first 15 lines).
    author: single-author filter (Twitter username, no @) — frames the summary
        around that person instead of "the AI/ML community".
    """
    sample = content_sample if full_content else content_sample[:15]
    tweet_count = stats.get('tweet_count', 0)
    if author:
        opener = prompt['opener_author'].format(author=author, date_range=date_range_str, days=days)
        tweets_header = f"### Tweets by @{author} ({tweet_count} total, chronological)"
    else:
        opener = prompt['opener_general'].format(date_range=date_range_str, days=days)
        tweets_header = f"### Tweets ({tweet_count} total, chronological)"
    # Key topics only when the raw tweets are too many to read: the block biases
    # the model toward the concept taxonomy instead of what the tweets emphasise
    topics_block = ""
    if tweet_count > 100 and key_topics:
        topics_block = ("\n### Key Topics (by frequency, for context only)\n"
                        + ', '.join(f"**{t}** ({c})" for t, c in key_topics.most_common(10)) + "\n")
    # likes are not always populated by the collector: only show non-zero engagement
    parts = [f"{stats.get(k, 0):,} {label}" for k, label in (('total_likes', 'likes'), ('total_retweets', 'retweets'))
             if stats.get(k, 0) > 0]
    engagement_line = f"- Total engagement: {', '.join(parts)}\n" if parts else ""
    tasks = prompt['tasks']
    return prompt['frame'].format(
        opener=opener, tweets_header=tweets_header, content='\n'.join(sample), topics_block=topics_block,
        tweet_count=tweet_count, article_count=stats.get('article_count', 0),
        paper_count=stats.get('paper_count', 0), unique_authors=stats.get('unique_authors', 0),
        engagement_line=engagement_line, task=tasks.get(detail_level, tasks['standard']))


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
