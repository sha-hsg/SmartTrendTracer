"""
MongoDB queries of app.api.tag_ontology.concepts, moved verbatim out of the router
(one function per former inline call site).
"""
from datetime import datetime
from datetime import timezone
from app.database.mongodb import get_database

db = get_database()


def tag_instances_aggregate__get_concept_detail(id_variants):
    """tag_instances.aggregate from tag_ontology.concepts.get_concept_detail()"""
    return db.tag_instances.aggregate([
            {"$match": {"concept_id": {"$in": id_variants}}},
            {"$group": {"_id": "$content_type", "count": {"$sum": 1}}}
        ])


def tag_concepts_v2_insert_one__create_concept(concept):
    """tag_concepts_v2.insert_one from tag_ontology.concepts.create_concept()"""
    return db.tag_concepts_v2.insert_one(concept)


def tag_concepts_v2_update_one__update_concept(fields, concept):
    """tag_concepts_v2.update_one from tag_ontology.concepts.update_concept()"""
    return db.tag_concepts_v2.update_one({"_id": concept["_id"]}, {"$set": fields})


def tag_concepts_v2_update_one__delete_concept(concept):
    """tag_concepts_v2.update_one from tag_ontology.concepts.delete_concept()"""
    return db.tag_concepts_v2.update_one(
        {"_id": concept["_id"]},
        {
            "$set": {
                "status": "deprecated",
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )


def tag_aliases_v2_find__get_concept_detail(id_variants):
    """tag_aliases_v2.find from tag_ontology.concepts.get_concept_detail()"""
    return db.tag_aliases_v2.find({"concept_id": {"$in": id_variants}})


def tag_concepts_v2_update_one__create_concept(parent, new_oid):
    """tag_concepts_v2.update_one from tag_ontology.concepts.create_concept()"""
    return db.tag_concepts_v2.update_one(
        {"_id": parent["_id"]},
        {"$push": {"children": new_oid}}
    )


def tag_concepts_v2_find__get_concept_detail(parent_ids):
    """tag_concepts_v2.find from tag_ontology.concepts.get_concept_detail()"""
    return db.tag_concepts_v2.find({"_id": {"$in": parent_ids}})


def tag_concepts_v2_find__get_concept_detail_2(child_ids):
    """tag_concepts_v2.find from tag_ontology.concepts.get_concept_detail()"""
    return db.tag_concepts_v2.find({"_id": {"$in": child_ids}})


def find_active_concepts():
    """Cursor over all non-deprecated concepts."""
    return db.tag_concepts_v2.find({'status': {'$ne': 'deprecated'}})
