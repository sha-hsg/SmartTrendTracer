"""
Backwards-compatible shim — real implementation lives in app.services.rag
"""
from app.services.rag import ConceptBasedRAGService

__all__ = ['ConceptBasedRAGService']
