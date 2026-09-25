"""
MongoDB queries of app.api.trend_analysis_mongodb, moved verbatim out of the router
(one function per former inline call site).
"""
from app.database.mongodb import get_database

db = get_database()


def tag_instances_distinct__get_trend_overview(cutoff_date):
    """tag_instances.distinct from trend_analysis_mongodb.get_trend_overview()"""
    return db.tag_instances.distinct('concept_id',
            {'created_at': {'$gte': cutoff_date}})


def tag_instances_aggregate__get_trend_overview(cutoff_date):
    """tag_instances.aggregate from trend_analysis_mongodb.get_trend_overview()"""
    return db.tag_instances.aggregate([
            {'$match': {'created_at': {'$gte': cutoff_date}}},
            {'$group': {
                '_id': '$content_type',
                'count': {'$sum': 1}
            }}
        ])


def tag_instances_aggregate__get_trend_overview_2(cutoff_date):
    """tag_instances.aggregate from trend_analysis_mongodb.get_trend_overview()"""
    return db.tag_instances.aggregate([
            {'$match': {'created_at': {'$gte': cutoff_date}}},
            {'$addFields': {
                'date': {'$dateToString': {
                    'format': '%Y-%m-%d',
                    'date': '$created_at'
                }}
            }},
            {'$group': {
                '_id': '$date',
                'count': {'$sum': 1}
            }},
            {'$sort': {'_id': 1}}
        ])
