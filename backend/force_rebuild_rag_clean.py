#!/usr/bin/env python3
"""
Force a clean rebuild of the RAG index, removing old Document object format
"""
import os
import shutil
from app.models import SessionLocal
from app.services.rag_service_fast import FastRAGService

def force_clean_rebuild():
    """Force a complete rebuild of the RAG index"""
    
    print("="*60)
    print("FORCE CLEAN RAG INDEX REBUILD")
    print("="*60)
    
    # Backup and remove old index
    index_dir = 'data/rag_index'
    backup_dir = 'data/rag_index_backup_old_format'
    
    if os.path.exists(index_dir):
        print(f"1. Backing up old index to {backup_dir}...")
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)
        shutil.move(index_dir, backup_dir)
        print("   ✅ Old index backed up")
    
    # Create fresh index directory
    os.makedirs(index_dir, exist_ok=True)
    print("2. Created fresh index directory")
    
    # Initialize database
    db = SessionLocal()
    
    try:
        # Create new RAG service (this will trigger a rebuild)
        print("3. Initializing RAG service...")
        rag_service = FastRAGService(db)
        
        # Check if it needs rebuilding (it should since we deleted the index)
        if rag_service.needs_rebuild():
            print("4. Starting index rebuild...")
            result = rag_service.build_index_async()
            print(f"   Result: {result}")
            
            # Wait for completion
            import time
            max_wait = 300  # 5 minutes
            start_time = time.time()
            
            while not rag_service.status.is_ready and (time.time() - start_time) < max_wait:
                status = rag_service.get_status()
                print(f"   Progress: {status['progress_percent']}% - {status['current_step']}")
                time.sleep(5)
            
            if rag_service.status.is_ready:
                print("✅ Index rebuild complete!")
                status = rag_service.get_status()
                print(f"   Total documents: {status['total_documents']}")
                print(f"   Index ready: {status['is_ready']}")
            else:
                print("❌ Index rebuild timed out or failed")
                print(f"   Error: {rag_service.status.error}")
        else:
            print("4. Index doesn't need rebuilding (this is unexpected)")
            
    finally:
        db.close()
    
    print("="*60)
    print("Clean rebuild process complete!")
    print("The RAG index has been rebuilt from scratch.")
    print("="*60)

if __name__ == "__main__":
    force_clean_rebuild()