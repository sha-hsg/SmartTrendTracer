"""
MongoDB queries of app.api.analytics_trends.timeline_animation, moved verbatim out of the router
(one function per former inline call site).
"""
from bson import ObjectId
from app.database.mongodb import get_database

db = get_database()


def tag_concepts_v2_find_one__get_animated_timeline_data(cid):
    """tag_concepts_v2.find_one from analytics_trends.timeline_animation.get_animated_timeline_data()"""
    return db.tag_concepts_v2.find_one({'_id': ObjectId(cid)})
