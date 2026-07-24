"""
RAG API using MongoDB concepts for enhanced search
Replaces rag_simple.py with concept-aware search
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
import logging

from app.services.rag_service_concepts import ConceptBasedRAGService

router = APIRouter(tags=["rag-concepts"])
logger = logging.getLogger(__name__)

# Global RAG service instance
_rag_service = None

def get_rag_service() -> ConceptBasedRAGService:
    """Get or create RAG service instance"""
    global _rag_service
    if _rag_service is None:
        _rag_service = ConceptBasedRAGService()
    return _rag_service

class RAGQuery(BaseModel):
    """Model for RAG query request"""
    question: str
    k: int = 10
    use_concepts: bool = True
    concept_filter: Optional[List[str]] = None
    content_types: Optional[List[str]] = None  # Filter by ['tweet', 'article', 'paper']
    model: Optional[str] = None  # User-selected model for LLM generation

class RebuildRequest(BaseModel):
    """Model for rebuild request"""
    force: bool = False

@router.get("/stats")
async def get_index_stats():
    """Get statistics about the RAG index"""
    try:
        rag_service = get_rag_service()
        stats = rag_service.get_stats()
        
        return {
            "indexed_documents": stats.get('total_documents', 0),
            "is_ready": stats.get('status') == 'ready',
            "tweets": stats.get('tweets', 0),
            "articles": stats.get('articles', 0),
            "papers": stats.get('papers', 0),
            "last_updated": stats.get('last_updated'),
            "uses_concepts": stats.get('uses_concepts', True),
            "total_concepts": 0,  # Would need to query MongoDB for this
            "embedding_model": stats.get('embedding_model', 'all-MiniLM-L6-v2')
        }
    except Exception as e:
        logger.error(f"Error getting index stats: {e}")
        return {
            "indexed_documents": 0,
            "is_ready": False,
            "error": str(e)
        }

@router.get("/sample-questions")
async def get_sample_questions():
    """Get sample questions based on indexed content"""
    try:
        rag_service = get_rag_service()
        return rag_service.get_sample_questions()
    except Exception as e:
        logger.error(f"Error getting sample questions: {e}")
        # Return default questions
        return [
            "What are the latest developments in AI?",
            "What papers discuss transformer architectures?",
            "What are people saying about GPT models?",
            "Summarize recent articles about machine learning",
            "What are the key trends in AI research?",
            "What do the papers say about neural networks?",
            "Find discussions about AI safety and alignment",
            "What are the newest model architectures?"
        ]

@router.post("/ask")
async def ask_question(query: RAGQuery):
    """
    Ask a question and get an AI-generated answer with sources
    Enhanced with concept information
    """
    try:
        rag_service = get_rag_service()
        
        # Check if index exists
        stats = rag_service.get_stats()
        if stats.get('total_documents', 0) == 0:
            return {
                "question": query.question,
                "answer": "The search index is empty. Please rebuild the index first.",
                "sources": [],
                "concepts_used": [],
                "needs_rebuild": True
            }
        
        # Get answer with concept enhancement, concept filter and content type filtering
        result = rag_service.ask(
            question=query.question,
            k=query.k,
            use_concepts=query.use_concepts,
            concept_filter=query.concept_filter,
            content_types=query.content_types,
            model=query.model  # Pass user-selected model
        )

        # Pass through ALL fields from the service result (e.g. is_trend_analysis,
        # documents_analyzed, source_type — expected by RAGSearchModern.tsx)
        return {
            "question": query.question,
            "concepts_used": result.get('concepts_used', []),
            "total_sources": len(result.get('sources', [])),
            **result
        }

    except Exception as e:
        logger.error(f"Error answering question: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rebuild")
async def rebuild_index(
    request: RebuildRequest = RebuildRequest(),
):
    """
    Rebuild the RAG index with concept information
    """
    try:
        rag_service = get_rag_service()
        
        # Start rebuild
        logger.info("Starting RAG index rebuild with concepts...")
        result = rag_service.rebuild_index()
        
        return {
            "message": "Index rebuilt successfully with concept integration",
            "stats": result
        }
        
    except Exception as e:
        logger.error(f"Error rebuilding index: {e}")
        raise HTTPException(status_code=500, detail=str(e))
