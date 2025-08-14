#!/usr/bin/env python3
"""
Test vector store search directly
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.vector_store_openai import get_vector_store
from app.models import get_db, Tweet

load_dotenv()

def test_vector_search():
    """Test vector search with sample queries"""
    
    # Get vector store
    vector_store = get_vector_store()
    print(f"Vector store loaded with {len(vector_store.tag_to_id)} tags")
    print("=" * 60)
    
    # Test queries
    test_queries = [
        "OpenAI releases new GPT model with improved capabilities",
        "Hugging Face announces open source AI tools",
        "Machine learning research paper on neural networks",
        "Breaking news about artificial intelligence",
        "Google DeepMind breakthrough in AI safety"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query[:60]}...")
        print("-" * 40)
        
        results = vector_store.search_similar_tags(
            query_text=query,
            k=5,
            min_similarity=0.5
        )
        
        if results:
            print("Similar tags found:")
            for tag, score, count in results:
                print(f"  • {tag:<30} (score: {score:.3f}, used: {count}x)")
        else:
            print("  No similar tags found")
    
    # Now test with actual tweets
    print("\n" + "=" * 60)
    print("Testing with actual tweets")
    print("=" * 60)
    
    db = next(get_db())
    
    # Get tweets with few or no tags
    tweets = db.query(Tweet).limit(3).all()
    
    for tweet in tweets:
        print(f"\nTweet: @{tweet.author_username}")
        print(f"Text: {tweet.text[:80]}...")
        print("-" * 40)
        
        results = vector_store.search_similar_tags(
            query_text=tweet.text,
            k=5,
            min_similarity=0.45  # Even lower threshold for testing
        )
        
        if results:
            print("Similar tags found:")
            for tag, score, count in results:
                print(f"  • {tag:<30} (score: {score:.3f}, used: {count}x)")
        else:
            print("  No similar tags found")
    
    db.close()

if __name__ == "__main__":
    test_vector_search()