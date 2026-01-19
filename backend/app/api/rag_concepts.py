"""
RAG API using MongoDB concepts for enhanced search
Replaces rag_simple.py with concept-aware search
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional
from pydantic import BaseModel
import logging

from app.services.rag_service_concepts import ConceptBasedRAGService
from app.services.concept_only_tag_service import ConceptOnlyTagService

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
        
        # Get answer with concept enhancement and content type filtering
        result = rag_service.ask(
            question=query.question,
            k=query.k,
            use_concepts=query.use_concepts,
            content_types=query.content_types,
            model=query.model  # Pass user-selected model
        )
        
        return {
            "question": query.question,
            "answer": result['answer'],
            "sources": result['sources'],
            "concepts_used": result.get('concepts_used', []),
            "total_sources": len(result['sources'])
        }
        
    except Exception as e:
        logger.error(f"Error answering question: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search")
async def search_documents(
    query: str = Query(..., description="Search query"),
    k: int = Query(10, description="Number of results"),
    concept_filter: Optional[List[str]] = Query(None, description="Filter by concept IDs"),
    content_types: Optional[List[str]] = Query(None, description="Filter by content types (tweet, article, paper)"),
):
    """
    Search documents with optional concept and content type filtering
    """
    try:
        rag_service = get_rag_service()
        
        results = rag_service.search(
            query=query,
            k=k,
            concept_filter=concept_filter,
            content_types=content_types
        )
        
        return {
            "query": query,
            "results": results,
            "total": len(results),
            "filtered_by_concepts": concept_filter is not None,
            "filtered_by_types": content_types is not None
        }
        
    except Exception as e:
        logger.error(f"Error searching: {e}")
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

@router.get("/concepts/top")
async def get_top_concepts_in_index(
    limit: int = Query(20, description="Number of top concepts to return"),
):
    """
    Get the most frequently used concepts in the indexed documents
    """
    try:
        concept_service = ConceptOnlyTagService()
        
        # Get top concepts across all content types
        all_concepts = []
        
        for content_type in ['tweet', 'article', 'paper']:
            concepts = concept_service.get_all_concepts_with_counts(content_type=content_type)
            all_concepts.extend(concepts)
        
        # Aggregate and sort
        concept_map = {}
        for concept in all_concepts:
            slug = concept['slug']
            if slug not in concept_map:
                concept_map[slug] = {
                    'slug': slug,
                    'display_name': concept.get('display_name', slug),
                    'count': 0,
                    'content_types': []
                }
            concept_map[slug]['count'] += concept['count']
            if content_type not in concept_map[slug]['content_types']:
                concept_map[slug]['content_types'].append(content_type)
        
        # Sort by count and return top N
        sorted_concepts = sorted(
            concept_map.values(),
            key=lambda x: x['count'],
            reverse=True
        )[:limit]
        
        return sorted_concepts
        
    except Exception as e:
        logger.error(f"Error getting top concepts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Check if RAG service is healthy"""
    try:
        rag_service = get_rag_service()
        stats = rag_service.get_stats()
        
        return {
            "status": "healthy" if stats.get('total_documents', 0) > 0 else "needs_rebuild",
            "indexed_documents": stats.get('total_documents', 0),
            "uses_concepts": True
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }