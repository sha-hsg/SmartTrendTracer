#!/usr/bin/env python3
"""
Test that LLM service methods are working after the fix
"""
from app.services.llm_service import LLMService

# Initialize service
llm_service = LLMService()

print("Testing LLM Service Methods")
print("=" * 60)

# Test 1: _call_llm method
print("\n1. Testing _call_llm method:")
print("-" * 40)
try:
    model_config = {
        'model': 'gpt-4o-mini',
        'temperature': 0.3,
        'max_tokens': 100
    }
    result = llm_service._call_llm("What is 2+2?", model_config)
    print(f"✅ _call_llm works: {result[:50]}...")
except AttributeError as e:
    print(f"❌ _call_llm failed: {e}")
except Exception as e:
    print(f"⚠️ _call_llm error: {e}")

# Test 2: generate_text method
print("\n2. Testing generate_text method:")
print("-" * 40)
try:
    result = llm_service.generate_text(
        prompt="What is machine learning?",
        system_message="You are a helpful AI assistant. Answer concisely.",
        max_tokens=100,
        temperature=0.5
    )
    print(f"✅ generate_text works: {result[:50]}...")
except AttributeError as e:
    print(f"❌ generate_text failed: {e}")
except Exception as e:
    print(f"⚠️ generate_text error: {e}")

# Test 3: generate_completion method (should already work)
print("\n3. Testing generate_completion method:")
print("-" * 40)
try:
    result = llm_service.generate_completion(
        prompt="What is Python?",
        model="gpt-4o-mini",
        temperature=0.3,
        max_tokens=100
    )
    print(f"✅ generate_completion works: {result[:50]}...")
except AttributeError as e:
    print(f"❌ generate_completion failed: {e}")
except Exception as e:
    print(f"⚠️ generate_completion error: {e}")

print("\n" + "=" * 60)
print("All methods should now be available!")