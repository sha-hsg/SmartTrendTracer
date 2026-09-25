"""
MongoDB-based Substack API - compatible with full MongoDB system
"""

from fastapi import APIRouter, HTTPException, Query
from app.database.mongodb import get_database
from app.services.analytics import (
    count_tags_for_content, calculate_tag_velocity, determine_trend,
    get_previous_period_range,
)
from typing import Dict, Any
from datetime import datetime, timezone, timedelta
import logging
from collections import Counter, defaultdict
import re
from app.repositories import substack as repo
from app.repositories import substack_queries as queries

logger = logging.getLogger(__name__)
router = APIRouter()

# MongoDB connection
db = get_database()

# Common English words filtered out during simple topic extraction
STOP_WORDS = {'that', 'with', 'have', 'this', 'will', 'from', 'they', 'been', 'said', 'each', 'which', 'their', 'time', 'about', 'would', 'there', 'could', 'other', 'after', 'first', 'well', 'also', 'into', 'over', 'think', 'just', 'only', 'more', 'than', 'some', 'what', 'know', 'year', 'much', 'take', 'make', 'way', 'come', 'when', 'work', 'life', 'world', 'people', 'state', 'part', 'right', 'system', 'never'}


def _as_utc(dt) -> datetime:
    """Return a tz-aware UTC datetime; naive values are assumed to be UTC."""
    if dt is None:
        return datetime.min.replace(tzinfo=timezone.utc)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

