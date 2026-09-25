"""
MongoDB queries of app.api.system_stats.system_and_llm, moved verbatim out of the router
(one function per former inline call site).
"""
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
            )
