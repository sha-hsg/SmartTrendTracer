"""
MongoDB queries of app.api.tag_ontology.utils, moved verbatim out of the router
(one function per former inline call site).
"""
from bson import ObjectId
from app.database.mongodb import get_database

db = get_database()


def find_concept_by_any_id(concept_id: str):
    """Find a concept by its custom id field ("c_...") or its ObjectId string."""
    concept = db.tag_concepts_v2.find_one({"id": concept_id})
    if concept is None and ObjectId.is_valid(concept_id):
        concept = db.tag_concepts_v2.find_one({"_id": ObjectId(concept_id)})
    return concept
