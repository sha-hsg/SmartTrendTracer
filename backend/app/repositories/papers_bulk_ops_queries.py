"""
MongoDB queries of app.api.papers.bulk_ops, moved verbatim out of the router
(one function per former inline call site).
"""
from datetime import datetime
from datetime import timezone
from app.database.mongodb import get_database

db = get_database()


def papers_update_one__bulk_action_entities(paper, rejected_items):
    """papers.update_one from papers.bulk_ops.bulk_action_entities()"""
    return db.papers.update_one(
        {'_id': paper['_id']},
        {
            '$addToSet': {'rejected_entities': {'$each': rejected_items}},
            '$set': {'rejected_entities_updated_at': datetime.now(timezone.utc)}
        }
    )


def papers_update_one__bulk_action_entities_2(paper, tagged_concept_id):
    """papers.update_one from papers.bulk_ops.bulk_action_entities()"""
    return db.papers.update_one(
        {'_id': paper['_id']},
        {'$addToSet': {'concept_ids': tagged_concept_id}}
    )
