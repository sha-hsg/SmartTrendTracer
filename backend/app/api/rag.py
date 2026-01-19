"""
API endpoints for RAG (Retrieval-Augmented Generation) system
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Dict, List, Optional
from pydantic import BaseModel
import json
import asyncio

from app.services.rag_service_fast import get_rag_service, FastRAGService

router = APIRouter()

class RAGQuery(BaseModel):
    """Model for RAG query request"""
    question: str
    k: int = 5  # Number of sources to retrieve
    filter_type: Optional[str] = None  # 'tweet', 'article', 'snippet', or None for all

class SearchQuery(BaseModel):
    """Model for search query request"""
    query: str
    k: int = 10
    filter_type: Optional[str] = None

@router.get("/status")
    """Get current RAG index status"""
    service = get_rag_service(db)
    return service.get_status()

@router.post("/build")
async def build_index(
    force: bool = Query(False, description="Force rebuild even if index exists"),
):
    """Build or rebuild the RAG index"""
    service = get_rag_service(db)
    
    # Check if rebuild is needed
    if not force and service.status.is_ready and not service.needs_rebuild():
        return {
            "status": "ready",
            "message": "Index is up to date",
            "documents": service.status.total_documents
        }
    
    # Start building in background
    result = service.build_index_async()
    return result

@router.get("/build/progress")
    """Stream build progress updates via Server-Sent Events"""
    async def generate():
        service = get_rag_service(db)
        last_status = None
        
        while True:
            current_status = service.get_status()
            
            # Only send if status changed
            if current_status != last_status:
                # Format as SSE
                data = json.dumps(current_status)
                yield f"data: {data}\n\n"
                last_status = current_status
            
            # Stop if build is complete or failed
            if not current_status['is_building']:
                if current_status['is_ready'] or current_status['error']:
                    break
            
            await asyncio.sleep(0.5)  # Check every 500ms
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )

@router.post("/ask")
async def ask_question(
    query: RAGQuery,
):
    """
    Ask a question and get an AI-generated answer with sources.
    
    Supports questions like:
    - "What are the latest developments in GPT-5?"
    - "Which articles talk about Claude?"
    - "What did @sama tweet about AI safety?"
    - "Show me discussions about multimodal AI"
    """
    try:
        rag_service = get_rag_service(db)
        
        # Auto-build index if not ready
        if not rag_service.status.is_ready:
            if rag_service.status.is_building:
                return {
                    "error": "Index is currently building. Please wait.",
                    "status": rag_service.get_status()
                }
            else:
                rag_service.build_index_async()
                return {
                    "error": "Index not ready. Building now, please try again in a moment.",
                    "status": rag_service.get_status()
                }
        
        # Check if this is a "which article/tweet" type question
        question_lower = query.question.lower()
        is_article_search = any(phrase in question_lower for phrase in [
            "which article", "what article", "which post", "what post",
            "find article", "show article", "list article"
        ])
        is_tweet_search = any(phrase in question_lower for phrase in [
            "which tweet", "what tweet", "who tweet", "find tweet",
            "show tweet", "list tweet", "what did", "who said"
        ])
        
        # Set filter type based on question if not specified
        if not query.filter_type:
            if is_article_search:
                query.filter_type = 'article'
            elif is_tweet_search:
                query.filter_type = 'tweet'
        
        # Get answer with sources
        result = await rag_service.search_with_answer(query.question, query.k)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Format sources for frontend
        sources = []
        for source in result.get('sources', []):
            formatted_source = {
                'type': source['type'],
                'content': source['content'],
                'score': source['score'],
                'rank': source.get('rank', 0)
            }
            
            # Add type-specific fields
            if source['type'] == 'tweet':
                formatted_source.update({
                    'author': source['metadata'].get('author'),
                    'url': source['metadata'].get('url'),
                    'created_at': source['metadata'].get('created_at'),
                    'tags': source['metadata'].get('tags', [])
                })
            elif source['type'] == 'article':
                formatted_source.update({
                    'title': source['metadata'].get('title'),
                    'author': source['metadata'].get('author'),
                    'url': source['metadata'].get('url'),
                    'published_at': source['metadata'].get('published_at')
                })
            elif source['type'] == 'snippet':
                formatted_source.update({
                    'category': source['metadata'].get('category'),
                    'article_id': source['metadata'].get('article_id')
                })
            
            sources.append(formatted_source)
        
        return {
            "question": query.question,
            "answer": result.get('answer', 'No answer generated'),
            "sources": sources,
            "total_sources": result.get('total_results', 0),
            "index_stats": {
                "total_documents": rag_service.status.total_documents,
                "last_updated": rag_service.status.last_updated.isoformat() if rag_service.status.last_updated else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in ask_question: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search")
async def search_documents(
    query: SearchQuery,
):
    """
    Search documents without generating an answer.
    Returns raw search results for browsing.
    """
    try:
        rag_service = get_rag_service(db)
        
        # Check if index is ready
        if not rag_service.status.is_ready:
            if rag_service.status.is_building:
                return {
                    "error": "Index is currently building",
                    "status": rag_service.get_status()
                }
            else:
                # Auto-build if not ready
                rag_service.build_index_async()
                return {
                    "error": "Index not ready, building now. Please try again in a moment.",
                    "status": rag_service.get_status()
                }
        
        # Perform search
        results = rag_service.search(query.query, query.k)
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_result = {
                'type': result.get('type'),
                'content': result.get('content'),
                'score': result.get('score'),
                'rank': result.get('rank')
            }
            
            metadata = result.get('metadata', {})
            if result.get('type') == 'tweet':
                formatted_result.update({
                    'author': metadata.get('author'),
                    'url': metadata.get('url'),
                    'created_at': metadata.get('created_at'),
                    'tags': metadata.get('tags', [])
                })
            elif result.get('type') == 'article':
                formatted_result.update({
                    'title': metadata.get('title'),
                    'author': metadata.get('author'),
                    'url': metadata.get('url'),
                    'published_at': metadata.get('published_at')
                })
            
            formatted_results.append(formatted_result)
        
        return {
            "query": query.query,
            "results": formatted_results,
            "total": len(formatted_results)
        }
        
    except Exception as e:
        print(f"Error in search_documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
    """Get statistics about the RAG index"""
    try:
        rag_service = get_rag_service(db)
        status = rag_service.get_status()
        
        return {
            "indexed_documents": status.get('total_documents', 0),
            "is_ready": status.get('is_ready', False),
            "is_building": status.get('is_building', False),
            "last_updated": status.get('last_updated'),
            "current_step": status.get('current_step', ''),
            "progress_percent": status.get('progress_percent', 0),
            "error": status.get('error')
        }
        
    except Exception as e:
        print(f"Error in get_index_stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sample-questions")
def get_sample_questions():
    """Get sample questions for the RAG interface"""
    return [
        "What are the latest developments in AI agents?",
        "Which articles discuss Claude and Anthropic?",
        "What did Sam Altman tweet about GPT-5?",
        "Show me discussions about multimodal AI",
        "What are the key trends in machine learning?",
        "Which newsletters talk about AI safety?",
        "Find tweets about open source LLMs",
        "What are people saying about AI regulation?",
        "What are the most discussed AI models recently?",
        "Which tweets mention breakthrough research?",
        "What are the emerging topics in deep learning?",
        "Show me content about AI consciousness debates"
    ]

@router.post("/rebuild")
    """Force rebuild the entire index from scratch"""
    try:
        rag_service = get_rag_service(db)
        
        # Clear existing index
        rag_service.index = None
        rag_service.doc_map = {}
        rag_service.metadata = {}
        rag_service._update_status(is_ready=False)
        
        # Start rebuild
        result = rag_service.build_index_async()
        return {
            **result,
            "message": "Force rebuild initiated"
        }
        
    except Exception as e:
        print(f"Error in rebuild_index: {e}")
        raise HTTPException(status_code=500, detail=str(e))