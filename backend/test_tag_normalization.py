"""
Test script for tag normalization system
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db
from app.services.tag_normalizer import get_tag_normalizer
from sqlalchemy import text

def test_normalization():
    """Test tag normalization functionality"""
    db = next(get_db())
    normalizer = get_tag_normalizer(db)
    
    print("=" * 80)
    print("TAG NORMALIZATION TESTS")
    print("=" * 80)
    
    # Test cases
    test_cases = [
        # Input, Expected Output
        ("openai", "OpenAI"),
        ("OpenAI", "OpenAI"),
        ("OPENAI", "OpenAI"),
        ("gpt-4", "GPT-4"),
        ("GPT-4", "GPT-4"),
        ("artificial-intelligence", "artificial-intelligence"),
        ("Artificial Intelligence", "artificial-intelligence"),
        ("AI", "AI"),
        ("ai", "AI"),
        ("machine learning", "machine-learning"),
        ("Machine Learning", "machine-learning"),
        ("deep-learning", "deep-learning"),
        ("Deep Learning", "deep-learning"),
        ("huggingface", "HuggingFace"),
        ("HuggingFace", "HuggingFace"),
        ("pytorch", "PyTorch"),
        ("PyTorch", "PyTorch"),
        ("chatgpt", "ChatGPT"),
        ("ChatGPT", "ChatGPT"),
        ("api", "API"),
        ("API", "API"),
        ("llm", "LLM"),
        ("LLM", "LLM"),
        ("rlhf", "RLHF"),
        ("RLHF", "RLHF"),
        ("new-tag", "new-tag"),  # Unknown tag should be lowercase
        ("New Tag", "new-tag"),  # Unknown multi-word should be lowercase with hyphen
        ("NEWTAG", "NEWTAG"),  # Could be acronym, keep as-is
    ]
    
    print("\n1. Testing tag normalization:")
    print("-" * 40)
    
    passed = 0
    failed = 0
    
    for input_tag, expected in test_cases:
        result = normalizer.normalize_tag(input_tag)
        status = "✓" if result == expected else "✗"
        
        if result == expected:
            passed += 1
            print(f"{status} '{input_tag}' → '{result}'")
        else:
            failed += 1
            print(f"{status} '{input_tag}' → '{result}' (expected: '{expected}')")
    
    print(f"\nResults: {passed} passed, {failed} failed")
    
    # Test synonym relationships
    print("\n2. Testing synonym relationships:")
    print("-" * 40)
    
    # Check existing synonyms from migration using raw SQL
    cursor = db.execute(text("SELECT primary_tag, synonym_tag FROM tag_synonyms LIMIT 5"))
    synonyms = cursor.fetchall()
    
    if synonyms:
        print("Existing synonym relationships:")
        for primary_tag, synonym_tag in synonyms:
            print(f"  '{synonym_tag}' → sameAs → '{primary_tag}'")
            
            # Test resolution
            resolved = normalizer.get_primary_tag(synonym_tag)
            print(f"    Resolution test: '{synonym_tag}' resolves to '{resolved}'")
    else:
        print("No synonym relationships found in database")
    
    # Test getting all synonyms
    print("\n3. Testing synonym resolution:")
    print("-" * 40)
    
    test_tags = ["GPT-4", "gpt-4", "Open-Source", "open-source"]
    
    for tag in test_tags:
        primary = normalizer.get_primary_tag(tag)
        if primary:
            all_synonyms = normalizer.get_all_synonyms(tag)
            print(f"'{tag}' → Primary: '{primary}', All variants: {all_synonyms}")
        else:
            print(f"'{tag}' → No synonym relationship")
    
    db.close()
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_normalization()