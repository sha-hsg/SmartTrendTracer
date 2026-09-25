"""
MongoDB queries of app.api.tag_ontology.tools, moved verbatim out of the router
(one function per former inline call site).
"""
from app.database.mongodb import get_database

db = get_database()


def tag_concepts_v2_find__rebuild_mappings():
    """tag_concepts_v2.find from tag_ontology.tools.rebuild_mappings()"""
    return db.tag_concepts_v2.find()


def tag_aliases_v2_find__rebuild_mappings():
    """tag_aliases_v2.find from tag_ontology.tools.rebuild_mappings()"""
    return db.tag_aliases_v2.find()


def tag_instances_find__rebuild_mappings():
    """tag_instances.find from tag_ontology.tools.rebuild_mappings()"""
    return db.tag_instances.find({"concept_id": None})


def tag_instances_aggregate__get_ontology_graph():
    """tag_instances.aggregate from tag_ontology.tools.get_ontology_graph()"""
    return db.tag_instances.aggregate([
                {"$group": {"_id": "$concept_id", "count": {"$sum": 1}}}
            ])


def tag_instances_update_one__rebuild_mappings(orphan, concept_id):
    """tag_instances.update_one from tag_ontology.tools.rebuild_mappings()"""
    return db.tag_instances.update_one(
        {"_id": orphan["_id"]},
        {"$set": {"concept_id": concept_id}}
    )


def tag_concepts_v2_count_documents__get_stats():
    """tag_concepts_v2.count_documents from tag_ontology.tools.get_stats()"""
    return db.tag_concepts_v2.count_documents({})


def tag_concepts_v2_count_documents__get_stats_2():
    """tag_concepts_v2.count_documents from tag_ontology.tools.get_stats()"""
    return db.tag_concepts_v2.count_documents({"status": "active"})


def tag_concepts_v2_count_documents__get_stats_3():
    """tag_concepts_v2.count_documents from tag_ontology.tools.get_stats()"""
    return db.tag_concepts_v2.count_documents({"parents": []})


def tag_concepts_v2_count_documents__get_stats_4():
    """tag_concepts_v2.count_documents from tag_ontology.tools.get_stats()"""
    return db.tag_concepts_v2.count_documents({"children": {"$ne": []}})


def tag_aliases_v2_count_documents__get_stats():
    """tag_aliases_v2.count_documents from tag_ontology.tools.get_stats()"""
    return db.tag_aliases_v2.count_documents({})


def tag_instances_count_documents__get_stats():
    """tag_instances.count_documents from tag_ontology.tools.get_stats()"""
    return db.tag_instances.count_documents({})


def tag_instances_count_documents__get_stats_2():
    """tag_instances.count_documents from tag_ontology.tools.get_stats()"""
    return db.tag_instances.count_documents({"content_type": "tweet"})


def tag_instances_count_documents__get_stats_3():
    """tag_instances.count_documents from tag_ontology.tools.get_stats()"""
    return db.tag_instances.count_documents({"content_type": "paper"})


def tag_instances_count_documents__get_stats_4():
    """tag_instances.count_documents from tag_ontology.tools.get_stats()"""
    return db.tag_instances.count_documents({"content_type": "article"})


def tag_instances_count_documents__get_stats_5():
    """tag_instances.count_documents from tag_ontology.tools.get_stats()"""
    return db.tag_instances.count_documents({"concept_id": {"$ne": None}})


def tag_instances_count_documents__get_stats_6():
    """tag_instances.count_documents from tag_ontology.tools.get_stats()"""
    return db.tag_instances.count_documents({"concept_id": None})


def tag_concepts_v2_find__get_ontology_graph():
    """tag_concepts_v2.find from tag_ontology.tools.get_ontology_graph()"""
    return db.tag_concepts_v2.find({})


def tag_concepts_v2_find__export_ontology():
    """tag_concepts_v2.find from tag_ontology.tools.export_ontology()"""
    return db.tag_concepts_v2.find({})


def tag_aliases_v2_find__export_ontology():
    """tag_aliases_v2.find from tag_ontology.tools.export_ontology()"""
    return db.tag_aliases_v2.find({})


def tag_aliases_v2_distinct__get_stats():
    """tag_aliases_v2.distinct from tag_ontology.tools.get_stats()"""
    return db.tag_aliases_v2.distinct("concept_id")


def tag_aliases_v2_find__get_ontology_graph():
    """tag_aliases_v2.find from tag_ontology.tools.get_ontology_graph()"""
    return db.tag_aliases_v2.find({})
