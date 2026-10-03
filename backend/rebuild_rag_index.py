#!/usr/bin/env python
"""
Rebuild the RAG index for AI-powered search (MongoDB version)

Runs the full index build synchronously and only exits once the index
has been written to disk (data/rag_index_concepts/).

    venv/bin/python rebuild_rag_index.py                # full rebuild (~30 min, ~0.50 $)
    venv/bin/python rebuild_rag_index.py --incremental  # only new/changed content

The running backend keeps its loaded index; use POST /api/rag/update (or
restart the backend) so it sees a CLI update.
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


def update_index():
    """Embed only new and changed content and append it to the existing index"""
    print("🔄 Updating RAG index (incremental)...")
    try:
        result = ConceptBasedRAGService().update_index()
    except RuntimeError as e:
        print(f"❌ {e}")
        return 1
    print(f"✅ Added {result['added']}, updated {result['updated']}, "
          f"removed {result['removed']}, failed {result['failed']}")
    print(f"📊 Total documents: {result['total_documents']} "
          f"(tweets {result['tweets']}, articles {result['articles']}, papers {result['papers']})")
    return 0 if result['failed'] == 0 else 1


if __name__ == "__main__":
    sys.exit(update_index() if '--incremental' in sys.argv[1:] else rebuild_index())
