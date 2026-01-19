#!/usr/bin/env python
"""
Rebuild the RAG index for AI-powered search (MongoDB version)
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.rag_service_concepts import ConceptBasedRAGService

def rebuild_index():
    """Rebuild the RAG index from scratch"""
    print("🔄 Starting RAG index rebuild (MongoDB)...")
    
    # Get RAG service
    rag_service = ConceptBasedRAGService()
    
    # Clear existing index
    print("🗑️  Clearing existing index...")
    rag_service.index = None
    rag_service.doc_map = {}
    rag_service.metadata = {}
    rag_service._update_status(is_ready=False)
    
    # Build new index
    print("🏗️  Building new index...")
    result = rag_service.build_index_async()
    
    if result.get('status') in ['building', 'started']:
        print("✅ Index rebuild started successfully!")
        
        # Get document count from the status
        status = rag_service.get_status()
        total_docs = status.get('total_documents', 0)
        
        print(f"📊 Processing {total_docs} documents")
        print("\n⏳ The index is being built in the background.")
        print("   This may take a few minutes depending on the number of documents.")
        print("\n💡 You can use the search interface while the index is building,")
        print("   but results may be incomplete until it finishes.")
    elif result.get('status') == 'already_building':
        print("⚠️  Index rebuild is already in progress")
        print(f"   Progress: {result.get('progress', 0)}%")
    else:
        print("❌ Failed to start index rebuild")
        print(f"   Status: {result.get('status', 'Unknown')}")
        print(f"   Error: {result.get('error', result.get('message', 'Unknown error'))}")
    
    # Close database session
    db.close()

if __name__ == "__main__":
    rebuild_index()