"""
Shared utilities for the tag_ontology package (logger, id helpers).
Concept lookups live in app.repositories.tag_ontology_utils_queries.
"""
import logging


logger = logging.getLogger(__name__)


def concept_id_variants(concept) -> list:
    """All id representations under which references to this concept may be
    stored: the ObjectId, its string form, and the legacy custom "c_..." id."""
    oid = concept["_id"]
    variants = [oid, str(oid)]
    custom_id = concept.get("id")
    if custom_id and custom_id not in variants:
        variants.append(custom_id)
    return variants
