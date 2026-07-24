#!/usr/bin/env python3
"""Clear the RAG index to force rebuild with correct dimensions"""

import os
import shutil
from datetime import datetime

def clear_index():
    """Clear the RAG index"""
    index_dir = "data/rag_index"
    
    if os.path.exists(index_dir):
        # Backup first
        backup_dir = f"data/rag_index_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"Backing up old index to {backup_dir}")
        shutil.copytree(index_dir, backup_dir)
        
        # Remove the old index
        print(f"Removing old index from {index_dir}")
        shutil.rmtree(index_dir)
        print("✅ Index cleared successfully")
        print("The index will be rebuilt automatically on next use with correct dimensions (1536)")
    else:
        print("No index found to clear")

if __name__ == "__main__":
    clear_index()