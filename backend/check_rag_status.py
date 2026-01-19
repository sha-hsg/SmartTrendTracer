#!/usr/bin/env python3
"""
Check RAG service status
"""
from app.services.rag_service_fast import FastRAGService
from app.models import SessionLocal

def check_status():
    """Check RAG service status"""
    
    # Initialize service
    db = SessionLocal()
    rag = FastRAGService(db)
    
    print("="*60)
    print("RAG SERVICE STATUS")
    print("="*60)
    
    status = rag.get_status()
    
    for key, value in status.items():
        print(f"{key}: {value}")
    
    print("\n" + "-"*40)
    
    # Check index directly
    if rag.index is not None:
        print(f"FAISS index size: {rag.index.ntotal}")
    else:
        print("FAISS index: Not loaded")
    
    if rag.doc_map:
        print(f"Doc map entries: {len(rag.doc_map)}")
    else:
        print("Doc map: Empty")
    
    if rag.metadata:
        print(f"Metadata entries: {len(rag.metadata)}")
    else:
        print("Metadata: Empty")
    
    db.close()
    print("="*60)

if __name__ == "__main__":
    check_status()