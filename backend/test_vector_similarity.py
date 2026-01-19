#!/usr/bin/env python3
"""Test vector similarity search for papers"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.vector_store_openai import get_vector_store
from app.models import get_db
from app.models.papers import Paper

def test_similarity():
    """Test similarity search"""
    
    # Get database and paper
    db = next(get_db())
    paper = db.query(Paper).filter(Paper.id == 16).first()
    
    if not paper:
        print("Paper 16 not found")
        return
    
    print(f"Paper: {paper.title[:80]}...")
    print(f"Abstract: {(paper.abstract or '')[:200]}...")
    print("-" * 50)
    
    # Get vector store
    vector_store = get_vector_store()
    print(f"Vector store has {vector_store.index.ntotal} tags")
    
    # Test with just title
    print("\n1. Testing with TITLE only:")
    results = vector_store.search_similar_tags(
        query_text=paper.title,
        k=10,
        min_similarity=0.3
    )
    
    for tag, score, count in results:
        print(f"  {tag:<30} Score: {score:.3f}, Used: {count} times")
    
    # Test with title + abstract
    print("\n2. Testing with TITLE + ABSTRACT:")
    content = f"{paper.title}\n\n{paper.abstract or ''}"
    results = vector_store.search_similar_tags(
        query_text=content,
        k=10,
        min_similarity=0.3
    )
    
    for tag, score, count in results:
        print(f"  {tag:<30} Score: {score:.3f}, Used: {count} times")
    
    # Test with some keywords
    print("\n3. Testing with KEYWORDS:")
    keywords = "knowledge graphs large language models LLM"
    results = vector_store.search_similar_tags(
        query_text=keywords,
        k=10,
        min_similarity=0.3
    )
    
    for tag, score, count in results:
        print(f"  {tag:<30} Score: {score:.3f}, Used: {count} times")

if __name__ == "__main__":
    test_similarity()