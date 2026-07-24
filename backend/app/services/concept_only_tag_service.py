"""
Backwards-compatibility shim.
The real implementation lives in app.services.concept_tag.
"""

from app.services.concept_tag.service import ConceptOnlyTagService

__all__ = ["ConceptOnlyTagService"]
