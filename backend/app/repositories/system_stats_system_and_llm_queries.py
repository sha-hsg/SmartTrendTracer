"""
MongoDB queries of app.api.system_stats.system_and_llm, moved verbatim out of the router
(one function per former inline call site).
"""
from pymongo import DESCENDING
from app.database.mongodb import get_database

db = get_database()


def tweets_find_one__get_statistics_summary():
    """tweets.find_one from system_stats.system_and_llm.get_statistics_summary()"""
    return db.tweets.find_one(sort=[("created_at", -1)])


def articles_find_one__get_statistics_summary():
    """articles.find_one from system_stats.system_and_llm.get_statistics_summary()"""
    return db.articles.find_one(sort=[("created_at", -1)])


def tweets_count_documents__get_system_statistics():
    """tweets.count_documents from system_stats.system_and_llm.get_system_statistics()"""
    return db.tweets.count_documents({"processed": False})


def tweets_count_documents__get_system_statistics_2():
    """tweets.count_documents from system_stats.system_and_llm.get_system_statistics()"""
    return db.tweets.count_documents({"concept_ids": []})


def articles_count_documents__get_system_statistics():
    """articles.count_documents from system_stats.system_and_llm.get_system_statistics()"""
    return db.articles.count_documents({
                    "$or": [
                        {"summary": {"$exists": False}},
                        {"summary": ""}
                    ]
                })


def papers_count_documents__get_system_statistics():
    """papers.count_documents from system_stats.system_and_llm.get_system_statistics()"""
    return db.papers.count_documents({
                    "processed": {"$ne": True}
                })


def articles_count_documents__get_statistics_summary(week_start, week_end):
    """articles.count_documents from system_stats.system_and_llm.get_statistics_summary()"""
    return db.articles.count_documents({
                    "created_at": {"$gte": week_start, "$lt": week_end}
                })


def tag_concepts_v2_find__get_statistics_summary():
    """tag_concepts_v2.find from system_stats.system_and_llm.get_statistics_summary()"""
    return db.tag_concepts_v2.find(
                {"created_at": {"$exists": True}},
                {"display_name": 1, "created_at": 1, "entity_type": 1}
            ).sort('created_at', -1).limit(10)


def llm_usage_find_one__get_llm_statistics():
    """llm_usage.find_one from system_stats.system_and_llm.get_llm_statistics()"""
    return db.llm_usage.find_one(
                {},
                {"_id": 0, "model": 1, "task_type": 1, "timestamp": 1, "status": 1}
            , sort=[("timestamp", DESCENDING)])


def llm_usage_count_documents__get_llm_statistics(day_ago):
    """llm_usage.count_documents from system_stats.system_and_llm.get_llm_statistics()"""
    return db.llm_usage.count_documents({
                "timestamp": {"$gte": day_ago}
            })


def llm_usage_count_documents__get_llm_statistics_2():
    """llm_usage.count_documents from system_stats.system_and_llm.get_llm_statistics()"""
    return db.llm_usage.count_documents({})


def llm_usage_count_documents__get_llm_statistics_3():
    """llm_usage.count_documents from system_stats.system_and_llm.get_llm_statistics()"""
    return db.llm_usage.count_documents({"status": "success"})


def llm_usage_aggregate__get_llm_statistics():
    """llm_usage.aggregate from system_stats.system_and_llm.get_llm_statistics()"""
    return db.llm_usage.aggregate([
                {"$group": {"_id": "$model", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ])


def llm_usage_aggregate__get_llm_statistics_2():
    """llm_usage.aggregate from system_stats.system_and_llm.get_llm_statistics()"""
    return db.llm_usage.aggregate([
                {"$group": {"_id": "$task_type", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ])


def llm_usage_aggregate__get_llm_statistics_3():
    """llm_usage.aggregate from system_stats.system_and_llm.get_llm_statistics()"""
    return db.llm_usage.aggregate([
                {
                    "$group": {
                        "_id": None,
                        "total_tokens": {"$sum": "$tokens_used"},
                        "avg_tokens": {"$avg": "$tokens_used"},
                        "total_calls": {"$sum": 1}
                    }
                }
            ])


def llm_usage_aggregate__get_llm_statistics_4():
    """llm_usage.aggregate from system_stats.system_and_llm.get_llm_statistics()"""
    return db.llm_usage.aggregate([
                {
                    "$group": {
                        "_id": "$model",
                        "avg_duration": {"$avg": "$duration_ms"}
                    }
                },
                {"$sort": {"avg_duration": -1}}
            ])


def llm_usage_find__get_llm_statistics():
    """llm_usage.find from system_stats.system_and_llm.get_llm_statistics()"""
    return db.llm_usage.find(
                {},
                {"_id": 0}
            ).sort('timestamp', DESCENDING).limit(20)


def database_size_stats():
    """dbStats plus per-collection document/size figures."""
    stats = db.command("dbStats")
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
    return stats, collection_sizes
