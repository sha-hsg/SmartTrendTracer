#!/usr/bin/env python3
"""Test the RAG system by building index and running sample queries"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db
from app.services.rag_service import RAGService
import json

def test_rag_system():
    """Test the complete RAG system"""
    print("=" * 60)
    print("Testing RAG System")
    print("=" * 60)
    
    # Get database session
    db = next(get_db())
    
    # Initialize RAG service
    print("\n1. Initializing RAG service...")
    rag_service = RAGService(db)
    
    # Get stats
    print("\n2. Current index statistics:")
    stats = rag_service.get_stats()
    print(json.dumps(stats, indent=2))
    
    # Test search
    test_queries = [
        "What are the latest developments in GPT-5?",
        "Which articles talk about Claude?",
        "multimodal AI capabilities",
        "What did @sama tweet about?",
        "AI safety concerns"
    ]
    
    print("\n3. Testing search functionality:")
    for query in test_queries:
        print(f"\n   Query: '{query}'")
        results = rag_service.search(query, k=3)
        print(f"   Found {len(results)} results")
        for i, result in enumerate(results, 1):
            print(f"      {i}. {result.source_type}: {result.content[:100]}... (score: {result.score:.3f})")
    
    # Test question answering
    print("\n4. Testing question answering:")
    test_question = "Which articles discuss AI efficiency improvements?"
    print(f"   Question: {test_question}")
    
    answer = rag_service.answer_question(test_question, k=5)
    print(f"\n   Answer: {answer['answer'][:500]}...")
    print(f"\n   Sources found: {len(answer['sources'])}")
    for i, source in enumerate(answer['sources'][:3], 1):
        print(f"      {i}. {source['type']}: {source['display_title']}")
    
    print("\n5. RAG system test complete!")
    
    # Optionally rebuild index
    rebuild = input("\nDo you want to rebuild the index from scratch? (y/n): ")
    if rebuild.lower() == 'y':
        print("\nRebuilding index...")
        result = rag_service.rebuild_index()
        print(result['message'])

if __name__ == "__main__":
    test_rag_system()