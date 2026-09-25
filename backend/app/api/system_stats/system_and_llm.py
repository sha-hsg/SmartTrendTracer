"""
System health, LLM usage, summary statistics, and circuit breaker endpoints.
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone, timedelta
from pymongo import DESCENDING
import os

from app.paths import RAG_INDEX_PATH, VECTOR_STORE_PATH
from .utils import db, logger
from app.repositories import system_stats_system_and_llm_queries as queries

router = APIRouter(
    prefix="/api/system",
    tags=["system-statistics"]
)


async def get_system_statistics():
    """System health and performance statistics (used internally by /statistics/summary)"""
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
            except Exception:
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
            except Exception:
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
            except Exception:
                pass

        # Processing queue status
        processing_stats = {
            "unprocessed_tweets": queries.tweets_count_documents__get_system_statistics(),
            "untagged_tweets": queries.tweets_count_documents__get_system_statistics_2(),
            "unsummarized_articles": queries.articles_count_documents__get_system_statistics(),
            # Papers track processing via 'processed' / 'processing_status'
            # (grobid_processed/marker_processed are legacy fields)
            "unprocessed_papers": queries.papers_count_documents__get_system_statistics()
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
        # Import sibling endpoints for aggregation
        from .overview_and_content import (
            get_system_overview,
            get_content_statistics,
            get_author_statistics,
        )
        from .analytics import (
            get_tag_statistics,
            get_trend_statistics,
            get_cross_source_statistics,
        )

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
        recent_concepts = list(queries.tag_concepts_v2_find__get_statistics_summary().sort("created_at", -1).limit(10))
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
            count = queries.articles_count_documents__get_statistics_summary(week_start, week_end)
            articles_per_week.append({
                "week": f"Week {i+1}",
                "start": week_start.strftime("%Y-%m-%d"),
                "count": count
            })

        # Get last collection timestamps
        last_tweet = queries.tweets_find_one__get_statistics_summary()
        last_article = queries.articles_find_one__get_statistics_summary()
        last_tweet_time = last_tweet.get("created_at").isoformat() if last_tweet and last_tweet.get("created_at") else None
        last_article_time = last_article.get("created_at").isoformat() if last_article and last_article.get("created_at") else None

        # Format for frontend consumption
        return {
            "content": content,
            "authors": {
                "twitter_authors": authors.get("twitter_authors", []),
                "article_authors": authors.get("article_authors", [])
            },
            "tags": {
                "total_concepts": tags.get("total_concepts", 0),
                "unique_tags": tags.get("total_concepts", 0),
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


