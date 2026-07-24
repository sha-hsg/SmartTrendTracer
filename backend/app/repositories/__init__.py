"""Data-access layer for SmartTrendTracer.

This package provides a clean import surface for the most commonly shared
data-access utilities.  Rather than introducing redundant wrapper classes
around simple one-liner MongoDB calls, we re-export the existing services
and helpers that already centralise database operations:

* ``safe_object_id`` – consistent ObjectId conversion (replaces 6+ ad-hoc
  patterns scattered across services).
* ``ConceptOnlyTagService`` – singleton concept/tag repository with
  ``get_concept_by_id``, ``get_concepts_by_ids``, ``get_tags_for_content``,
  ``get_instances_by_concept_id``, ``get_tagged_content_ids``, etc.
* ``get_database`` – the shared MongoDB database handle.

Content-specific operations (papers, tweets, articles) are already
centralised in their respective API packages under ``app/api/``.
"""

from app.database.mongodb import get_database, safe_object_id
from app.services.concept_only_tag_service import ConceptOnlyTagService

__all__ = [
    "get_database",
    "safe_object_id",
    "ConceptOnlyTagService",
]
