#!/usr/bin/env python3
"""Quick rebuild of RAG index with papers included"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db
from app.models.papers import Paper
import time

def quick_check_and_rebuild():
    """Check if papers need to be added to index"""
    
    db = next(get_db())
    
    # Check papers in database
    paper_count = db.query(Paper).count()
    print(f"Papers in database: {paper_count}")
    
    if paper_count == 0:
        print("No papers to index")
        return
    
    # Check current index
    metadata_path = "data/rag_index/metadata.pkl"
    if os.path.exists(metadata_path):
        import pickle
        with open(metadata_path, 'rb') as f:
            metadata = pickle.load(f)
        
        # Count paper entries
        paper_entries = sum(1 for doc_id in metadata.keys() if 'paper' in doc_id)
        print(f"Papers in current index: {paper_entries}")
        
        if paper_entries > 0:
            print("✅ Papers are already in the index!")
            return
    
    print("\n⚠️ Papers not in index. Need to rebuild.")
    print("Please run one of these commands:")
    print("  1. If server is running: curl -X POST http://localhost:8000/api/rag/rebuild")
    print("  2. Or start server and use AI Search to trigger rebuild")
    print("  3. Or wait for the background build to complete")
    
    db.close()

if __name__ == "__main__":
    quick_check_and_rebuild()