@router.get("/trends")
async def get_substack_trends(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze")
) -> Dict[str, Any]:
    """
    Get Substack article trends for specified time period
    """
    try:
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # Get articles from MongoDB within the date range
        articles_cursor = queries.articles_find__get_substack_trends(start_date, end_date)
        articles = list(articles_cursor)
        
        if not articles:
            return {
                "status": "No articles found",
                "period": f"{days} days",
                "total_articles": 0,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "topic_trends": {"top_topics": [], "trending_up": []},
                "author_trends": {"most_active": [], "total_authors": 0, "avg_articles_per_author": 0},
                "tag_trends": {"top_tags": [], "tag_relationships": [], "unique_tags": 0},
                "snippet_insights": {"categories": {}, "important_highlights": [], "total_snippets": 0},
                "velocity_trends": []
            }
        
        # Analyze articles
        total_articles = len(articles)
        logger.info(f"Analyzing {total_articles} articles from last {days} days")
        
        # Extract topics from titles and summaries
        all_text = []
        for article in articles:
            if article.get('title'):
                all_text.append(article['title'].lower())
            if article.get('summary'):
                all_text.append(article['summary'].lower())
        
        # Simple topic extraction (keywords)
        topic_counter = Counter()
        for text in all_text:
            # Extract meaningful words (basic NLP)
            words = re.findall(r'\b[a-zA-Z]{4,}\b', text)
            # Filter out common words
            meaningful_words = [word for word in words if word not in STOP_WORDS and len(word) > 3]
            topic_counter.update(meaningful_words)
        
        top_topics = [{"term": term, "score": count, "articles": count} for term, count in topic_counter.most_common(10)]
        
        # Author analysis
        author_stats = defaultdict(lambda: {"articles": 0, "total_words": 0, "snippets": 0, "topics": set()})
        for article in articles:
            author = article.get('author', 'Unknown')
            author_stats[author]["articles"] += 1
            
            # Use the stored word_count; fall back to counting the markdown
            # (the old code read 'content', which does not exist — the field
            # is 'content_markdown' — so it always fell back to the summary)
            estimated_words = article.get('word_count') or len(
                (article.get('content_markdown') or article.get('summary') or '').split())
            author_stats[author]["total_words"] += estimated_words
            
            # Add topics for this author
            if article.get('title'):
                words = re.findall(r'\b[a-zA-Z]{4,}\b', article['title'].lower())
                author_stats[author]["topics"].update([w for w in words if w not in STOP_WORDS])
        
        most_active_authors = []
        for author, stats in sorted(author_stats.items(), key=lambda x: x[1]["articles"], reverse=True)[:10]:
            avg_words = stats["total_words"] / max(stats["articles"], 1)
            avg_reading_time = avg_words / 200 if avg_words > 0 else 0  # Assume 200 words per minute
            
            productivity = "High" if stats["articles"] >= 5 else "Medium" if stats["articles"] >= 2 else "Low"
            
            most_active_authors.append({
                "author": author,
                "articles": stats["articles"],
                "avg_words": int(avg_words),
                "avg_reading_time": round(avg_reading_time, 1),
                "total_snippets": stats["snippets"],
                "topics": list(stats["topics"])[:5],  # Top 5 topics
                "productivity": productivity
            })
        
        # Tag analysis from tag_instances/concepts — the articles collection
        # has no 'tags' field, so the old loop always produced an empty list
        from app.services.concept_only_tag_service import ConceptOnlyTagService
        concept_service = ConceptOnlyTagService()

        current_counts_raw = count_tags_for_content(db, articles, 'article', date_field='published_at')
        current_counts = Counter()
        for cid, cnt in current_counts_raw.items():
            current_counts[str(cid)] += cnt

        prev_start, prev_end = get_previous_period_range(start_date, days)
        previous_articles = list(queries.articles_find__get_substack_trends_2(prev_start, prev_end))
        previous_counts_raw = count_tags_for_content(db, previous_articles, 'article', date_field='published_at')
        previous_counts = Counter()
        for cid, cnt in previous_counts_raw.items():
            previous_counts[str(cid)] += cnt

        concept_map = concept_service.get_concepts_by_ids(
            list(set(current_counts) | set(previous_counts)))

        def _name(cid: str) -> str:
            return concept_map.get(cid, {}).get('display_name', cid)

        top_tags = [
            {"tag": _name(cid), "count": count}
            for cid, count in current_counts.most_common(10)
        ]

        # Real trending-up: growth vs the immediately preceding equal period
        # (the old value was literally top_topics[:5]; the UI rendered
        # "+undefined articles")
        trending_up = sorted(
            (
                {
                    "term": _name(cid),
                    "growth": count - previous_counts.get(cid, 0),
                    "current_count": count,
                }
                for cid, count in current_counts.items()
                if count - previous_counts.get(cid, 0) > 0
            ),
            key=lambda t: (t["growth"], t["current_count"]),
            reverse=True,
        )[:5]

        # Per-topic velocity in the shape the Velocity tab renders
        # ({topic, velocity, first_period, second_period, trend}); the old
        # per-day counts produced 30 blank rows in the UI
        velocity_trends = []
        for cid, count in current_counts.most_common(15):
            previous = previous_counts.get(cid, 0)
            velocity = calculate_tag_velocity(count, previous)
            trend = determine_trend(velocity)
            velocity_trends.append({
                "topic": _name(cid),
                "velocity": round(velocity, 1),
                "first_period": previous,
                "second_period": count,
                "trend": "falling" if trend == "declining" else trend,
            })

        # Emerging themes: concepts absent in the previous period
        emerging_themes = [
            {
                "theme": _name(cid),
                "type": "new" if previous_counts.get(cid, 0) == 0 else "growing",
                "occurrences": count,
                "growth": f"+{count - previous_counts.get(cid, 0)}",
            }
            for cid, count in current_counts.most_common(50)
            if count >= 2 and count > 2 * max(previous_counts.get(cid, 0), 0)
        ][:8]

        # Tag relationships from the existing co-occurrence service
        tag_relationships = []
        try:
            from app.services.anomaly_detection import get_concept_cooccurrence
            cooc = get_concept_cooccurrence(db, days=days, min_cooccurrence=2, top_n=25)
            related_by_tag = defaultdict(list)
            for pair in cooc.get('pairs', []):
                related_by_tag[pair['concept_a']].append(
                    {"tag": pair['concept_b'], "strength": pair['strength']})
                related_by_tag[pair['concept_b']].append(
                    {"tag": pair['concept_a'], "strength": pair['strength']})
            tag_relationships = [
                {"tag": tag, "related": sorted(rel, key=lambda r: r['strength'], reverse=True)[:6]}
                for tag, rel in sorted(related_by_tag.items(),
                                       key=lambda kv: len(kv[1]), reverse=True)[:10]
            ]
        except Exception as cooc_err:
            logger.warning(f"Co-occurrence for substack trends failed: {cooc_err}")
        
        return {
            "period": f"{days} days",
            "total_articles": total_articles,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "topic_trends": {
                "top_topics": top_topics,
                "trending_up": trending_up
            },
            "author_trends": {
                "most_active": most_active_authors,
                "total_authors": len(author_stats),
                "avg_articles_per_author": round(total_articles / max(len(author_stats), 1), 1)
            },
            "tag_trends": {
                "top_tags": top_tags,
                "tag_relationships": tag_relationships,
                "unique_tags": len(current_counts)
            },
            # PARTIAL STUB: snippet analysis not implemented; kept empty because
            # the frontend (SubstackTrendsModern.tsx) reads snippet_insights.
            "snippet_insights": {
                "categories": {},
                "important_highlights": [],
                "total_snippets": 0
            },
            "velocity_trends": velocity_trends,
            "emerging_themes": emerging_themes
        }
        
    except Exception as e:
        logger.error(f"Error analyzing Substack trends: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze trends: {str(e)}")

@router.get("/health")
async def substack_health():
    """Health check for Substack API"""
    return repo.substack_health()
