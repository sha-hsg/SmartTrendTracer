"""
MongoDB queries of app.api.substack_mongodb, moved verbatim out of the router
(one function per former inline call site).
"""
from app.database.mongodb import get_database

db = get_database()


def articles_find__get_substack_trends(start_date, end_date):
    """articles.find from substack_mongodb.get_substack_trends()"""
    return db.articles.find({
                "published_at": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            })


def articles_find__get_substack_trends_2(prev_start, prev_end):
    """articles.find from substack_mongodb.get_substack_trends()"""
    return db.articles.find({
                'published_at': {'$gte': prev_start, '$lt': prev_end}
            })
