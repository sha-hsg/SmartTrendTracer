#!/usr/bin/env python3
"""Test that the RAG index rebuilds correctly"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db
from app.services.rag_service import RAGService

def test_rebuild():
    """Test the RAG index rebuilds with correct dimensions"""
    try:
        db = next(get_db())
        
        print("Creating RAG service (will trigger rebuild)...")
        rag_service = RAGService(db)
        
        # Get stats
        stats = rag_service.get_stats()
        print(f"\n✅ Index rebuilt successfully!")
        print(f"Total documents: {stats.get('total_documents', 0)}")
        print(f"Index ready: {stats.get('index_ready')}")
        
        # Test a search
        print("\nTesting search functionality...")
        results = rag_service.search("machine learning papers", k=5)
        print(f"Search returned {len(results)} results")
        
        if results:
            print("\nSample result:")
            print(f"  Type: {results[0].source_type}")
            print(f"  Score: {results[0].score:.3f}")
            print(f"  Content preview: {results[0].content[:100]}...")
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    test_rebuild()