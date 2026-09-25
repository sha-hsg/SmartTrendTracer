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

    for tweet in tweets[:effective_sample]:
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


def _get_task_instructions(detail_level: str) -> str:
    """Return level-specific task instructions for the LLM prompt."""
    if detail_level == 'brief':
        return """## Your Task

Provide a concise 2-3 paragraph summary of the most important highlights. No section headers needed. Under 300 words. Focus on the single most impactful developments and key takeaways."""

    if detail_level == 'detailed':
        return """## Your Task

Please provide a thorough and substantive summary including:

### 1. Executive Summary
A 3-4 sentence overview of the main themes, trends, and notable developments.

### 2. Key Insights
- What are the most important developments or announcements?
- What topics are generating the most discussion?
- Are there any emerging trends or shifts in focus?

### 3. Notable Highlights
- Significant product launches, research breakthroughs, or industry news
- Influential voices or perspectives that stood out
- Controversial or debated topics

### 4. Engagement Analysis
Analysis of what content resonated most with the audience based on engagement metrics.

### 5. Emerging Trends & Patterns
- Cross-cutting themes that appear across multiple sources
- Connections between different developments
- Early signals of upcoming shifts in the field

### 6. Deep Dive: Notable Content
Highlight 3-5 specific pieces of content (tweets, articles, or papers) that are particularly noteworthy. Include direct quotes or specific data points where available.

Be thorough and substantive. Include specific quotes, data points, and concrete examples. Target 1000-1500 words."""

    if detail_level == 'executive':
        return """## Your Task

Produce a comprehensive executive report including:

### 1. Executive Summary
A 4-5 sentence high-level overview of the most significant themes and developments.

### 2. Key Insights & Developments
- Major announcements, product launches, and breakthroughs
- Topics generating the most discussion and why
- Emerging trends and shifts in focus

### 3. Notable Highlights
- Significant research breakthroughs and industry news
- Influential voices and standout perspectives
- Controversial or heavily debated topics

### 4. Engagement Analysis
Detailed analysis of what content resonated most with the audience, with specific metrics and examples.

### 5. Cross-Source Analysis
- How do discussions on Twitter compare to article and paper coverage?
- Are there topics covered in research that haven't reached social media yet (or vice versa)?
- Identify gaps between academic and public discourse

### 6. Sentiment & Reception
- Overall sentiment around key topics
- Community reactions to major announcements
- Areas of consensus vs. disagreement

### 7. Recommendations & Outlook
- What should readers pay attention to in the coming weeks?
- Which emerging topics are likely to grow in importance?
- Strategic implications for practitioners and researchers

### 8. Key Sources Appendix
List the 5-10 most important individual sources (tweets, articles, papers) with brief descriptions of why they matter.

Be exhaustive and analytical. Include specific quotes, data points, statistics, and concrete examples throughout. Target 2000+ words."""

    # standard (default)
    return """## Your Task

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


def build_summarization_prompt(
    content_sample: List[str],
    key_topics: Counter,
    stats: Dict[str, Any],
    date_range_str: str,
    days: int,
    detail_level: str = 'standard',
    full_content: bool = False,
    author: str | None = None,
) -> str:
    """
    Build the summarization prompt for LLM.

    Args:
        content_sample: List of content descriptions
        key_topics: Counter of key topics
        stats: Statistics dict
        date_range_str: Human-readable date range
        days: Number of days
        detail_level: Controls prompt complexity and output length
        full_content: If True, do not cap the content list inside the prompt.
        author: Single-author filter (Twitter username, no @). When set, the
            prompt frames the summary around that person instead of "the AI/ML
            community".

    Returns:
        Formatted prompt string
    """
    task_instructions = _get_task_instructions(detail_level)
    # Hard cap of 15 lines is the historical brief default; bypass when caller
    # asked for full content.
    sample_for_prompt = content_sample if full_content else content_sample[:15]
    tweet_count = stats.get('tweet_count', 0)
    total_likes = stats.get('total_likes', 0)
    total_retweets = stats.get('total_retweets', 0)

    # 1) Author-aware framing.
    if author:
        opener = (
            f"You are an analyst summarizing one person's activity. Below are "
            f"@{author}'s tweets {date_range_str} (the past {days} day(s)). "
            f"Frame the summary around @{author} as an individual — what they "
            f"posted about, what shifted, what stands out — not 'the community'."
        )
        tweets_header = f"### Tweets by @{author} ({tweet_count} total, chronological)"
    else:
        opener = (
            f"You are an AI research analyst. Analyze the following AI/ML content "
            f"{date_range_str} (the past {days} day(s)) and provide a comprehensive summary."
        )
        tweets_header = f"### Tweets ({tweet_count} total, chronological)"

    # 3) Skip the Key Topics block when the LLM has the raw tweets in plain sight
    #    anyway. The block can bias the model toward our concept taxonomy
    #    instead of what the tweets actually emphasize.
    topics_block = ""
    if tweet_count > 100 and key_topics:
        topics_block = (
            "\n### Key Topics (by frequency, for context only)\n"
            + ', '.join(f"**{topic}** ({count})" for topic, count in key_topics.most_common(10))
            + "\n"
        )

    # 2) Likes data is unreliable (collector doesn't always populate); only show
    #    when non-zero. Retweets are populated for retweeted tweets, so it's
    #    safer — but still skip if zero to avoid noise.
    engagement_parts = []
    if total_likes > 0:
        engagement_parts.append(f"{total_likes:,} likes")
    if total_retweets > 0:
        engagement_parts.append(f"{total_retweets:,} retweets")
    engagement_line = (
        f"- Total engagement: {', '.join(engagement_parts)}\n"
        if engagement_parts else ""
    )

    return f"""{opener}

## Content to Analyze

{tweets_header}
{chr(10).join(sample_for_prompt)}
{topics_block}
### Statistics
- Total tweets analyzed: {tweet_count}
- Total articles analyzed: {stats.get('article_count', 0)}
- Total papers analyzed: {stats.get('paper_count', 0)}
- Unique authors: {stats.get('unique_authors', 0)}
{engagement_line}
{task_instructions}"""


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
