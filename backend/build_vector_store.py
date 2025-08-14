#!/usr/bin/env python3
"""
Build vector store from existing database tags
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.vector_store_openai import get_vector_store
from app.models import get_db

load_dotenv()

def main():
    """Build vector store from database"""
    print("=" * 60)
    print("Building Tag Vector Store")
    print("=" * 60)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Get vector store
        vector_store = get_vector_store()
        
        # Build from database
        vector_store.build_from_database(db)
        
        print("\n✅ Vector store built successfully!")
        
        # Test search
        print("\n" + "=" * 60)
        print("Testing Vector Store Search")
        print("=" * 60)
        
        test_queries = [
            "OpenAI GPT model announcement",
            "machine learning research paper",
            "artificial intelligence ethics",
            "hugging face open source",
            "breaking news AI development"
        ]
        
        for query in test_queries:
            print(f"\nQuery: '{query}'")
            results = vector_store.search_similar_tags(query, k=5)
            
            if results:
                print("Similar tags:")
                for tag, score, count in results:
                    print(f"  - {tag:<30} (score: {score:.3f}, used: {count}x)")
            else:
                print("  No similar tags found")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()