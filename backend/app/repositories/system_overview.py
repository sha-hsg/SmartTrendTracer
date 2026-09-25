"""
Data access for app.api.system_stats.overview_and_content (extracted by the arch-audit refactor).

Overview, content, and author statistics endpoints.
High-level system overview, detailed content stats, author analytics.
"""
from app.repositories.cache import get_cached as _get_cached
from app.repositories.errors import DataAccessError
from collections import defaultdict
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any
from pymongo import DESCENDING
from typing import Dict
import logging

from app.database.mongodb import get_database

db = get_database()

logger = logging.getLogger(__name__)


async def get_system_overview():
    """High-level system overview statistics (used internally by /statistics/summary)"""
    try:
        def _compute() -> Dict[str, Any]:
            stats = {
                "total_tweets": db.tweets.count_documents({}),
                "total_articles": db.articles.count_documents({}),
                "total_papers": db.papers.count_documents({}),
                "unique_twitter_authors": len(db.tweets.distinct("author_username")),
                "unique_substack_authors": db.substack_authors.count_documents({}),
                "unique_paper_authors": len({
                    author for paper in db.papers.find({}, {"authors": 1})
                    for author in paper.get("authors", [])
                }),
                "total_concepts": db.tag_concepts_v2.count_documents({}),
                "total_aliases": db.tag_aliases_v2.count_documents({}),
                "total_tag_instances": db.tag_instances.count_documents({}),
                "database_collections": len(db.list_collection_names()),
                "last_tweet_collected": None,
                "last_article_collected": None,
                "system_uptime_days": None,
            }

            last_tweet = db.tweets.find_one({}, sort=[("collected_at", DESCENDING)])
            if last_tweet:
                stats["last_tweet_collected"] = last_tweet.get("collected_at")

            last_article = db.articles.find_one({}, sort=[("created_at", DESCENDING)])
            if last_article:
                stats["last_article_collected"] = last_article.get("created_at")

            return stats

        return _get_cached("system_overview", _compute)

    except Exception as e:
        logger.error(f"Error getting system overview: {e}")
        raise DataAccessError(str(e))


def get_content_statistics():
    """Get detailed content statistics across all sources"""
    try:
        def _compute() -> Dict[str, Any]:
            tweet_stats = {
                "total": db.tweets.count_documents({}),
                "with_media": db.tweets.count_documents({"media_count": {"$gt": 0}}),
                "with_urls": db.tweets.count_documents({"urls": {"$ne": []}}),
                "retweets": db.tweets.count_documents({"referenced_tweets": {"$elemMatch": {"type": "retweeted"}}}),
                "quotes": db.tweets.count_documents({"referenced_tweets": {"$elemMatch": {"type": "quoted"}}}),
                "replies": db.tweets.count_documents({"referenced_tweets": {"$elemMatch": {"type": "replied_to"}}}),
                "processed": db.tweets.count_documents({"processed": True}),
                "tagged": db.tweets.count_documents({"concept_ids": {"$ne": []}}),
            }

            article_stats = {
                "total": db.articles.count_documents({}),
                "with_summaries": db.articles.count_documents({"summary": {"$exists": True, "$ne": ""}}),
                "with_snippets": db.articles.count_documents({"snippets": {"$exists": True, "$ne": []}}),
                # Articles have no 'tags' field - count distinct tagged articles via tag_instances
                "with_tags": len(db.tag_instances.distinct("content_id", {"content_type": "article"})),
                "forwarded": db.articles.count_documents({"forwarded": True}),
                "direct_subscriptions": db.articles.count_documents({"forwarded": {"$ne": True}}),
            }

            paper_stats = {
                "total": db.papers.count_documents({}),
                "with_pdf": db.papers.count_documents({"pdf_path": {"$exists": True, "$ne": None}}),
                "with_markdown": db.papers.count_documents({"markdown_content": {"$exists": True, "$ne": ""}}),
                "with_grobid": db.papers.count_documents({"grobid_processed": True}),
                # Papers store the processor in 'processor_used' (marker_service/mineru_service/...)
                "with_marker": db.papers.count_documents({"processor_used": "marker_service"}),
                "with_mineru": db.papers.count_documents({"processor_used": "mineru_service"}),
                "with_tags": db.papers.count_documents({"tags": {"$exists": True, "$ne": []}}),
                "with_snippets": db.papers.count_documents({"snippets": {"$exists": True, "$ne": []}}),
                "from_arxiv": db.papers.count_documents({"arxiv_id": {"$exists": True, "$ne": None}}),
            }

            media_stats = {
                "total_tweet_media": db.tweets.aggregate([
                    {"$group": {"_id": None, "total": {"$sum": "$media_count"}}}
                ]).next().get("total", 0) if db.tweets.count_documents({}) > 0 else 0,
                "tweet_photos": db.tweets.count_documents({"media": {"$elemMatch": {"type": "photo"}}}),
                "tweet_videos": db.tweets.count_documents({"media": {"$elemMatch": {"type": "video"}}}),
                "tweet_gifs": db.tweets.count_documents({"media": {"$elemMatch": {"type": "animated_gif"}}}),
                "article_images": db.articles.count_documents({"images": {"$exists": True, "$ne": []}}),
            }

            total_snippets = 0
            for result in db.articles.aggregate([
                {"$project": {"snippet_count": {"$size": {"$ifNull": ["$snippets", []]}}}},
                {"$group": {"_id": None, "total": {"$sum": "$snippet_count"}}}
            ]):
                total_snippets += result.get("total", 0)

            for result in db.papers.aggregate([
                {"$project": {"snippet_count": {"$size": {"$ifNull": ["$snippets", []]}}}},
                {"$group": {"_id": None, "total": {"$sum": "$snippet_count"}}}
            ]):
                total_snippets += result.get("total", 0)

            return {
                "tweets": tweet_stats,
                "articles": article_stats,
                "papers": paper_stats,
                "media": media_stats,
                "total_snippets": total_snippets,
            }

        return _get_cached("content_stats", _compute)

    except Exception as e:
        logger.error(f"Error getting content statistics: {e}")
        raise DataAccessError(str(e))



