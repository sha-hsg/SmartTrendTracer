"""
Simple RAG API endpoints that actually work
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List, Optional
from pydantic import BaseModel
import datetime

from app.services.rag_service_fast import get_rag_service
from app.database.mongodb import get_database

router = APIRouter()


class RAGQuery(BaseModel):
    """Model for RAG query request"""
    question: str
    k: int = 10
    content_types: Optional[List[str]] = None  # ['tweet', 'article', 'paper']
    model: Optional[str] = None  # Optional model override


@router.get("/stats")
def get_index_stats(db=Depends(get_database)):
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
            "error": status.get('error'),
            # Document type counts for filtering UI
            "tweets": status.get('tweets', 0),
            "articles": status.get('articles', 0),
            "papers": status.get('papers', 0),
            "snippets": status.get('snippets', 0)
        }
    except Exception as e:
        print(f"Error in get_index_stats: {e}")
        return {
            "indexed_documents": 0,
            "is_ready": False,
            "is_building": False,
            "last_updated": None,
            "current_step": '',
            "progress_percent": 0,
            "error": str(e),
            "tweets": 0,
            "articles": 0,
            "papers": 0,
            "snippets": 0
        }


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


@router.post("/ask")
async def ask_question(query: RAGQuery, db=Depends(get_database)):
    """
    Ask a question and get an AI-generated answer with sources.
    """
    try:
        rag_service = get_rag_service(db)

        # Check if index is ready
        if not rag_service.status.is_ready:
            # Try to build index
            rag_service.build_index_async()
            return {
                "question": query.question,
                "answer": "The search index is being built. Please try again in a moment.",
                "sources": [],
                "total_sources": 0,
                "index_stats": {
                    "total_documents": 0,
                    "last_updated": None
                }
            }

        # Get answer with sources (with optional content type filtering)
        result = await rag_service.search_with_answer(query.question, query.k, query.content_types)

        if "error" in result:
            # If there's an error, return a simple search instead
            search_results = rag_service.search(query.question, query.k, query.content_types)
            return {
                "question": query.question,
                "answer": f"Found {len(search_results)} relevant documents. Please review them below.",
                "sources": search_results[:10],
                "total_sources": len(search_results),
                "index_stats": {
                    "total_documents": rag_service.status.total_documents,
                    "last_updated": rag_service.status.last_updated.isoformat() if rag_service.status.last_updated else None
                }
            }

        return {
            "question": query.question,
            "answer": result.get('answer', 'No answer generated'),
            "sources": result.get('sources', [])[:10],
            "total_sources": result.get('total_results', 0),
            "index_stats": {
                "total_documents": rag_service.status.total_documents,
                "last_updated": rag_service.status.last_updated.isoformat() if rag_service.status.last_updated else None
            }
        }

    except Exception as e:
        import traceback
        print(f"Error in ask_question: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return {
            "question": query.question,
            "answer": f"An error occurred while processing your question: {str(e)}",
            "sources": [],
            "total_sources": 0,
            "index_stats": {
                "total_documents": 0,
                "last_updated": None
            }
        }


@router.post("/rebuild")
def rebuild_index(db=Depends(get_database)):
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
            "status": "rebuilding",
            "message": "Index rebuild started successfully!",
            "total_documents": result.get('total_documents', 0)
        }

    except Exception as e:
        print(f"Error in rebuild_index: {e}")
        return {
            "status": "error",
            "message": f"Failed to rebuild index: {str(e)}",
            "total_documents": 0
        }
