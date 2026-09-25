"""Concept ontology queries shared by the tag_ontology / organization routers."""
from bson import ObjectId
from app.database.mongodb import get_database

db = get_database()


def find_concept_by_any_id(concept_id: str):
    """Find a concept by its custom id field ("c_...") or its ObjectId string."""
    concept = db.tag_concepts_v2.find_one({"id": concept_id})
    if concept is None and ObjectId.is_valid(concept_id):
        concept = db.tag_concepts_v2.find_one({"_id": ObjectId(concept_id)})
    return concept


def find_all_aliases():
    """Cursor over all concept aliases."""
    return db.tag_aliases_v2.find({})


def count_concepts():
    """Total number of concepts."""
    return db.tag_concepts_v2.count_documents({})


def remove_from_children(id_variants):
    """Remove a concept (all id forms) from every children list."""
    return db.tag_concepts_v2.update_many({'children': {'$in': id_variants}}, {'$pull': {'children': {'$in': id_variants}}})


def remove_from_parents(id_variants):
    """Remove a concept (all id forms) from every parents list."""
    return db.tag_concepts_v2.update_many({'parents': {'$in': id_variants}}, {'$pull': {'parents': {'$in': id_variants}}})


def delete_concept_instances(id_variants):
    """Delete all tag instances of a concept (all id forms)."""
    return db.tag_instances.delete_many({'concept_id': {'$in': id_variants}})
