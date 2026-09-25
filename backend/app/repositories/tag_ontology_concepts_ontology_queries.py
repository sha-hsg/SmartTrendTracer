"""
MongoDB queries of app.api.tag_ontology.concepts_ontology, moved verbatim out of the router
(one function per former inline call site).
"""
from app.database.mongodb import get_database

db = get_database()


def tag_concepts_v2_insert_one__create_concept_ontology(new_concept):
    """tag_concepts_v2.insert_one from tag_ontology.concepts_ontology.create_concept_ontology()"""
    return db.tag_concepts_v2.insert_one(new_concept)


def tag_concepts_v2_update_one__update_concept_ontology(oid, update_data):
    """tag_concepts_v2.update_one from tag_ontology.concepts_ontology.update_concept_ontology()"""
    return db.tag_concepts_v2.update_one(
                {"_id": oid},
                {"$set": update_data}
            )


def tag_concepts_v2_find_one__delete_concept_ontology(oid):
    """tag_concepts_v2.find_one from tag_ontology.concepts_ontology.delete_concept_ontology()"""
    return db.tag_concepts_v2.find_one({"_id": oid})


def tag_concepts_v2_update_many__delete_concept_ontology(id_variants):
    """tag_concepts_v2.update_many from tag_ontology.concepts_ontology.delete_concept_ontology()"""
    return db.tag_concepts_v2.update_many(
        {"children": {"$in": id_variants}},
        {"$pull": {"children": {"$in": id_variants}}}
    )


def tag_concepts_v2_update_many__delete_concept_ontology_2(id_variants):
    """tag_concepts_v2.update_many from tag_ontology.concepts_ontology.delete_concept_ontology()"""
    return db.tag_concepts_v2.update_many(
        {"parents": {"$in": id_variants}},
        {"$pull": {"parents": {"$in": id_variants}}}
    )


def tag_instances_delete_many__delete_concept_ontology(id_variants):
    """tag_instances.delete_many from tag_ontology.concepts_ontology.delete_concept_ontology()"""
    return db.tag_instances.delete_many({"concept_id": {"$in": id_variants}})


def tag_concepts_v2_delete_one__delete_concept_ontology(oid):
    """tag_concepts_v2.delete_one from tag_ontology.concepts_ontology.delete_concept_ontology()"""
    return db.tag_concepts_v2.delete_one({"_id": oid})


def tag_concepts_v2_update_one__create_concept_ontology(parent_oid, result):
    """tag_concepts_v2.update_one from tag_ontology.concepts_ontology.create_concept_ontology()"""
    return db.tag_concepts_v2.update_one(
        {"_id": parent_oid},
        {"$push": {"children": result.inserted_id}}
    )


def tag_concepts_v2_find_one__update_concept_ontology(concept_id):
    """tag_concepts_v2.find_one from tag_ontology.concepts_ontology.update_concept_ontology()"""
    return db.tag_concepts_v2.find_one({"id": concept_id})


def tag_concepts_v2_find_one__update_concept_ontology_2(concept_id):
    """tag_concepts_v2.find_one from tag_ontology.concepts_ontology.update_concept_ontology()"""
    return db.tag_concepts_v2.find_one({"id": concept_id})


def tag_concepts_v2_find_one__delete_concept_ontology_2(concept_id):
    """tag_concepts_v2.find_one from tag_ontology.concepts_ontology.delete_concept_ontology()"""
    return db.tag_concepts_v2.find_one({"id": concept_id})


def tag_concepts_v2_find_one__delete_concept_ontology_3(concept_id):
    """tag_concepts_v2.find_one from tag_ontology.concepts_ontology.delete_concept_ontology()"""
    return db.tag_concepts_v2.find_one({"id": concept_id})
