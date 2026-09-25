"""
MongoDB queries of app.api.tweets.annotation, moved verbatim out of the router
(one function per former inline call site).
"""
from datetime import datetime
from datetime import timezone
from app.database.mongodb import get_database

db = get_database()


def tweets_distinct__batch_annotate_all_unannotated():
    """tweets.distinct from tweets.annotation.batch_annotate_all_unannotated()"""
    return db.tweets.distinct('_id')


def tag_instances_aggregate__batch_annotate_all_unannotated(annotated_pipeline):
    """tag_instances.aggregate from tweets.annotation.batch_annotate_all_unannotated()"""
    return db.tag_instances.aggregate(annotated_pipeline)


def tweets_find_one__annotate_one(tweet_id):
    """tweets.find_one from tweets.annotation.annotate_one()"""
    return db.tweets.find_one({"_id": tweet_id})


def tag_instances_update_one__annotate_one(tweet_id):
    """tag_instances.update_one from tweets.annotation.annotate_one()"""
    return db.tag_instances.update_one(
        {'content_type': 'tweet', 'content_id': str(tweet_id), 'concept_id': None},
        {'$setOnInsert': {
            'content_type': 'tweet',
            'content_id': str(tweet_id),
            'concept_id': None,
            'display_name': '_no_concepts',
            'created_at': datetime.now(timezone.utc),
            'source': 'auto_annotation',
        }},
        upsert=True
    )
