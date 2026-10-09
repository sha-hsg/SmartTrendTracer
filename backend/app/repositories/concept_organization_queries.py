"""
MongoDB queries of app.api.concept_organization, moved out of the router.
"""
from app.database.mongodb import get_database

db = get_database()


def count_aliases():
    return db.tag_aliases_v2.count_documents({})


def count_orphan_tag_instances():
    """Tag instances without a concept (the _no_concepts sentinel rows)."""
    return db.tag_instances.count_documents({"concept_id": None})
