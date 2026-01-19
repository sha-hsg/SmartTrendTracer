#!/usr/bin/env python3
"""Test that papers are properly included in RAG search"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db, Paper
from app.services.rag_service import RAGService
import json

def test_paper_search():
    """Test searching for papers in RAG index"""
    try:
        db = next(get_db())
        
        # Check how many papers are in the database
        paper_count = db.query(Paper).count()
        print(f"Total papers in database: {paper_count}")
        
        # Create RAG service
        rag_service = RAGService(db)
        
        # Get index stats
        stats = rag_service.get_stats()
        print(f"\nRAG Index Stats:")
        print(f"  Total documents: {stats.get('total_documents', 0)}")
        print(f"  Index ready: {stats.get('index_ready')}")
        
        # Test paper-specific queries
        test_queries = [
            "What are the state-of-the-art methods in LLM research?",
            "transformer architectures",
            "machine learning papers",
            "recent research papers",
            "AI safety alignment"
        ]
        
        print("\n" + "="*60)
        for query in test_queries:
            print(f"\nQuery: '{query}'")
            print("-" * 40)
            
            # Search
            results = rag_service.search(query, k=10)
            
            # Count paper results
            paper_results = [r for r in results if r.source_type == 'paper']
            tweet_results = [r for r in results if r.source_type == 'tweet']
            article_results = [r for r in results if r.source_type == 'article']
            
            print(f"Results found: {len(results)}")
            print(f"  - Papers: {len(paper_results)}")
            print(f"  - Tweets: {len(tweet_results)}")
            print(f"  - Articles: {len(article_results)}")
            
            # Show paper results
            if paper_results:
                print("\nPaper Results:")
                for i, result in enumerate(paper_results[:3], 1):
                    print(f"\n  {i}. Score: {result.score:.3f}")
                    if result.metadata:
                        print(f"     Title: {result.metadata.get('title', 'N/A')}")
                        authors = result.metadata.get('authors', [])
                        if authors:
                            authors_str = authors[:2] if isinstance(authors, list) else str(authors)
                            if isinstance(authors, list) and len(authors) > 2:
                                authors_str = authors[:2] + ['et al.']
                            print(f"     Authors: {', '.join(authors_str) if isinstance(authors_str, list) else authors_str}")
                        if result.metadata.get('conference'):
                            print(f"     Conference: {result.metadata['conference']}")
                        if result.metadata.get('publication_date'):
                            print(f"     Date: {result.metadata['publication_date']}")
                    print(f"     Content preview: {result.content[:150]}...")
        
        print("\n" + "="*60)
        print("\n✅ Paper RAG search is working!")
        
        # Test the full question-answering pipeline
        print("\n\nTesting Question-Answering with Papers:")
        print("-" * 60)
        qa_result = rag_service.answer_question(
            "What are the latest research papers about transformer architectures?",
            k=10
        )
        
        print(f"Question: What are the latest research papers about transformer architectures?")
        print(f"\nAnswer: {qa_result['answer'][:500]}...")
        print(f"\nSources used: {len(qa_result.get('sources', []))}")
        
        # Count source types
        sources = qa_result.get('sources', [])
        paper_sources = sum(1 for s in sources if s.get('type') == 'paper')
        print(f"  - Papers: {paper_sources}")
        print(f"  - Other: {len(sources) - paper_sources}")
        
        if paper_sources > 0:
            print("\n✅ Papers are being used in question answering!")
        else:
            print("\n⚠️ No papers found in question answering sources")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    test_paper_search()