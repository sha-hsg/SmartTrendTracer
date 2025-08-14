#!/usr/bin/env python3
"""
Test tag suggestion to see why it's using fallback
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.llm_service import LLMService

load_dotenv()

def test_tag_suggestion():
    """Test the tag suggestion"""
    
    print("=" * 60)
    print("Testing Tag Suggestion")
    print("=" * 60)
    
    # Check API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment!")
        print("   Please set it in your .env file")
        return
    else:
        print(f"✅ OPENAI_API_KEY found: {api_key[:10]}...")
    
    # Initialize LLM service
    try:
        llm_service = LLMService()
        print("✅ LLM Service initialized")
        
        # Check config
        print(f"\nConfiguration:")
        print(f"  Provider: {llm_service.llm_config.get('provider', 'unknown')}")
        print(f"  Tag model: {llm_service.llm_config['models']['tag_suggestion']['model']}")
        print(f"  Is reasoning: {llm_service.llm_config['models']['tag_suggestion'].get('is_reasoning', False)}")
        
    except Exception as e:
        print(f"❌ Error initializing LLM service: {e}")
        return
    
    # Test with a sample tweet
    test_tweet = "OpenAI just released GPT-5 with amazing new capabilities for coding and reasoning. This is a game changer for AI development!"
    test_author = "sama"
    
    print(f"\nTest tweet:")
    print(f"  Author: @{test_author}")
    print(f"  Text: {test_tweet}")
    
    print("\nCalling tag suggestion...")
    try:
        tags = llm_service.suggest_tags(test_tweet, test_author)
        print(f"\n✅ Success! Generated {len(tags)} tags:")
        for i, tag in enumerate(tags, 1):
            print(f"  {i}. {tag}")
            
    except Exception as e:
        print(f"\n❌ Error generating tags: {e}")
        print(f"   Error type: {type(e).__name__}")
        
        # Try fallback
        print("\nTrying fallback extraction...")
        fallback_tags = llm_service._fallback_tag_extraction(test_tweet)
        print(f"Fallback generated {len(fallback_tags)} tags:")
        for i, tag in enumerate(fallback_tags, 1):
            print(f"  {i}. {tag}")

if __name__ == "__main__":
    test_tag_suggestion()