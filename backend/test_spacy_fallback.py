#!/usr/bin/env python3
"""
Test spaCy fallback for tag extraction
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.llm_service import LLMService
from app.models import get_db, Tweet

load_dotenv()

def test_spacy_fallback():
    """Test spaCy fallback with truncated retweets"""
    
    db = next(get_db())
    
    # Get truncated retweets (ones with ellipsis)
    tweets = db.query(Tweet).filter(
        Tweet.text.like('RT @%'),
        Tweet.text.like('%…%')
    ).limit(5).all()
    
    if not tweets:
        print("No truncated retweets found!")
        # Try any retweet
        tweets = db.query(Tweet).filter(
            Tweet.text.like('RT @%')
        ).limit(5).all()
    
    print("=" * 60)
    print("Testing spaCy Fallback for Truncated Retweets")
    print("=" * 60)
    
    # Initialize LLM service
    llm_service = LLMService()
    
    # Force use of fallback by temporarily setting wrong API key
    original_client = llm_service.client
    llm_service.client = None  # This will force fallback
    
    for tweet in tweets:
        print(f"\nTweet ID: {tweet.id}")
        print(f"Author: @{tweet.author_username}")
        print(f"Text: {tweet.text[:100]}...")
        print(f"Truncated: {'…' in tweet.text}")
        
        try:
            # This should use spaCy fallback
            tags = llm_service._fallback_tag_extraction(tweet.text)
            
            print(f"spaCy Tags: {tags}")
            print("-" * 40)
            
        except Exception as e:
            print(f"Error: {e}")
    
    # Restore client
    llm_service.client = original_client
    
    db.close()

def test_spacy_vs_simple():
    """Compare spaCy extraction vs simple keyword extraction"""
    
    test_texts = [
        "RT @sama: GPT-5 thinking capabilities are really amazing! We've been testing new methods for improving writing quality...",
        "OpenAI announces breakthrough in neural network architecture for large language models",
        "Just published our research paper on bias mitigation in AI systems. Available on arXiv.",
        "Hugging Face releases new open-source dataset for training multimodal models",
        "Thread: My thoughts on the recent developments in artificial general intelligence 🧵"
    ]
    
    print("\n" + "=" * 60)
    print("Comparing spaCy vs Simple Keyword Extraction")
    print("=" * 60)
    
    # Test spaCy extraction
    try:
        from app.services.spacy_tagger import get_spacy_tagger
        spacy_tagger = get_spacy_tagger()
        
        for text in test_texts:
            print(f"\nText: {text[:80]}...")
            
            # spaCy extraction
            spacy_tags = spacy_tagger.extract_tags(text, max_tags=5)
            print(f"spaCy tags: {spacy_tags}")
            
            # Simple keyword extraction (simulate the old fallback)
            llm_service = LLMService()
            # Temporarily break spaCy to force simple fallback
            import app.services.spacy_tagger
            original_get = app.services.spacy_tagger.get_spacy_tagger
            app.services.spacy_tagger.get_spacy_tagger = lambda: None
            
            simple_tags = llm_service._fallback_tag_extraction(text)
            print(f"Simple tags: {simple_tags}")
            
            # Restore
            app.services.spacy_tagger.get_spacy_tagger = original_get
            
            print("-" * 40)
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Testing spaCy fallback for truncated retweets...")
    test_spacy_fallback()
    
    print("\n\nComparing extraction methods...")
    test_spacy_vs_simple()