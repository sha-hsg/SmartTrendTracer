"""
MongoDB-based Substack API - compatible with full MongoDB system
"""

from fastapi import APIRouter, HTTPException, Query
from app.database.mongodb import get_database
from typing import Dict, Any
from datetime import datetime, timezone, timedelta
import logging
from collections import Counter, defaultdict
import re

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
        articles_cursor = db.articles.find({
            "published_at": {
                "$gte": start_date,
                "$lte": end_date
            }
        })
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
            
            # Estimate word count from content length
            content = article.get('content', '') or article.get('summary', '') or ''
            estimated_words = len(content.split()) if content else 0
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
        
        # Tag analysis
        all_tags = []
        for article in articles:
            tags = article.get('tags', [])
            if isinstance(tags, list):
                for tag in tags:
                    if isinstance(tag, str):
                        all_tags.append(tag)
                    elif isinstance(tag, dict) and 'tag' in tag:
                        all_tags.append(tag['tag'])
        
        tag_counter = Counter(all_tags)
        top_tags = [{"tag": tag, "count": count} for tag, count in tag_counter.most_common(10)]
        
        # Velocity trends (articles per day)
        velocity_trends = []
        for i in range(min(days, 30)):  # Last 30 days max for visualization
            day = start_date + timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            day_articles = [a for a in articles if day_start <= _as_utc(a.get('published_at')) < day_end]
            
            velocity_trends.append({
                "date": day.strftime("%Y-%m-%d"),
                "articles": len(day_articles),
                "total_words": sum(len((a.get('content') or a.get('summary') or '').split()) for a in day_articles)
            })
        
        return {
            "period": f"{days} days",
            "total_articles": total_articles,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "topic_trends": {
                "top_topics": top_topics,
                "trending_up": top_topics[:5]  # Simple trending up = top topics
            },
            "author_trends": {
                "most_active": most_active_authors,
                "total_authors": len(author_stats),
                "avg_articles_per_author": round(total_articles / max(len(author_stats), 1), 1)
            },
            "tag_trends": {
                "top_tags": top_tags,
                # PARTIAL STUB: co-occurrence analysis not implemented; kept empty
                # because the frontend (substack-trends/TabPanels.tsx) reads this field.
                "tag_relationships": [],
                "unique_tags": len(set(all_tags))
            },
            # PARTIAL STUB: snippet analysis not implemented; kept empty because
            # the frontend (SubstackTrendsModern.tsx) reads snippet_insights.
            "snippet_insights": {
                "categories": {},
                "important_highlights": [],
                "total_snippets": 0
            },
            "velocity_trends": velocity_trends
        }
        
    except Exception as e:
        logger.error(f"Error analyzing Substack trends: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze trends: {str(e)}")

@router.get("/health")
async def substack_health():
    """Health check for Substack API"""
    try:
        article_count = db.articles.count_documents({})
        return {
            "status": "healthy",
            "articles_count": article_count,
            "database": "MongoDB"
        }
    except Exception as e:
        logger.error(f"Substack health check failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }
