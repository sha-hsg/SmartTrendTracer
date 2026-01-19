#!/usr/bin/env python3
"""
Comprehensive test suite for RAG trend analysis features.

Tests:
1. Trend query detection
2. Trend analysis with tweets only
3. Trend analysis with articles only
4. Trend analysis with papers only
5. Trend analysis with mixed content
6. Response format validation
7. LLM integration
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


def test_trend_query_detection():
    """Test that trend-related questions are correctly detected."""

    print_separator("TEST 1: Trend Query Detection")

    db = get_database()
    rag_service = ConceptBasedRAGService(db)

    # Trend queries (should return True)
    trend_queries = [
        "What are the key trends on Twitter?",
        "Show me trending topics in papers",
        "What's hot in articles right now?",
        "What are people talking about?",
        "What are the latest developments?",
        "What's the biggest topic emerging?",
        "What are the most discussed papers?",
        "What's trending in AI research?"
    ]

    print("Testing TREND queries (should be detected as trends):\n")
    all_detected = True
    for query in trend_queries:
        is_trend = rag_service.is_trend_query(query)
        status = "✅ PASS" if is_trend else "❌ FAIL"
        print(f"  {status}: \"{query}\" -> {is_trend}")
        if not is_trend:
            all_detected = False

    # Non-trend queries (should return False)
    normal_queries = [
        "What papers discuss transformer architectures?",
        "Explain how GPT-4 works",
        "Which articles mention Claude?",
        "Summarize tweets about AI safety"
    ]

    print("\nTesting NORMAL queries (should NOT be detected as trends):\n")
    for query in normal_queries:
        is_trend = rag_service.is_trend_query(query)
        status = "✅ PASS" if not is_trend else "❌ FAIL"
        print(f"  {status}: \"{query}\" -> {is_trend}")
        if is_trend:
            all_detected = False

    if all_detected:
        print("\n✅ PASS: All trend detection tests passed")
    else:
        print("\n❌ FAIL: Some trend detection tests failed")

    return all_detected


def test_trend_analysis_tweets():
    """Test trend analysis with tweets only."""

    print_separator("TEST 2: Trend Analysis - Tweets Only")

    db = get_database()
    rag_service = ConceptBasedRAGService(db)

    print("Analyzing trends in tweets...")
    print("Query: 'What are the key trends on Twitter?'\n")

    try:
        result = rag_service.analyze_trends(
            question="What are the key trends on Twitter?",
            content_types=['tweet'],
            k=30  # Analyze 30 tweets
        )

        print(f"✅ Analysis completed successfully")
        print(f"  is_trend_analysis: {result.get('is_trend_analysis')}")
        print(f"  documents_analyzed: {result.get('documents_analyzed')}")
        print(f"  source_type: {result.get('source_type')}")
        print(f"  sources count: {len(result.get('sources', []))}")
        print(f"\n📊 Answer preview:")
        print(f"  {result['answer'][:300]}...")

        # Validate response format
        assert result.get('is_trend_analysis') == True, "Should be marked as trend analysis"
        assert result.get('documents_analyzed', 0) > 0, "Should have analyzed documents"
        assert result.get('source_type') == 'tweets', "Should specify tweets as source type"
        assert len(result.get('answer', '')) > 0, "Should have non-empty answer"
        assert len(result.get('sources', [])) > 0, "Should have sources"

        print("\n✅ PASS: Tweets trend analysis working correctly")
        return True

    except Exception as e:
        print(f"\n❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_trend_analysis_papers():
    """Test trend analysis with papers only."""

    print_separator("TEST 3: Trend Analysis - Papers Only")

    db = get_database()
    rag_service = ConceptBasedRAGService(db)

    print("Analyzing trends in research papers...")
    print("Query: 'What are the key trends in research papers?'\n")

    try:
        result = rag_service.analyze_trends(
            question="What are the key trends in research papers?",
            content_types=['paper'],
            k=20  # Analyze 20 papers
        )

        print(f"✅ Analysis completed successfully")
        print(f"  is_trend_analysis: {result.get('is_trend_analysis')}")
        print(f"  documents_analyzed: {result.get('documents_analyzed')}")
        print(f"  source_type: {result.get('source_type')}")
        print(f"  sources count: {len(result.get('sources', []))}")
        print(f"\n📊 Answer preview:")
        print(f"  {result['answer'][:300]}...")

        # Validate response format
        assert result.get('is_trend_analysis') == True
        assert result.get('source_type') == 'papers'
        assert len(result.get('answer', '')) > 0

        print("\n✅ PASS: Papers trend analysis working correctly")
        return True

    except Exception as e:
        print(f"\n❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_trend_analysis_articles():
    """Test trend analysis with articles only."""

    print_separator("TEST 4: Trend Analysis - Articles Only")

    db = get_database()
    rag_service = ConceptBasedRAGService(db)

    print("Analyzing trends in articles...")
    print("Query: 'What are the hot topics in articles?'\n")

    try:
        result = rag_service.analyze_trends(
            question="What are the hot topics in articles?",
            content_types=['article'],
            k=20  # Analyze 20 articles
        )

        print(f"✅ Analysis completed successfully")
        print(f"  is_trend_analysis: {result.get('is_trend_analysis')}")
        print(f"  documents_analyzed: {result.get('documents_analyzed')}")
        print(f"  source_type: {result.get('source_type')}")
        print(f"  sources count: {len(result.get('sources', []))}")
        print(f"\n📊 Answer preview:")
        print(f"  {result['answer'][:300]}...")

        # Validate response format
        assert result.get('is_trend_analysis') == True
        assert result.get('source_type') == 'articles'
        assert len(result.get('answer', '')) > 0

        print("\n✅ PASS: Articles trend analysis working correctly")
        return True

    except Exception as e:
        print(f"\n❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ask_method_routing():
    """Test that ask() method routes trend queries correctly."""

    print_separator("TEST 5: ask() Method Routing")

    db = get_database()
    rag_service = ConceptBasedRAGService(db)

    print("Testing that ask() routes trend queries to analyze_trends()...\n")

    try:
        # Ask a trend question through the ask() method
        result = rag_service.ask(
            question="What are the key trends on Twitter?",
            content_types=['tweet']
        )

        print("✅ ask() method completed successfully")
        print(f"  is_trend_analysis: {result.get('is_trend_analysis')}")

        # Should be routed to trend analysis
        assert result.get('is_trend_analysis') == True, "Should be routed to trend analysis"
        assert result.get('documents_analyzed', 0) > 0, "Should analyze many documents"

        print(f"  documents_analyzed: {result.get('documents_analyzed')}")
        print(f"\n📊 Trend analysis result:")
        print(f"  {result['answer'][:200]}...")

        print("\n✅ PASS: ask() method correctly routes to trend analysis")
        return True

    except Exception as e:
        print(f"\n❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_normal_query_not_routed():
    """Test that normal queries are NOT routed to trend analysis."""

    print_separator("TEST 6: Normal Query Handling")

    db = get_database()
    rag_service = ConceptBasedRAGService(db)

    print("Testing that normal queries use standard RAG search...\n")

    try:
        # Ask a normal question
        result = rag_service.ask(
            question="What papers discuss transformer architectures?",
            content_types=['paper']
        )

        print("✅ ask() method completed successfully")
        print(f"  is_trend_analysis: {result.get('is_trend_analysis', False)}")

        # Should NOT be trend analysis
        assert result.get('is_trend_analysis') != True, "Should NOT be trend analysis"

        print(f"  concepts_used: {len(result.get('concepts_used', []))} concepts")
        print(f"\n📊 Standard RAG answer:")
        print(f"  {result['answer'][:200]}...")

        print("\n✅ PASS: Normal queries use standard RAG search")
        return True

    except Exception as e:
        print(f"\n❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""

    print_separator("RAG Trend Analysis Test Suite")
    print("Testing all trend analysis features...\n")

    results = {
        "Trend Detection": test_trend_query_detection(),
        "Tweets Trend Analysis": test_trend_analysis_tweets(),
        "Papers Trend Analysis": test_trend_analysis_papers(),
        "Articles Trend Analysis": test_trend_analysis_articles(),
        "ask() Routing": test_ask_method_routing(),
        "Normal Query Handling": test_normal_query_not_routed()
    }

    # Summary
    print_separator("TEST SUMMARY")

    total = len(results)
    passed = sum(results.values())
    failed = total - passed

    print(f"Total tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}\n")

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {test_name}")

    print("\n" + "=" * 80)

    if failed == 0:
        print("🎉 All tests passed! Trend analysis is working correctly.")
        return 0
    else:
        print(f"⚠️  {failed} test(s) failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
