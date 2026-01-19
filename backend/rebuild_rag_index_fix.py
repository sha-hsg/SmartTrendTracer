#!/usr/bin/env python3
"""Rebuild the RAG index with correct dimensions"""

import os
import sys
import shutil
from datetime import datetime

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db
from app.services.rag_service import RAGService

def backup_old_index():
    """Backup the old index before rebuilding"""
    index_dir = "data/rag_index"
    if os.path.exists(index_dir):
        backup_dir = f"data/rag_index_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"Backing up old index to {backup_dir}")
        shutil.copytree(index_dir, backup_dir)
        print("Backup complete")

def rebuild_index():
    """Rebuild the RAG index"""
    try:
        # Backup old index first
        backup_old_index()
        
        # Clear the existing index directory
        index_dir = "data/rag_index"
        if os.path.exists(index_dir):
            print(f"Removing old index from {index_dir}")
            shutil.rmtree(index_dir)
        
        # Create fresh directory
        os.makedirs(index_dir, exist_ok=True)
        
        # Get database session
        db = next(get_db())
        
        # Create new RAG service (this will trigger index building)
        print("Building new RAG index with OpenAI text-embedding-ada-002 (1536 dimensions)...")
        rag_service = RAGService(db)
        
        # Force rebuild
        result = rag_service.rebuild_index()
        
        if result.get('success'):
            print(f"\n✅ Index rebuilt successfully!")
            print(f"Total documents indexed: {result.get('total_documents', 0)}")
            stats = result.get('stats', {})
            print(f"  - Tweets: {stats.get('tweets', 0)}")
            print(f"  - Articles: {stats.get('articles', 0)}")
            print(f"  - Papers: {stats.get('papers', 0)}")
            print(f"  - Snippets: {stats.get('snippets', 0)}")
        else:
            print(f"\n❌ Failed to rebuild index: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"\n❌ Error rebuilding index: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    rebuild_index()