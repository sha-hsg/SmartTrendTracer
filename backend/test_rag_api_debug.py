#!/usr/bin/env python3
"""Debug the RAG API to see why sources are empty"""

import asyncio
from app.api.rag_simple import ask_question, RAGQuery
from app.models import get_db
import json

async def test_api():
    # Get a database session
    db = next(get_db())
    
    # Create a query
    query = RAGQuery(question="What are the latest AI papers?", k=5)
    
    # Call the API function directly
    result = await ask_question(query, db)
    
    print("API Response:")
    print(f"Question: {result['question']}")
    print(f"Answer length: {len(result.get('answer', ''))}")
    print(f"Number of sources: {len(result.get('sources', []))}")
    
    if result.get('sources'):
        print("\nSource Analysis:")
        for i, source in enumerate(result['sources'][:3], 1):
            print(f"\nSource {i}:")
            print(f"  Type: {type(source)}")
            if isinstance(source, dict):
                print(f"  Keys: {source.keys()}")
                print(f"  Content type: {source.get('type', 'missing')}")
                print(f"  Content length: {len(source.get('content', ''))}")
                print(f"  Content preview: {source.get('content', '')[:50]}...")
            else:
                print(f"  Value: {source}")
    
    # Save full response for inspection
    with open('/tmp/rag_api_response.json', 'w') as f:
        json.dump(result, f, indent=2, default=str)
    print("\nFull response saved to /tmp/rag_api_response.json")

if __name__ == "__main__":
    asyncio.run(test_api())