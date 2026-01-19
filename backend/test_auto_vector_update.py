#!/usr/bin/env python3
"""
Test script to verify automatic vector store updates when tags are added
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from app.services.vector_store_openai import get_vector_store
from app.models import get_db

def test_vector_store_auto_update():
    """Test that vector store updates automatically when tags are added"""
    
    print("=" * 60)
    print("Testing Automatic Vector Store Updates")
    print("=" * 60)
    
    # Get vector store
    vector_store = get_vector_store()
    
    # Check current status
    print(f"\nCurrent vector store status:")
    print(f"- Total tags indexed: {len(vector_store.tag_to_id)}")
    
    # Test incremental update
    print("\n" + "=" * 60)
    print("Testing Incremental Update")
    print("=" * 60)
    
    test_tag = "test-auto-update-tag"
    test_context = "This is a test context for automatic vector store update"
    
    # Check if test tag already exists
    if test_tag in vector_store.tag_to_id:
        print(f"Test tag '{test_tag}' already exists in vector store")
        print(f"Current count: {vector_store.tag_counts.get(test_tag, 0)}")
    else:
        print(f"Test tag '{test_tag}' not in vector store, adding it...")
    
    # Update incrementally
    success = vector_store.update_tag_incrementally(test_tag, 'test', test_context)
    
    if success:
        print(f"✅ Successfully updated vector store with tag: {test_tag}")
        print(f"New count: {vector_store.tag_counts.get(test_tag, 0)}")
        
        # Test search
        print(f"\nTesting search for context: '{test_context[:50]}...'")
        results = vector_store.search_similar_tags(test_context, k=5)
        
        if results:
            print("Search results:")
            for tag, score, count in results:
                print(f"  - {tag:<30} (score: {score:.3f}, used: {count}x)")
                if tag == test_tag:
                    print(f"    ✅ Test tag found in results!")
        else:
            print("  No results found")
    else:
        print(f"❌ Failed to update vector store")
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)
    print("\nNOTE: The vector store now updates automatically when tags are added via:")
    print("  - Paper tags: /api/papers/{paper_id}/tags")
    print("  - Twitter tags: /api/tags/tweet/{tweet_id}")
    print("  - Article tags: /api/substack/articles/{article_id}/tags")
    print("\nNo manual rebuilding needed! The vector store saves every 10 new tags.")

if __name__ == "__main__":
    test_vector_store_auto_update()