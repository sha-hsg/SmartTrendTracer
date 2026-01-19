#!/usr/bin/env python3
"""Test RAG answer generation"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.rag_service_fast import FastRAGService
from app.models import get_db

async def test_rag_answer():
    """Test RAG answer generation"""
    
    # Get database session
    db = next(get_db())
    
    # Initialize service
    print("Initializing RAG service...")
    rag_service = FastRAGService(db)
    
    # Check status
    status = rag_service.get_status()
    print(f"Index status: Ready={status['is_ready']}, Documents={status['total_documents']}")
    
    if not status['is_ready']:
        print("Index not ready, cannot test")
        return
    
    # Test query about ontology learning
    query = "tell me about the state of the art in ontology learning"
    print(f"\nQuery: {query}")
    print("-" * 50)
    
    # Get answer with sources
    result = await rag_service.search_with_answer(query, k=10)
    
    if 'error' in result:
        print(f"Error: {result['error']}")
    else:
        print(f"Answer:\n{result['answer']}\n")
        print(f"Number of sources: {result.get('total_results', 0)}")
        print("\nTop sources:")
        for i, source in enumerate(result.get('sources', [])[:3], 1):
            print(f"\n{i}. Type: {source['type']}, Score: {source['score']:.3f}")
            print(f"   Content: {source['content'][:200]}...")
            if source.get('metadata', {}).get('title'):
                print(f"   Title: {source['metadata']['title']}")

if __name__ == "__main__":
    asyncio.run(test_rag_answer())