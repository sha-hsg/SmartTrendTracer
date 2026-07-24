#!/usr/bin/env python
"""
Rebuild the RAG index for AI-powered search (MongoDB version)

Runs the full index build synchronously and only exits once the index
has been written to disk (data/rag_index_concepts/).
"""
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)
# The RAG service uses a relative index path (data/rag_index_concepts),
# so make sure we run from the backend directory regardless of CWD.
os.chdir(SCRIPT_DIR)

from app.services.rag_service_concepts import ConceptBasedRAGService


def rebuild_index():
    """Rebuild the RAG index from scratch (synchronous, blocks until done)"""
    print("🔄 Starting RAG index rebuild (MongoDB)...")

    # Get RAG service
    rag_service = ConceptBasedRAGService()

    # Build new index synchronously — this blocks until the index
    # is fully built and persisted to disk.
    print("🏗️  Building new index (this may take a few minutes)...")
    index_info = rag_service.rebuild_index()

    total_docs = index_info.get('total_documents', 0)
    if index_info.get('status') == 'ready' and total_docs > 0:
        print("✅ Index rebuilt successfully!")
        print(f"📊 Total documents: {total_docs}")
        print(f"   Tweets:   {index_info.get('tweets', 0)}")
        print(f"   Articles: {index_info.get('articles', 0)}")
        print(f"   Papers:   {index_info.get('papers', 0)}")
        print(f"   Embedding model: {index_info.get('embedding_model', 'unknown')}")
        return 0

    print("❌ Index rebuild produced no usable index")
    print(f"   Result: {index_info}")
    return 1


if __name__ == "__main__":
    sys.exit(rebuild_index())
