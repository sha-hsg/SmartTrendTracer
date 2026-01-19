#!/usr/bin/env python3
"""Rebuild the RAG index to include papers"""

import sys
import os
import shutil
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db, Paper
from app.services.rag_service_fast import FastRAGService

def rebuild_with_papers():
    """Rebuild the RAG index including papers"""
    try:
        db = next(get_db())
        
        # Check how many papers we have
        paper_count = db.query(Paper).count()
        print(f"Papers in database: {paper_count}")
        
        if paper_count == 0:
            print("⚠️ No papers in database to index")
            return
        
        # Backup current index
        index_dir = "data/rag_index"
        if os.path.exists(index_dir):
            backup_dir = f"data/rag_index_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            print(f"Backing up current index to {backup_dir}")
            shutil.copytree(index_dir, backup_dir)
        
        # Force rebuild using the fast service (which includes papers)
        print("\nRebuilding index with papers...")
        print("This will include:")
        print("  - Tweets")
        print("  - Articles") 
        print("  - Papers")
        print("  - Snippets")
        
        # Use the FastRAGService which is configured to use Gemini
        rag_service = FastRAGService(db)
        
        # Force a rebuild
        result = await rag_service.rebuild_index()
        
        if result.get('success'):
            print(f"\n✅ Index rebuilt successfully!")
            stats = result.get('stats', {})
            print(f"Documents indexed:")
            print(f"  - Tweets: {stats.get('tweets', 0)}")
            print(f"  - Articles: {stats.get('articles', 0)}")
            print(f"  - Papers: {stats.get('papers', 0)}")
            print(f"  - Snippets: {stats.get('snippets', 0)}")
            print(f"  - Total: {stats.get('total', 0)}")
        else:
            print(f"\n❌ Failed to rebuild: {result.get('error')}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    # Run the async function
    import asyncio
    asyncio.run(rebuild_with_papers())