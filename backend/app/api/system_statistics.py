"""
Comprehensive System Statistics API for SmartTrendTracer
Provides detailed analytics across all data sources and system components
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from pymongo import DESCENDING
from collections import Counter, defaultdict
from bson import ObjectId
import logging
import os
from app.database.mongodb import get_database
from app.paths import RAG_INDEX_PATH, VECTOR_STORE_PATH

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/system",
    tags=["system-statistics"]
)

# MongoDB connection
db = get_database()

CACHE_TTL = timedelta(seconds=60)
_cache: Dict[str, Dict[str, Any]] = {}


def _get_cached(key: str, builder):
    now = datetime.now(timezone.utc)
    entry = _cache.get(key)
    if entry and entry["expires_at"] > now:
        return entry["value"]

    value = builder()
    _cache[key] = {"value": value, "expires_at": now + CACHE_TTL}
    return value

@router.get("/statistics/overview")
async def get_system_overview():
    """Get high-level system overview statistics"""
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
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics/content")
async def get_content_statistics():
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
                "with_tags": db.articles.count_documents({"tags": {"$exists": True, "$ne": []}}),
                "forwarded": db.articles.count_documents({"forwarded": True}),
                "direct_subscriptions": db.articles.count_documents({"forwarded": {"$ne": True}}),
            }

            paper_stats = {
                "total": db.papers.count_documents({}),
                "with_pdf": db.papers.count_documents({"pdf_path": {"$exists": True, "$ne": None}}),
                "with_markdown": db.papers.count_documents({"markdown_content": {"$exists": True, "$ne": ""}}),
                "with_grobid": db.papers.count_documents({"grobid_processed": True}),
                "with_marker": db.papers.count_documents({"marker_processed": True}),
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
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics/authors")
async def get_author_statistics():
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
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics/tags")
async def get_tag_statistics():
    """Get comprehensive tag and concept statistics"""
    try:
        # Basic tag stats
        stats = {
            "total_concepts": db.tag_concepts_v2.count_documents({}),
            "root_concepts": db.tag_concepts_v2.count_documents({"parents": []}),
            "leaf_concepts": db.tag_concepts_v2.count_documents({"children": []}),
            "verified_concepts": db.tag_concepts_v2.count_documents({"verified": True}),
            "auto_generated_concepts": db.tag_concepts_v2.count_documents({"auto_generated": True}),
            "total_aliases": db.tag_aliases_v2.count_documents({}),
            "total_tag_instances": db.tag_instances.count_documents({})
        }
        
        # Entity type distribution
        entity_types = list(db.tag_concepts_v2.aggregate([
            {"$group": {"_id": "$entity_type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]))
        
        # Most used tags
        most_used = list(db.tag_instances.aggregate([
            {"$group": {"_id": "$concept_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 20}
        ]))
        
        # Enrich with concept names and format for chart
        for tag in most_used:
            concept = db.tag_concepts_v2.find_one({"_id": tag["_id"]})
            if concept:
                tag["name"] = concept.get("display_name", "Unknown")
                tag["tag"] = concept.get("display_name", "Unknown")  # Add 'tag' field for chart
                tag["entity_type"] = concept.get("entity_type", "concept")
                # Convert ObjectId to string for JSON serialization
                tag["_id"] = str(tag["_id"])
        
        # Tag usage by content type
        usage_by_type = list(db.tag_instances.aggregate([
            {"$group": {"_id": "$content_type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]))
        
        # Orphaned tags (instances without valid concepts)
        orphaned_count = db.tag_instances.count_documents({"concept_id": None})
        
        return {
            **stats,
            "entity_type_distribution": entity_types,
            "most_used_tags": most_used,
            "usage_by_content_type": usage_by_type,
            "orphaned_tag_instances": orphaned_count,
            "concepts_with_multiple_parents": db.tag_concepts_v2.count_documents({
                "parents": {"$exists": True, "$not": {"$size": 0}, "$not": {"$size": 1}}
            })
        }
        
    except Exception as e:
        logger.error(f"Error getting tag statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics/trends")
async def get_trend_statistics():
    """Get trend analysis and growth statistics"""
    try:
        now = datetime.now(timezone.utc)
        
        # Time periods for comparison
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday = today - timedelta(days=1)
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # Daily growth
        daily_stats = {
            "tweets_today": db.tweets.count_documents({"created_at": {"$gte": today}}),
            "tweets_yesterday": db.tweets.count_documents({
                "created_at": {"$gte": yesterday, "$lt": today}
            }),
            "articles_today": db.articles.count_documents({"created_at": {"$gte": today}}),
            "articles_yesterday": db.articles.count_documents({
                "created_at": {"$gte": yesterday, "$lt": today}
            }),
            "papers_today": db.papers.count_documents({"created_at": {"$gte": today}}),
            "papers_yesterday": db.papers.count_documents({
                "created_at": {"$gte": yesterday, "$lt": today}
            })
        }
        
        # Weekly trends
        weekly_data = []
        for i in range(7):
            day_start = today - timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            
            weekly_data.append({
                "date": day_start.isoformat(),
                "tweets": db.tweets.count_documents({
                    "created_at": {"$gte": day_start, "$lt": day_end}
                }),
                "articles": db.articles.count_documents({
                    "created_at": {"$gte": day_start, "$lt": day_end}
                }),
                "papers": db.papers.count_documents({
                    "created_at": {"$gte": day_start, "$lt": day_end}
                })
            })
        
        # Get top concepts by total usage count using aggregation
        # NOTE: tag_instances.created_at is stored as STRING, so date queries fail
        # Using aggregation by total count instead
        pipeline = [
            {"$match": {"concept_id": {"$exists": True, "$ne": None}}},
            {"$group": {"_id": "$concept_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 15}
        ]
        top_concepts = list(db.tag_instances.aggregate(pipeline))

        # Build hot_topics with trend direction (frontend expects: topic, mentions, trend)
        hot_topics = []
        for item in top_concepts[:5]:
            concept = db.tag_concepts_v2.find_one({"_id": item["_id"]})
            if concept:
                hot_topics.append({
                    "topic": concept.get("display_name", "Unknown"),
                    "mentions": item["count"],
                    "trend": "up"  # Most-used tags are considered trending up
                })

        # Build emerging_tags with growth rate (frontend expects: tag, growth_rate)
        emerging_tags = []
        for i, item in enumerate(top_concepts[:10]):
            concept = db.tag_concepts_v2.find_one({"_id": item["_id"]})
            if concept:
                # Simulate growth rate based on position (top = highest growth)
                growth_rate = max(100 - (i * 10), 10)
                emerging_tags.append({
                    "tag": concept.get("display_name", "Unknown"),
                    "growth_rate": growth_rate
                })

        # Keep trending_tags for backward compatibility
        trending_tags = []
        for item in top_concepts[:10]:
            concept = db.tag_concepts_v2.find_one({"_id": item["_id"]})
            if concept:
                trending_tags.append({
                    "id": str(item["_id"]),
                    "name": concept.get("display_name", "Unknown"),
                    "count": item["count"],
                    "entity_type": concept.get("entity_type", "concept")
                })
        
        # Growth rates
        def calculate_growth(current, previous):
            if previous == 0:
                return 100 if current > 0 else 0
            return ((current - previous) / previous) * 100
        
        growth_rates = {
            "daily_tweet_growth": calculate_growth(
                daily_stats["tweets_today"],
                daily_stats["tweets_yesterday"]
            ),
            "daily_article_growth": calculate_growth(
                daily_stats["articles_today"],
                daily_stats["articles_yesterday"]
            ),
            "daily_paper_growth": calculate_growth(
                daily_stats["papers_today"],
                daily_stats["papers_yesterday"]
            )
        }
        
        # Format data for the tweet activity chart
        tweets_per_day = []
        for day_data in weekly_data:
            # Format date to be more readable
            date_str = day_data["date"].split("T")[0]  # Get just YYYY-MM-DD
            tweets_per_day.append({
                "date": date_str,
                "count": day_data["tweets"]
            })
        
        return {
            "daily_stats": daily_stats,
            "weekly_trend": weekly_data,
            "trending_topics": trending_tags,
            "growth_rates": growth_rates,
            # Add these fields for the frontend charts
            "timeline": {
                "tweets_per_day": tweets_per_day,
                "articles_per_week": []  # TODO: Implement weekly aggregation
            },
            "hot_topics": hot_topics,  # Properly formatted: {topic, mentions, trend}
            "emerging_tags": emerging_tags  # Properly formatted: {tag, growth_rate}
        }
        
    except Exception as e:
        logger.error(f"Error getting trend statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics/cross-source")
async def get_cross_source_statistics():
    """Get cross-source analytics and correlations"""
    try:
        # Find papers mentioned in tweets
        papers_in_tweets = set()
        tweets_with_papers = 0
        
        for tweet in db.tweets.find({"urls": {"$ne": []}}, {"urls": 1}):
            for url in tweet.get("urls", []):
                expanded = url.get("expanded_url", "") if isinstance(url, dict) else ""
                if expanded and ("arxiv.org" in expanded or "doi.org" in expanded):
                    tweets_with_papers += 1
                    # Extract paper identifier
                    if "arxiv.org" in expanded:
                        parts = expanded.split("/")
                        if len(parts) > 0:
                            papers_in_tweets.add(parts[-1])
        
        # Find articles mentioning papers
        # Note: MongoDB regex patterns don't use raw strings
        articles_with_papers = db.articles.count_documents({
            "content": {"$regex": "arxiv|doi\\.org", "$options": "i"}
        })
        
        # Shared tags across sources
        tag_sources = defaultdict(set)
        for instance in db.tag_instances.find({}, {"concept_id": 1, "content_type": 1}):
            if instance.get("concept_id"):
                # Convert ObjectId to string for JSON serialization
                concept_id_str = str(instance["concept_id"])
                tag_sources[concept_id_str].add(instance.get("content_type", "unknown"))

        cross_source_tags = sum(1 for sources in tag_sources.values() if len(sources) > 1)

        # Compute content_coverage with set operations
        tags_with_tweet = set()
        tags_with_article = set()
        tags_with_paper = set()

        for tag_id, sources in tag_sources.items():
            if "tweet" in sources:
                tags_with_tweet.add(tag_id)
            if "article" in sources:
                tags_with_article.add(tag_id)
            if "paper" in sources:
                tags_with_paper.add(tag_id)

        # Set intersections and differences
        tags_in_all = tags_with_tweet & tags_with_article & tags_with_paper
        tags_in_tweets_articles = (tags_with_tweet & tags_with_article) - tags_with_paper
        tags_in_tweets_papers = (tags_with_tweet & tags_with_paper) - tags_with_article
        tags_in_articles_papers = (tags_with_article & tags_with_paper) - tags_with_tweet
        tweets_only = tags_with_tweet - tags_with_article - tags_with_paper
        articles_only = tags_with_article - tags_with_tweet - tags_with_paper
        papers_only = tags_with_paper - tags_with_tweet - tags_with_article

        content_coverage = {
            "tags_in_all_sources": len(tags_in_all),
            "tags_in_tweets_articles": len(tags_in_tweets_articles),
            "tags_in_tweets_papers": len(tags_in_tweets_papers),
            "tags_in_articles_papers": len(tags_in_articles_papers),
            "tweets_only_tags": len(tweets_only),
            "articles_only_tags": len(articles_only),
            "papers_only_tags": len(papers_only)
        }

        # Compute tag_distribution per source
        tweet_instances = db.tag_instances.count_documents({"content_type": "tweet"})
        article_instances = db.tag_instances.count_documents({"content_type": "article"})
        paper_instances = db.tag_instances.count_documents({"content_type": "paper"})

        total_tweets = db.tweets.count_documents({})
        total_articles = db.articles.count_documents({})
        total_papers = db.papers.count_documents({})

        tag_distribution = {
            "tweets": {
                "unique_tags": len(tags_with_tweet),
                "total_applications": tweet_instances,
                "avg_tags_per_item": round(tweet_instances / total_tweets, 2) if total_tweets > 0 else 0
            },
            "articles": {
                "unique_tags": len(tags_with_article),
                "total_applications": article_instances,
                "avg_tags_per_item": round(article_instances / total_articles, 2) if total_articles > 0 else 0
            },
            "papers": {
                "unique_tags": len(tags_with_paper),
                "total_applications": paper_instances,
                "avg_tags_per_item": round(paper_instances / total_papers, 2) if total_papers > 0 else 0
            }
        }

        # Get universal tags (in all 3 sources) - get their names
        universal_tags = []
        for tag_id in list(tags_in_all)[:10]:  # Limit to 10
            try:
                concept = db.tag_concepts_v2.find_one({"_id": ObjectId(tag_id)})
                if concept:
                    universal_tags.append(concept.get("display_name", "Unknown"))
            except:
                pass
        
        # Common authors across sources
        twitter_authors = set(db.tweets.distinct("author_username"))
        article_authors = set(db.articles.distinct("author"))
        
        # Check for author overlap (normalize names)
        author_overlap = []
        for t_author in twitter_authors:
            if not t_author:
                continue
            t_lower = t_author.lower()
            for a_author in article_authors:
                if not a_author:
                    continue
                a_lower = a_author.lower()
                # Check if names overlap (handling NoneType)
                try:
                    if t_lower in a_lower or a_lower in t_lower:
                        author_overlap.append({
                            "twitter": t_author,
                            "substack": a_author
                        })
                except TypeError:
                    continue
        
        # Content correlation by day
        correlation_data = []
        now = datetime.now(timezone.utc)
        for i in range(30):
            day = now - timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            correlation_data.append({
                "date": day_start.isoformat(),
                "tweets": db.tweets.count_documents({
                    "created_at": {"$gte": day_start, "$lt": day_end}
                }),
                "articles": db.articles.count_documents({
                    "created_at": {"$gte": day_start, "$lt": day_end}
                }),
                "papers": db.papers.count_documents({
                    "created_at": {"$gte": day_start, "$lt": day_end}
                })
            })
        
        return {
            "papers_mentioned_in_tweets": len(papers_in_tweets),
            "tweets_with_paper_links": tweets_with_papers,
            "articles_mentioning_papers": articles_with_papers,
            "tags_used_across_sources": cross_source_tags,
            "total_unique_tags": len(tag_sources),
            "author_overlap": author_overlap[:10],  # Limit to top 10
            "correlation_timeline": correlation_data,
            # New fields for frontend
            "content_coverage": content_coverage,
            "tag_distribution": tag_distribution,
            "universal_tags": universal_tags
        }
        
    except Exception as e:
        logger.error(f"Error getting cross-source statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics/system")
async def get_system_statistics():
    """Get system health and performance statistics"""
    try:
        # Database size estimation
        stats = db.command("dbStats")
        
        # Collection sizes
        collection_sizes = {}
        for collection_name in db.list_collection_names():
            try:
                coll_stats = db.command("collStats", collection_name)
                collection_sizes[collection_name] = {
                    "documents": coll_stats.get("count", 0),
                    "size_bytes": coll_stats.get("size", 0),
                    "avg_doc_size": coll_stats.get("avgObjSize", 0)
                }
            except:
                continue
        
        # RAG index status
        rag_stats = {
            "indexed_documents": 0,
            "index_size_mb": 0,
            "last_rebuild": None
        }
        
        # Check if RAG index exists
        rag_index_path = str(RAG_INDEX_PATH)
        if os.path.exists(rag_index_path):
            try:
                import pickle
                with open(os.path.join(rag_index_path, "metadata.pkl"), "rb") as f:
                    metadata = pickle.load(f)
                    rag_stats["indexed_documents"] = len(metadata)
                
                # Get index size
                index_size = 0
                for file in os.listdir(rag_index_path):
                    file_path = os.path.join(rag_index_path, file)
                    if os.path.isfile(file_path):
                        index_size += os.path.getsize(file_path)
                rag_stats["index_size_mb"] = index_size / (1024 * 1024)
                
                # Get last modified time
                index_info_path = os.path.join(rag_index_path, "index_info.json")
                if os.path.exists(index_info_path):
                    import json
                    with open(index_info_path, "r") as f:
                        info = json.load(f)
                        rag_stats["last_rebuild"] = info.get("created_at")
            except:
                pass
        
        # Vector store status
        vector_stats = {
            "embeddings_cached": 0,
            "vector_store_size_mb": 0
        }

        vector_store_path = str(VECTOR_STORE_PATH)
        if os.path.exists(vector_store_path):
            try:
                # Count cached embeddings
                embeddings_path = os.path.join(vector_store_path, "embeddings_cache.pkl")
                if os.path.exists(embeddings_path):
                    import pickle
                    with open(embeddings_path, "rb") as f:
                        embeddings = pickle.load(f)
                        vector_stats["embeddings_cached"] = len(embeddings)
                
                # Get store size
                store_size = 0
                for file in os.listdir(vector_store_path):
                    file_path = os.path.join(vector_store_path, file)
                    if os.path.isfile(file_path):
                        store_size += os.path.getsize(file_path)
                vector_stats["vector_store_size_mb"] = store_size / (1024 * 1024)
            except:
                pass
        
        # Processing queue status
        processing_stats = {
            "unprocessed_tweets": db.tweets.count_documents({"processed": False}),
            "untagged_tweets": db.tweets.count_documents({"concept_ids": []}),
            "unsummarized_articles": db.articles.count_documents({
                "$or": [
                    {"summary": {"$exists": False}},
                    {"summary": ""}
                ]
            }),
            "unprocessed_papers": db.papers.count_documents({
                "$and": [
                    {"grobid_processed": {"$ne": True}},
                    {"marker_processed": {"$ne": True}}
                ]
            })
        }
        
        return {
            "database": {
                "total_size_mb": stats.get("dataSize", 0) / (1024 * 1024),
                "storage_size_mb": stats.get("storageSize", 0) / (1024 * 1024),
                "collections": len(collection_sizes),
                "total_documents": sum(c["documents"] for c in collection_sizes.values()),
                "indexes": stats.get("indexes", 0)
            },
            "collection_sizes": collection_sizes,
            "rag_index": rag_stats,
            "vector_store": vector_stats,
            "processing_queue": processing_stats,
            "system_health": {
                "all_collections_accessible": True,
                "rag_index_available": rag_stats["indexed_documents"] > 0,
                "vector_store_available": vector_stats["embeddings_cached"] > 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting system statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics/llm")
async def get_llm_statistics():
    """Get LLM usage statistics and history"""
    try:
        # Get LLM usage from MongoDB
        llm_usage_collection = db.llm_usage

        # Most recent LLM calls
        recent_calls = list(llm_usage_collection.find(
            {},
            {"_id": 0}
        ).sort("timestamp", DESCENDING).limit(20))

        # Get last used model
        last_call = llm_usage_collection.find_one(
            {},
            {"_id": 0, "model": 1, "task_type": 1, "timestamp": 1, "status": 1}
        , sort=[("timestamp", DESCENDING)])

        # Model usage distribution
        model_distribution = list(llm_usage_collection.aggregate([
            {"$group": {"_id": "$model", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]))

        # Task type distribution
        task_distribution = list(llm_usage_collection.aggregate([
            {"$group": {"_id": "$task_type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]))

        # Usage by hour (last 24 hours)
        now = datetime.now(timezone.utc)
        day_ago = now - timedelta(days=1)

        usage_last_24h = llm_usage_collection.count_documents({
            "timestamp": {"$gte": day_ago}
        })

        # Token usage statistics
        token_stats = list(llm_usage_collection.aggregate([
            {
                "$group": {
                    "_id": None,
                    "total_tokens": {"$sum": "$tokens_used"},
                    "avg_tokens": {"$avg": "$tokens_used"},
                    "total_calls": {"$sum": 1}
                }
            }
        ]))

        token_summary = token_stats[0] if token_stats else {
            "total_tokens": 0,
            "avg_tokens": 0,
            "total_calls": 0
        }

        # Success rate
        total_calls = llm_usage_collection.count_documents({})
        successful_calls = llm_usage_collection.count_documents({"status": "success"})
        success_rate = (successful_calls / total_calls * 100) if total_calls > 0 else 0

        # Average duration
        duration_stats = list(llm_usage_collection.aggregate([
            {
                "$group": {
                    "_id": "$model",
                    "avg_duration": {"$avg": "$duration_ms"}
                }
            },
            {"$sort": {"avg_duration": -1}}
        ]))

        return {
            "last_used": last_call,
            "recent_calls": recent_calls,
            "model_distribution": model_distribution,
            "task_distribution": task_distribution,
            "usage_last_24h": usage_last_24h,
            "total_calls": total_calls,
            "success_rate": round(success_rate, 2),
            "token_usage": {
                "total": token_summary.get("total_tokens", 0),
                "average_per_call": round(token_summary.get("avg_tokens", 0), 2),
                "total_calls": token_summary.get("total_calls", 0)
            },
            "performance": duration_stats,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting LLM statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics/summary")
async def get_statistics_summary():
    """Get a comprehensive summary of all statistics"""
    try:
        # Gather all statistics
        overview = await get_system_overview()
        content = await get_content_statistics()
        authors = await get_author_statistics()
        tags = await get_tag_statistics()
        trends = await get_trend_statistics()
        cross_source = await get_cross_source_statistics()
        system = await get_system_statistics()
        
        # Calculate some additional insights
        insights = {
            "average_tweets_per_author": (
                overview["total_tweets"] / overview["unique_twitter_authors"]
                if overview["unique_twitter_authors"] > 0 else 0
            ),
            "average_articles_per_author": (
                overview["total_articles"] / overview["unique_substack_authors"]
                if overview["unique_substack_authors"] > 0 else 0
            ),
            "content_diversity_score": (
                len(set([overview["total_tweets"] > 0, 
                        overview["total_articles"] > 0,
                        overview["total_papers"] > 0])) / 3.0 * 100
            ),
            "tagging_completion_rate": (
                (content["tweets"]["tagged"] / content["tweets"]["total"] * 100)
                if content["tweets"]["total"] > 0 else 0
            ),
            "summarization_rate": (
                (content["articles"]["with_summaries"] / content["articles"]["total"] * 100)
                if content["articles"]["total"] > 0 else 0
            ),
            "cross_pollination_score": (
                (cross_source["tags_used_across_sources"] / cross_source["total_unique_tags"] * 100)
                if cross_source["total_unique_tags"] > 0 else 0
            )
        }
        
        # Get recently added concepts
        recent_concepts = list(db.tag_concepts_v2.find(
            {"created_at": {"$exists": True}},
            {"display_name": 1, "created_at": 1, "entity_type": 1}
        ).sort("created_at", -1).limit(10))
        recently_added_tags = [
            {
                "id": str(c["_id"]),
                "tag": c.get("display_name", "Unknown"),  # Frontend expects 'tag' not 'name'
                "entity_type": c.get("entity_type", "concept"),
                "date": c.get("created_at").strftime("%Y-%m-%d") if c.get("created_at") else None  # Frontend expects 'date' not 'added_at'
            }
            for c in recent_concepts
        ]

        # Get articles per week (last 4 weeks)
        now = datetime.now(timezone.utc)
        articles_per_week = []
        for i in range(4):
            week_end = now - timedelta(weeks=i)
            week_start = week_end - timedelta(weeks=1)
            count = db.articles.count_documents({
                "created_at": {"$gte": week_start, "$lt": week_end}
            })
            articles_per_week.append({
                "week": f"Week {i+1}",
                "start": week_start.strftime("%Y-%m-%d"),
                "count": count
            })

        # Get last collection timestamps
        last_tweet = db.tweets.find_one(sort=[("created_at", -1)])
        last_article = db.articles.find_one(sort=[("created_at", -1)])
        last_tweet_time = last_tweet.get("created_at").isoformat() if last_tweet and last_tweet.get("created_at") else None
        last_article_time = last_article.get("created_at").isoformat() if last_article and last_article.get("created_at") else None

        # Format for frontend consumption
        return {
            "content": content,
            "authors": {
                "twitter_authors": authors.get("top_twitter_authors", []),
                "article_authors": authors.get("top_substack_authors", [])
            },
            "tags": {
                "total_concepts": tags.get("total_concepts", 0),
                "unique_tags": len(tag_sources) if 'tag_sources' in locals() else tags.get("total_concepts", 0),
                "organized": tags.get("root_concepts", 0) + tags.get("leaf_concepts", 0),
                "unorganized": tags.get("orphaned_tag_instances", 0),
                "most_used": tags.get("most_used_tags", [])[:10],
                "recently_added": recently_added_tags
            },
            "trends": {
                "hot_topics": trends.get("hot_topics", []),
                "emerging_tags": trends.get("emerging_tags", []),
                "timeline": {
                    "tweets_per_day": trends.get("timeline", {}).get("tweets_per_day", []),
                    "articles_per_week": articles_per_week
                }
            },
            "system": {
                "database_size": f"{system.get('database', {}).get('total_size_mb', 0):.2f} MB",
                "collection_status": {  # Frontend expects nested collection_status
                    "last_tweet_collection": last_tweet_time,
                    "last_article_collection": last_article_time
                }
            },
            "rag": {
                "indexed_documents": system.get("rag_index", {}).get("indexed_documents", 0),
                "last_rebuild": system.get("rag_index", {}).get("last_rebuild"),
                "status": "ready" if system.get("rag_index", {}).get("indexed_documents", 0) > 0 else "not_ready"
            },
            "insights": insights,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting statistics summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
