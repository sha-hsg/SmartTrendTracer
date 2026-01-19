#!/usr/bin/env python3
"""
Test RAG query to verify it's working correctly
"""
from app.services.rag_service_fast import FastRAGService
from app.models import SessionLocal
import asyncio

async def test_rag():
    """Test RAG with a simple query"""
    
    # Initialize service
    db = SessionLocal()
    rag = FastRAGService(db)
    
    # Test query
    query = "What are the latest updates to ChatGPT?"
    
    print("="*60)
    print("TESTING RAG QUERY")
    print("="*60)
    print(f"Query: {query}")
    print("-"*40)
    
    # Get search results first
    search_results = rag.search(query, k=3)
    
    if search_results:
        print(f"\nFound {len(search_results)} search results:")
        for i, result in enumerate(search_results, 1):
            print(f"\n--- Result {i} ---")
            print(f"Keys in result: {list(result.keys())}")
            print(f"Type: {result.get('type', 'N/A')}")
            print(f"Score: {result.get('score', 0):.3f}")
            content = result.get('content', '')
            if content:
                print(f"Content: {content[:200]}...")
            else:
                print("Content: (empty)")
    else:
        print("No search results found")
    
    # Now test with answer generation
    print("\n" + "="*60)
    print("TESTING WITH ANSWER GENERATION")
    print("-"*40)
    
    response = await rag.search_with_answer(query, k=5)
    
    if 'error' in response:
        print(f"Error: {response['error']}")
    else:
        print(f"Answer:\n{response.get('answer', 'No answer generated')}")
        print(f"\nSources used: {response.get('total_results', 0)}")
        
        if response.get('sources'):
            print("\nSource excerpts:")
            for i, source in enumerate(response['sources'][:3], 1):
                print(f"\n{i}. [{source['type']}]: {source['content'][:100]}...")
    
    db.close()
    print("\n" + "="*60)

if __name__ == "__main__":
    asyncio.run(test_rag())