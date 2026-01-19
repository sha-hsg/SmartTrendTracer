#!/usr/bin/env python3
"""Build the RAG index for the SmartTrendTracer system"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db
from app.services.rag_service import RAGService
import time

def build_rag_index():
    """Build the RAG index from tweets and articles"""
    print("=" * 60)
    print("Building RAG Index for SmartTrendTracer")
    print("=" * 60)
    
    # Get database session
    db = next(get_db())
    
    # Count documents
    from app.models import Tweet, SubstackArticle, ArticleSnippet
    from app.models.papers import Paper, PaperSnippet
    tweet_count = db.query(Tweet).count()
    article_count = db.query(SubstackArticle).count()
    article_snippet_count = db.query(ArticleSnippet).count()
    paper_count = db.query(Paper).count()
    paper_snippet_count = db.query(PaperSnippet).count()
    
    print(f"\nDocuments to index:")
    print(f"  Tweets: {tweet_count}")
    print(f"  Articles: {article_count}")
    print(f"  Papers: {paper_count}")
    print(f"  Article Snippets: {article_snippet_count}")
    print(f"  Paper Snippets: {paper_snippet_count}")
    print(f"  Total: {tweet_count + article_count + paper_count + article_snippet_count + paper_snippet_count}")
    
    if tweet_count + article_count + paper_count == 0:
        print("\nNo documents to index! Please collect tweets, articles, and papers first.")
        return
    
    print("\nBuilding index (this may take a few minutes)...")
    start_time = time.time()
    
    try:
        # Initialize RAG service (this will build the index)
        rag_service = RAGService(db)
        
        # Get stats
        stats = rag_service.get_stats()
        
        elapsed_time = time.time() - start_time
        print(f"\n✅ Index built successfully in {elapsed_time:.1f} seconds!")
        print(f"Total documents indexed: {stats['total_documents']}")
        print(f"Documents by type: {stats['documents_by_type']}")
        print(f"Index location: {stats['index_path']}")
        
    except Exception as e:
        print(f"\n❌ Error building index: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "=" * 60)
    print("RAG index is ready for use!")
    print("You can now use the AI Search feature in the web interface.")
    print("=" * 60)

if __name__ == "__main__":
    build_rag_index()