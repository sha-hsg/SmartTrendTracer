#!/usr/bin/env python
"""
Rebuild the RAG index for AI-powered search
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db
from app.services.rag_service_fast import get_rag_service

def rebuild_index():
    """Rebuild the RAG index from scratch"""
    print("🔄 Starting RAG index rebuild...")
    
    # Get database session
    db = next(get_db())
    
    # Get RAG service
    rag_service = get_rag_service(db)
    
    # Clear existing index
    print("🗑️  Clearing existing index...")
    rag_service.index = None
    rag_service.doc_map = {}
    rag_service.metadata = {}
    rag_service._update_status(is_ready=False)
    
    # Build new index
    print("🏗️  Building new index...")
    result = rag_service.build_index_async()
    
    if result.get('status') == 'building':
        print("✅ Index rebuild started successfully!")
        print(f"📊 Processing {result.get('total_documents', 0)} documents")
        print("\n⏳ The index is being built in the background.")
        print("   This may take a few minutes depending on the number of documents.")
        print("\n💡 You can use the search interface while the index is building,")
        print("   but results may be incomplete until it finishes.")
    else:
        print("❌ Failed to start index rebuild")
        print(f"   Error: {result.get('error', 'Unknown error')}")
    
    # Close database session
    db.close()

if __name__ == "__main__":
    rebuild_index()