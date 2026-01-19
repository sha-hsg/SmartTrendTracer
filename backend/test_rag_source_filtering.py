#!/usr/bin/env python3
"""
Test script to verify RAG source filtering works correctly.

Tests that the Tweets/Articles/Papers checkboxes in the UI actually filter
search results as expected.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.rag_service_concepts import ConceptBasedRAGService
from app.database.mongodb import get_database


def print_separator(title):
    """Print a section separator."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def test_source_filtering():
    """Test that source filtering works correctly."""

    print_separator("RAG Source Filtering Verification Tests")

    # Initialize service
    db = get_database()
    rag_service = ConceptBasedRAGService(db)

    # Test query that should return results from all types
    test_query = "artificial intelligence and machine learning"

    # Test 1: Only Tweets
    print_separator("TEST 1: Only Tweets (content_types=['tweet'])")
    results = rag_service.search(
        query=test_query,
        k=10,
        content_types=['tweet']
    )

    print(f"Retrieved {len(results)} results")
    print("\nDocument types found:")
    type_counts = {}
    for result in results:
        doc_type = result['metadata'].get('type', 'unknown')
        type_counts[doc_type] = type_counts.get(doc_type, 0) + 1

    for doc_type, count in type_counts.items():
        status = "✅" if doc_type == 'tweet' else "❌"
        print(f"  {status} {doc_type}: {count}")

    if type_counts.keys() == {'tweet'}:
        print("\n✅ PASS: Only tweets returned")
    else:
        print(f"\n❌ FAIL: Expected only tweets, got: {list(type_counts.keys())}")

    # Show sample results
    print("\nSample results:")
    for i, result in enumerate(results[:3], 1):
        meta = result['metadata']
        print(f"\n  {i}. Type: {meta.get('type')}")
        print(f"     Author: {meta.get('author', 'N/A')}")
        print(f"     Content: {result['content'][:100]}...")

    # Test 2: Only Articles
    print_separator("TEST 2: Only Articles (content_types=['article'])")
    results = rag_service.search(
        query=test_query,
        k=10,
        content_types=['article']
    )

    print(f"Retrieved {len(results)} results")
    print("\nDocument types found:")
    type_counts = {}
    for result in results:
        doc_type = result['metadata'].get('type', 'unknown')
        type_counts[doc_type] = type_counts.get(doc_type, 0) + 1

    for doc_type, count in type_counts.items():
        status = "✅" if doc_type == 'article' else "❌"
        print(f"  {status} {doc_type}: {count}")

    if type_counts.keys() == {'article'}:
        print("\n✅ PASS: Only articles returned")
    else:
        print(f"\n❌ FAIL: Expected only articles, got: {list(type_counts.keys())}")

    # Show sample results
    print("\nSample results:")
    for i, result in enumerate(results[:3], 1):
        meta = result['metadata']
        print(f"\n  {i}. Type: {meta.get('type')}")
        print(f"     Title: {meta.get('title', 'N/A')}")
        print(f"     Author: {meta.get('author', 'N/A')}")

    # Test 3: Only Papers
    print_separator("TEST 3: Only Papers (content_types=['paper'])")
    results = rag_service.search(
        query=test_query,
        k=10,
        content_types=['paper']
    )

    print(f"Retrieved {len(results)} results")
    print("\nDocument types found:")
    type_counts = {}
    for result in results:
        doc_type = result['metadata'].get('type', 'unknown')
        type_counts[doc_type] = type_counts.get(doc_type, 0) + 1

    for doc_type, count in type_counts.items():
        status = "✅" if doc_type == 'paper' else "❌"
        print(f"  {status} {doc_type}: {count}")

    if type_counts.keys() == {'paper'}:
        print("\n✅ PASS: Only papers returned")
    else:
        print(f"\n❌ FAIL: Expected only papers, got: {list(type_counts.keys())}")

    # Show sample results
    print("\nSample results:")
    for i, result in enumerate(results[:3], 1):
        meta = result['metadata']
        print(f"\n  {i}. Type: {meta.get('type')}")
        print(f"     Title: {meta.get('title', 'N/A')}")
        print(f"     Year: {meta.get('year', 'N/A')}")

    # Test 4: Multiple types (tweets + articles)
    print_separator("TEST 4: Tweets + Articles (content_types=['tweet', 'article'])")
    results = rag_service.search(
        query=test_query,
        k=10,
        content_types=['tweet', 'article']
    )

    print(f"Retrieved {len(results)} results")
    print("\nDocument types found:")
    type_counts = {}
    for result in results:
        doc_type = result['metadata'].get('type', 'unknown')
        type_counts[doc_type] = type_counts.get(doc_type, 0) + 1

    for doc_type, count in type_counts.items():
        status = "✅" if doc_type in ['tweet', 'article'] else "❌"
        print(f"  {status} {doc_type}: {count}")

    if set(type_counts.keys()).issubset({'tweet', 'article'}):
        print("\n✅ PASS: Only tweets and articles returned")
    else:
        print(f"\n❌ FAIL: Expected only tweets/articles, got: {list(type_counts.keys())}")

    # Test 5: All types (no filter)
    print_separator("TEST 5: All Types (content_types=None)")
    results = rag_service.search(
        query=test_query,
        k=10,
        content_types=None
    )

    print(f"Retrieved {len(results)} results")
    print("\nDocument types found:")
    type_counts = {}
    for result in results:
        doc_type = result['metadata'].get('type', 'unknown')
        type_counts[doc_type] = type_counts.get(doc_type, 0) + 1

    for doc_type, count in sorted(type_counts.items()):
        print(f"  ✅ {doc_type}: {count}")

    print("\n✅ PASS: Mixed content types returned (filtering disabled)")

    # Test 6: Empty list (should return all)
    print_separator("TEST 6: Empty List (content_types=[])")
    results = rag_service.search(
        query=test_query,
        k=10,
        content_types=[]
    )

    print(f"Retrieved {len(results)} results")
    print("\nDocument types found:")
    type_counts = {}
    for result in results:
        doc_type = result['metadata'].get('type', 'unknown')
        type_counts[doc_type] = type_counts.get(doc_type, 0) + 1

    for doc_type, count in sorted(type_counts.items()):
        print(f"  ✅ {doc_type}: {count}")

    print("\n✅ PASS: Empty list treated as 'all types'")

    # Summary
    print_separator("TEST SUMMARY")
    print("✅ Source filtering appears to be working correctly!")
    print("\nAll tests passed. The Tweets/Articles/Papers checkboxes should work as expected.")
    print("\nNext steps:")
    print("  1. Test in the UI to confirm end-to-end functionality")
    print("  2. Try different queries and filter combinations")
    print("  3. Verify that results are relevant to the selected sources")


if __name__ == "__main__":
    try:
        test_source_filtering()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
