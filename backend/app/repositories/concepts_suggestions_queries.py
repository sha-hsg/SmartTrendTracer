"""
MongoDB queries of app.api.concepts_suggestions_mongodb, moved verbatim out of the router
(one function per former inline call site).
"""
from bson import ObjectId
from app.database.mongodb import get_database

db = get_database()


def tweets_find_one__suggest_concepts_for_tweet(tweet_id):
    """tweets.find_one from concepts_suggestions_mongodb.suggest_concepts_for_tweet()"""
    return db.tweets.find_one({"_id": tweet_id})


def reddit_posts_find_one__suggest_concepts_for_reddit(post_id):
    """reddit_posts.find_one from concepts_suggestions_mongodb.suggest_concepts_for_reddit()"""
    return db.reddit_posts.find_one({"_id": ObjectId(post_id)})


def reddit_posts_find_one__suggest_concepts_for_reddit_2(post_id):
    """reddit_posts.find_one from concepts_suggestions_mongodb.suggest_concepts_for_reddit()"""
    return db.reddit_posts.find_one({"_id": post_id})


def tag_aliases_v2_find__search_concepts_semantic():
    """tag_aliases_v2.find from concepts_suggestions_mongodb.search_concepts_semantic()"""
    return db.tag_aliases_v2.find({}, {'alias_text': 1, 'concept_id': 1})
