"""
MongoDB queries of app.api.tag_ontology.aliases_and_search, moved verbatim out of the router
(one function per former inline call site).
"""
import re
from app.database.mongodb import get_database

db = get_database()


def tag_aliases_v2_delete_one__delete_alias(alias_text, concept_ids):
    """tag_aliases_v2.delete_one from tag_ontology.aliases_and_search.delete_alias()"""
    return db.tag_aliases_v2.delete_one({
            "alias_text": alias_text,
            "concept_id": {"$in": concept_ids}
        })


def tag_aliases_v2_insert_one__add_alias(alias):
    """tag_aliases_v2.insert_one from tag_ontology.aliases_and_search.add_alias()"""
    return db.tag_aliases_v2.insert_one(alias)


def tag_concepts_v2_find_one__find_concept_by_name(tag_name):
    """tag_concepts_v2.find_one from tag_ontology.aliases_and_search.find_concept_by_name()"""
    return db.tag_concepts_v2.find_one({
                "$or": [
                    {"slug": tag_name.lower()},
                    {"name": tag_name},
                    {"display_name": tag_name},
                    {"slug": tag_name.lower().replace(" ", "-")},
                    {"name": {"$regex": f"^{re.escape(tag_name)}$", "$options": "i"}}
                ]
            })


def tag_aliases_v2_find_one__find_concept_by_name(tag_name):
    """tag_aliases_v2.find_one from tag_ontology.aliases_and_search.find_concept_by_name()"""
    return db.tag_aliases_v2.find_one({"alias_text": tag_name})


def tag_concepts_v2_find_one__find_concept_by_name_2(cid):
    """tag_concepts_v2.find_one from tag_ontology.aliases_and_search.find_concept_by_name()"""
    return db.tag_concepts_v2.find_one({"_id": cid})