def get_author_statistics():
    """Get detailed author and contributor statistics"""
    try:
        def _compute() -> Dict[str, Any]:
            # Get Twitter authors with latest tweet date
            top_twitter_raw = list(db.tweets.aggregate([
                {"$group": {
                    "_id": "$author_username",
                    "count": {"$sum": 1},
                    "latest": {"$max": "$created_at"}
                }},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]))
            # Transform to frontend expected format
            top_twitter = [
                {
                    "username": t["_id"],
                    "tweet_count": t["count"],
                    "latest_tweet": t.get("latest").isoformat() if t.get("latest") else None
                }
                for t in top_twitter_raw
            ]

            # Get article authors with latest article date
            top_substack_raw = list(db.articles.aggregate([
                {"$group": {
                    "_id": "$author",
                    "count": {"$sum": 1},
                    "latest": {"$max": "$created_at"}
                }},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]))
            # Transform to frontend expected format
            top_substack = [
                {
                    "name": a["_id"] or "Unknown",
                    "article_count": a["count"],
                    "latest_article": a.get("latest").isoformat() if a.get("latest") else None
                }
                for a in top_substack_raw
            ]

            paper_authors = defaultdict(int)
            for paper in db.papers.find({}, {"authors": 1}):
                for author in paper.get("authors", []):
                    author_name = author.get("name") if isinstance(author, dict) else str(author)
                    paper_authors[author_name or "Unknown"] += 1

            top_paper_authors = sorted(
                [{"_id": k, "count": v} for k, v in paper_authors.items()],
                key=lambda x: x["count"],
                reverse=True
            )[:10]

            now = datetime.now(timezone.utc)
            week_ago = now - timedelta(days=7)
            month_ago = now - timedelta(days=30)

            activity = {
                "tweets_last_week": db.tweets.count_documents({"created_at": {"$gte": week_ago}}),
                "tweets_last_month": db.tweets.count_documents({"created_at": {"$gte": month_ago}}),
                "articles_last_week": db.articles.count_documents({"created_at": {"$gte": week_ago}}),
                "articles_last_month": db.articles.count_documents({"created_at": {"$gte": month_ago}}),
                "papers_last_week": db.papers.count_documents({"created_at": {"$gte": week_ago}}),
                "papers_last_month": db.papers.count_documents({"created_at": {"$gte": month_ago}}),
            }

            return {
                "twitter_authors": top_twitter,  # Renamed from top_twitter_authors
                "article_authors": top_substack,  # Renamed from top_substack_authors
                "top_paper_authors": top_paper_authors,
                "activity": activity,
                "total_unique_contributors": (
                    len(db.tweets.distinct("author_username"))
                    + len(db.articles.distinct("author"))
                    + len(set(paper_authors.keys()))
                ),
            }

        return _get_cached("author_stats", _compute)

    except Exception as e:
        logger.error(f"Error getting author statistics: {e}")
        raise DataAccessError(str(e))

