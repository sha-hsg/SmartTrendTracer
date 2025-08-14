#!/usr/bin/env python3
"""Simple test to build RAG index with limited documents"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db
from app.services.rag_service import RAGService

def test_rag_simple():
    """Simple test to build the RAG index"""
    print("Building RAG index...")
    
    # Get database session
    db = next(get_db())
    
    # Initialize RAG service (this will build the index)
    try:
        rag_service = RAGService(db)
        
        # Get stats
        stats = rag_service.get_stats()
        print(f"\nIndex built successfully!")
        print(f"Total documents: {stats['total_documents']}")
        print(f"Documents by type: {stats['documents_by_type']}")
        
        # Test a simple search
        print("\nTesting search for 'AI'...")
        results = rag_service.search("AI", k=3)
        print(f"Found {len(results)} results")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_rag_simple()