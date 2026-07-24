"""
Tag, trend, and cross-source analytics endpoints.
Tag statistics, trend analysis, cross-source correlations.
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from bson import ObjectId

from .utils import db, logger

router = APIRouter(
    prefix="/api/system",
    tags=["system-statistics"]
)


async def get_tag_statistics():
    """Comprehensive tag and concept statistics (used internally by /statistics/summary)"""
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

        # Growth rate helper
        def calculate_growth(current, previous):
            if previous == 0:
                return 100 if current > 0 else 0
            return ((current - previous) / previous) * 100

        # Get top concepts by total usage count using aggregation
        pipeline = [
            {"$match": {"concept_id": {"$exists": True, "$ne": None}}},
            {"$group": {"_id": "$concept_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 15}
        ]
        top_concepts = list(db.tag_instances.aggregate(pipeline))

        # Real period comparison over tag_instances.created_at (native BSON datetime):
        # current 7-day window vs. previous 7-day window
        def _concept_counts(start, end):
            return {
                row["_id"]: row["count"]
                for row in db.tag_instances.aggregate([
                    {"$match": {
                        "concept_id": {"$exists": True, "$ne": None},
                        "created_at": {"$gte": start, "$lt": end}
                    }},
                    {"$group": {"_id": "$concept_id", "count": {"$sum": 1}}}
                ])
            }

        current_period_start = now - timedelta(days=7)
        previous_period_start = now - timedelta(days=14)
        current_counts = _concept_counts(current_period_start, now)
        previous_counts = _concept_counts(previous_period_start, current_period_start)

        # Batch-fetch all needed concept documents
        all_concept_ids = list(set(current_counts.keys()) | {item["_id"] for item in top_concepts})
        concept_docs = {c["_id"]: c for c in db.tag_concepts_v2.find({"_id": {"$in": all_concept_ids}})}

        def _trend_direction(current, previous):
            if current > previous:
                return "up"
            if current < previous:
                return "down"
            return "stable"

        # Build hot_topics with real trend direction (frontend expects: topic, mentions, trend)
        # Prefer concepts active in the current period; fill up with all-time top concepts.
        hot_topics = []
        seen_hot = set()
        current_sorted = sorted(current_counts.items(), key=lambda x: x[1], reverse=True)
        for cid, count in current_sorted[:5]:
            concept = concept_docs.get(cid)
            if concept:
                seen_hot.add(cid)
                hot_topics.append({
                    "topic": concept.get("display_name", "Unknown"),
                    "mentions": count,
                    "trend": _trend_direction(count, previous_counts.get(cid, 0))
                })
        if len(hot_topics) < 5:
            for item in top_concepts:
                if len(hot_topics) >= 5:
                    break
                cid = item["_id"]
                if cid in seen_hot:
                    continue
                concept = concept_docs.get(cid)
                if concept:
                    seen_hot.add(cid)
                    hot_topics.append({
                        "topic": concept.get("display_name", "Unknown"),
                        "mentions": item["count"],
                        "trend": _trend_direction(
                            current_counts.get(cid, 0), previous_counts.get(cid, 0)
                        )
                    })

        # Build emerging_tags with real growth rates (frontend expects: tag, growth_rate)
        emerging_candidates = []
        for cid, count in current_counts.items():
            previous = previous_counts.get(cid, 0)
            growth_rate = calculate_growth(count, previous)
            if count >= 2 and growth_rate > 0:
                emerging_candidates.append((cid, count, growth_rate))
        emerging_candidates.sort(key=lambda x: (x[2], x[1]), reverse=True)

        emerging_tags = []
        for cid, count, growth_rate in emerging_candidates[:10]:
            concept = concept_docs.get(cid)
            if concept:
                emerging_tags.append({
                    "tag": concept.get("display_name", "Unknown"),
                    "growth_rate": round(growth_rate, 1)
                })

        # Keep trending_tags for backward compatibility
        trending_tags = []
        for item in top_concepts[:10]:
            concept = concept_docs.get(item["_id"])
            if concept:
                trending_tags.append({
                    "id": str(item["_id"]),
                    "name": concept.get("display_name", "Unknown"),
                    "count": item["count"],
                    "entity_type": concept.get("entity_type", "concept")
                })

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

        # Articles per week (last 4 weeks)
        articles_per_week = []
        for i in range(4):
            week_end = now - timedelta(weeks=i)
            week_start = week_end - timedelta(weeks=1)
            articles_per_week.append({
                "week": f"Week {i + 1}",
                "start": week_start.strftime("%Y-%m-%d"),
                "count": db.articles.count_documents({
                    "created_at": {"$gte": week_start, "$lt": week_end}
                })
            })

        return {
            "daily_stats": daily_stats,
            "weekly_trend": weekly_data,
            "trending_topics": trending_tags,
            "growth_rates": growth_rates,
            # Add these fields for the frontend charts
            "timeline": {
                "tweets_per_day": tweets_per_day,
                "articles_per_week": articles_per_week
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
            except Exception:
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
