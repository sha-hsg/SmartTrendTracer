"""
MongoDB queries of app.api.article_clustering_mongodb, moved verbatim out of the router
(one function per former inline call site).
"""
from app.database.mongodb import get_database

db = get_database()


def articles_find_one__find_similar_articles(obj_id):
    """articles.find_one from article_clustering_mongodb.find_similar_articles()"""
    return db.articles.find_one({'_id': obj_id})


def articles_find___get_tagged_articles(limit):
    """articles.find from article_clustering_mongodb._get_tagged_articles()"""
    return db.articles.find(
            {'tags': {'$exists': True, '$ne': []}},
            {'title': 1, 'author': 1, 'tags': 1, 'url': 1, 'published_at': 1, 'summary': 1}
        ).limit(limit)
