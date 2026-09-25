"""
Backwards-compatibility shim.
The real implementation lives in app.repositories.concepts.
"""

from app.repositories.concepts import ConceptOnlyTagService

__all__ = ["ConceptOnlyTagService"]
