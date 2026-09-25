"""
MongoDB queries of app.api.reddit_mongodb, moved verbatim out of the router
(one function per former inline call site).
"""
from datetime import timedelta
from app.database.mongodb import get_database

db = get_database()


def tag_instances_find___build_reddit_query(concept_filter):
    """tag_instances.find from reddit_mongodb._build_reddit_query()"""
    return db.tag_instances.find({"concept_id": concept_filter})


def reddit_posts_find__get_reddit_posts(query):
    """reddit_posts.find from reddit_mongodb.get_reddit_posts()"""
    return db.reddit_posts.find(query)


def reddit_posts_count_documents__get_reddit_faceted_search(query):
    """reddit_posts.count_documents from reddit_mongodb.get_reddit_faceted_search()"""
    return db.reddit_posts.count_documents(query)


def reddit_posts_aggregate__get_reddit_facets(subreddit_pipeline):
    """reddit_posts.aggregate from reddit_mongodb.get_reddit_facets()"""
    return db.reddit_posts.aggregate(subreddit_pipeline)


def reddit_posts_aggregate__get_reddit_facets_2(author_pipeline):
    """reddit_posts.aggregate from reddit_mongodb.get_reddit_facets()"""
    return db.reddit_posts.aggregate(author_pipeline)


def reddit_posts_count_documents__get_reddit_facets(now):
    """reddit_posts.count_documents from reddit_mongodb.get_reddit_facets()"""
    return db.reddit_posts.count_documents({"created_utc": {"$gte": now - timedelta(hours=24)}})


def reddit_posts_count_documents__get_reddit_facets_2(now):
    """reddit_posts.count_documents from reddit_mongodb.get_reddit_facets()"""
    return db.reddit_posts.count_documents({"created_utc": {"$gte": now - timedelta(days=7)}})


def reddit_posts_count_documents__get_reddit_facets_3(now):
    """reddit_posts.count_documents from reddit_mongodb.get_reddit_facets()"""
    return db.reddit_posts.count_documents({"created_utc": {"$gte": now - timedelta(days=30)}})


def reddit_posts_count_documents__get_reddit_facets_4():
    """reddit_posts.count_documents from reddit_mongodb.get_reddit_facets()"""
    return db.reddit_posts.count_documents({"score": {"$gte": 100}})


def reddit_posts_count_documents__get_reddit_facets_5():
    """reddit_posts.count_documents from reddit_mongodb.get_reddit_facets()"""
    return db.reddit_posts.count_documents({"score": {"$gte": 10, "$lt": 100}})


def reddit_posts_count_documents__get_reddit_facets_6():
    """reddit_posts.count_documents from reddit_mongodb.get_reddit_facets()"""
    return db.reddit_posts.count_documents({"score": {"$lt": 10}})


def reddit_posts_count_documents__get_reddit_facets_7():
    """reddit_posts.count_documents from reddit_mongodb.get_reddit_facets()"""
    return db.reddit_posts.count_documents({"is_self": True})


def reddit_posts_count_documents__get_reddit_facets_8():
    """reddit_posts.count_documents from reddit_mongodb.get_reddit_facets()"""
    return db.reddit_posts.count_documents({"is_self": False})


def reddit_posts_count_documents__get_reddit_facets_9():
    """reddit_posts.count_documents from reddit_mongodb.get_reddit_facets()"""
    return db.reddit_posts.count_documents({"is_video": True})


def reddit_posts_count_documents__get_reddit_facets_10():
    """reddit_posts.count_documents from reddit_mongodb.get_reddit_facets()"""
    return db.reddit_posts.count_documents({})


def reddit_posts_count_documents__get_reddit_collection_stats():
    """reddit_posts.count_documents from reddit_mongodb.get_reddit_collection_stats()"""
    return db.reddit_posts.count_documents({})

