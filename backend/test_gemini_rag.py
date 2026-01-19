#!/usr/bin/env python3
"""Test RAG with Gemini 2.5 Pro"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db
from app.services.rag_service import RAGService
import json

def test_gemini_rag():
    """Test RAG search and answer generation with Gemini"""
    try:
        db = next(get_db())
        
        print("=" * 60)
        print("Testing RAG with Gemini 2.5 Pro")
        print("=" * 60)
        
        # Create RAG service
        rag_service = RAGService(db)
        
        # Check configuration
        models_config = rag_service.llm_service.llm_config.get('models', {})
        rag_model = models_config.get('rag_answer', {}).get('model')
        chat_model = models_config.get('chat_general', {}).get('model')
        
        print(f"\nConfiguration:")
        print(f"  RAG Answer Model: {rag_model or 'Not configured'}")
        print(f"  Chat General Model: {chat_model or 'Not configured'}")
        print(f"  Active Provider: {rag_service.llm_service.llm_config.get('active_provider')}")
        
        # Test queries focusing on papers
        test_queries = [
            "What are the state-of-the-art transformer architectures discussed in recent papers?",
            "Which research papers discuss Mamba models?",
            "What are the key findings about language models in the papers?",
            "Find papers about AI memory systems and agent architectures"
        ]
        
        print("\n" + "=" * 60)
        for query in test_queries:
            print(f"\n📝 Query: {query}")
            print("-" * 40)
            
            # Get answer
            result = rag_service.answer_question(query, k=10)
            
            # Display results
            print(f"\n✨ Model Used: {result.get('model_used', 'Unknown')}")
            print(f"\n💡 Answer:\n{result['answer'][:500]}...")
            
            # Count source types
            sources = result.get('sources', [])
            paper_sources = sum(1 for s in sources if s.get('type') == 'paper')
            tweet_sources = sum(1 for s in sources if s.get('type') == 'tweet')
            article_sources = sum(1 for s in sources if s.get('type') == 'article')
            
            print(f"\n📚 Sources Used: {len(sources)} total")
            print(f"  - Papers: {paper_sources}")
            print(f"  - Tweets: {tweet_sources}")
            print(f"  - Articles: {article_sources}")
            
            # Show paper sources
            if paper_sources > 0:
                print("\n📄 Paper Sources:")
                for s in sources:
                    if s.get('type') == 'paper':
                        metadata = s.get('metadata', {})
                        title = metadata.get('title', 'Untitled')
                        authors = metadata.get('authors', [])
                        authors_str = ', '.join(authors[:2]) if isinstance(authors, list) else str(authors)
                        if isinstance(authors, list) and len(authors) > 2:
                            authors_str += ' et al.'
                        score = s.get('score', 0)
                        print(f"  • [{score:.3f}] {title[:60]}...")
                        if authors_str:
                            print(f"    Authors: {authors_str}")
            
            print("\n" + "=" * 60)
        
        # Final confirmation
        if rag_model and 'gemini' in rag_model.lower():
            print(f"\n✅ RAG is correctly configured with {rag_model}!")
        elif chat_model and 'gemini' in chat_model.lower():
            print(f"\n✅ RAG is using {chat_model} for answers!")
        else:
            print(f"\n⚠️ RAG is not using Gemini models. Check configuration.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    test_gemini_rag()