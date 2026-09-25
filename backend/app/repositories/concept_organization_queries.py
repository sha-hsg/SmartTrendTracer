"""
MongoDB queries of app.api.concept_organization, moved out of the router.
"""
from app.database.mongodb import get_database

db = get_database()


def count_tag_instances_by_concept(id_variants):
    """Usage counts per stored concept_id form (mixed ObjectId/string)."""
    return db.tag_instances.aggregate([
        {"$match": {"concept_id": {"$in": id_variants}}},
        {"$group": {"_id": "$concept_id", "count": {"$sum": 1}}}
    ])


def count_aliases():
    return db.tag_aliases_v2.count_documents({})


def count_orphan_tag_instances():
    """Tag instances without a concept (the _no_concepts sentinel rows)."""
    return db.tag_instances.count_documents({"concept_id": None})


def tag_concepts_v2_count_documents__get_organization_stats():
    """tag_concepts_v2.count_documents from concept_organization.get_organization_stats()"""
    return db.tag_concepts_v2.count_documents({})


def tag_concepts_v2_count_documents__get_organization_stats_2():
    """tag_concepts_v2.count_documents from concept_organization.get_organization_stats()"""
    return db.tag_concepts_v2.count_documents({"is_organized": True})


def tag_concepts_v2_count_documents__get_organization_stats_3():
    """tag_concepts_v2.count_documents from concept_organization.get_organization_stats()"""
    return db.tag_concepts_v2.count_documents(
                {"$or": [
                    {"is_organized": False},
                    {"needs_review": True}
                ]}
            )

