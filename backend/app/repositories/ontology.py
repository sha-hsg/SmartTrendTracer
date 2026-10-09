"""Concept ontology queries shared by the tag_ontology / organization routers."""
from bson import ObjectId
from app.database.mongodb import get_database

db = get_database()


def find_concept_by_any_id(concept_id: str):
    """Find a concept by its ObjectId string or a legacy string _id. (The
    custom "id" field was not unique — 627 values shared by 10 726 concepts —
    and is no longer used.)"""
    concept = None
    if ObjectId.is_valid(concept_id):
        concept = db.tag_concepts_v2.find_one({"_id": ObjectId(concept_id)})
    if concept is None:
        concept = db.tag_concepts_v2.find_one({"_id": concept_id})
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


# --- Organization state: ONE definition for every statistic and the Organize list ----
# A concept counts as organized when it is placed in the hierarchy (has a parent, or
# is the parent of another concept) or the Organize step marked it (is_organized,
# e.g. resolved as an alias). `children` is not maintained consistently (21 concepts
# carry it, 24 are real parents), so parenthood is derived from `parents`.

def hierarchy_parent_ids() -> list:
    """Ids of concepts that are the parent of at least one concept."""
    return [p for p in db.tag_concepts_v2.distinct('parents') if p is not None]


def _unorganized_filter(parent_ids) -> dict:
    return {'parents.0': {'$exists': False}, '_id': {'$nin': parent_ids}, 'is_organized': {'$ne': True}}


def organization_stats() -> dict:
    parent_ids = hierarchy_parent_ids()
    total = db.tag_concepts_v2.count_documents({})
    unorganized = db.tag_concepts_v2.count_documents(_unorganized_filter(parent_ids))
    return {
        'total_concepts': total,
        'organized_concepts': total - unorganized,
        'unorganized_concepts': unorganized,
        'root_concepts': db.tag_concepts_v2.count_documents({'_id': {'$in': parent_ids}, 'parents.0': {'$exists': False}}),
        'with_children': db.tag_concepts_v2.count_documents({'_id': {'$in': parent_ids}}),
    }


def usage_counts() -> dict:
    """tag_instances per concept, keyed by str(concept _id) (all stored id forms summed)."""
    counts: dict = {}
    for row in db.tag_instances.aggregate([{'$group': {'_id': '$concept_id', 'n': {'$sum': 1}}}]):
        if row['_id'] is not None:
            counts[str(row['_id'])] = counts.get(str(row['_id']), 0) + row['n']
    return counts


def unorganized_concepts(limit: int = 50, offset: int = 0) -> tuple:
    """Unorganized concepts, most used first (then name). Returns (page, total)."""
    concepts = list(db.tag_concepts_v2.find(
        _unorganized_filter(hierarchy_parent_ids()),
        {'_id': 1, 'display_name': 1, 'slug': 1, 'description': 1, 'created_at': 1, 'entity_type': 1}))
    counts = usage_counts()
    for c in concepts:
        c['usage_count'] = counts.get(str(c['_id']), 0)
    concepts.sort(key=lambda c: (-c['usage_count'], (c.get('display_name') or '').lower()))
    return concepts[offset:offset + limit], len(concepts)
