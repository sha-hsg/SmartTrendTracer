"""
Fast RAG API with progress feedback
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any
import json
import asyncio
import time

from app.services.rag_service_fast import get_rag_service, FastRAGService

router = APIRouter(prefix="/api/rag", tags=["rag"])

@router.get("/status")
    """Get current RAG index status"""
    service = get_rag_service(db)
    return service.get_status()

@router.post("/build")
async def build_index(
    force: bool = Query(False, description="Force rebuild even if index exists"),
) -> Dict[str, Any]:
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

@router.post("/search")
async def search_documents(
    query: str,
    k: int = Query(10, description="Number of results to return"),
) -> Dict[str, Any]:
    """Search documents using RAG"""
    service = get_rag_service(db)
    
    # Check if index is ready
    if not service.status.is_ready:
        if service.status.is_building:
            return {
                "error": "Index is currently building",
                "status": service.get_status()
            }
        else:
            # Auto-build if not ready
            service.build_index_async()
            return {
                "error": "Index not ready, building now. Please try again in a moment.",
                "status": service.get_status()
            }
    
    # Perform search
    results = service.search(query, k)
    
    return {
        "query": query,
        "results": results,
        "total": len(results),
        "index_status": {
            "documents": service.status.total_documents,
            "last_updated": service.status.last_updated.isoformat() if service.status.last_updated else None
        }
    }

@router.post("/ask")
async def ask_question(
    question: str,
    k: int = Query(10, description="Number of sources to consider"),
) -> Dict[str, Any]:
    """Ask a question and get an AI-generated answer with sources"""
    service = get_rag_service(db)
    
    # Check if index is ready
    if not service.status.is_ready:
        if service.status.is_building:
            return {
                "error": "Index is currently building",
                "status": service.get_status()
            }
        else:
            # Auto-build if not ready
            service.build_index_async()
            return {
                "error": "Index not ready, building now. Please try again in a moment.",
                "status": service.get_status()
            }
    
    # Get answer
    result = await service.search_with_answer(question, k)
    
    if "error" in result:
        return result
    
    # Format sources for frontend
    sources = []
    for source in result.get('sources', []):
        formatted_source = {
            'type': source['type'],
            'content': source['content'],
            'score': source['score'],
            'rank': source['rank']
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
        "question": question,
        "answer": result['answer'],
        "sources": sources,
        "total_sources": result.get('total_results', 0)
    }

@router.post("/rebuild")
    """Force rebuild the entire index from scratch"""
    service = get_rag_service(db)
    
    # Clear existing index
    service.index = None
    service.doc_map = {}
    service.metadata = {}
    service._update_status(is_ready=False)
    
    # Start rebuild
    result = service.build_index_async()
    return {
        **result,
        "message": "Force rebuild initiated"
    }