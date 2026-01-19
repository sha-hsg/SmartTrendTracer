#!/usr/bin/env python3
"""Force rebuild the RAG index to fix corruption issues"""

import os
import sys
import shutil

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.rag_service_fast import FastRAGService
from app.models import get_db

def force_rebuild():
    """Force rebuild the RAG index"""
    
    # Remove existing index files
    index_dir = "data/rag_index"
    if os.path.exists(index_dir):
        print(f"Removing existing index directory: {index_dir}")
        shutil.rmtree(index_dir)
        os.makedirs(index_dir)
    
    # Get database session
    db = next(get_db())
    
    # Initialize service
    print("Initializing RAG service...")
    rag_service = FastRAGService(db)
    
    # Force rebuild
    print("Starting index rebuild...")
    result = rag_service.build_index_async()
    print(f"Rebuild result: {result}")
    
    # Wait for completion
    import time
    while rag_service.status.is_building:
        status = rag_service.get_status()
        print(f"Progress: {status['progress_percent']}% - {status['current_step']}")
        time.sleep(2)
    
    # Final status
    final_status = rag_service.get_status()
    if final_status['is_ready']:
        print(f"✅ Index rebuilt successfully with {final_status['total_documents']} documents")
    else:
        print(f"❌ Index rebuild failed: {final_status.get('error', 'Unknown error')}")

if __name__ == "__main__":
    force_rebuild()