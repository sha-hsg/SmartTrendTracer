#!/usr/bin/env python3
"""Test that user's model selection is actually used by LiteLLM"""
import requests
import json

API_BASE = "http://localhost:8000/api"
PAPER_ID = "6921a98ae1b933c06cb3525a"

def test_model_selection(model_name):
    """Test if selected model is actually used"""
    print(f"\n{'='*70}")
    print(f"Testing model selection: {model_name}")
    print('='*70)

    payload = {
        "analysis_type": "summary",
        "regenerate": True,
        "model": model_name  # User's selection from dropdown
    }

    response = requests.post(
        f"{API_BASE}/papers/{PAPER_ID}/analyses/generate",
        json=payload,
        timeout=120
    )

    result = response.json()

    if result.get('success'):
        model_used = result.get('model_used', 'Unknown')
        content_length = len(result.get('content', ''))

        print(f"✓ Requested: {model_name}")
        print(f"✓ Actually used: {model_used}")
        print(f"✓ Content generated: {content_length} chars")

        # Check if the model was honored (allowing for provider prefix)
        if model_name.replace('-', '') in model_used.replace('-', '').replace('/', ''):
            print(f"✅ SUCCESS: Your model selection was used!")
            return True
        else:
            print(f"⚠️  WARNING: Different model was used (might be fallback)")
            return False
    else:
        print(f"✗ FAILED: {result.get('error', 'Unknown error')}")
        return False

# Test different models from dropdown
print("\n" + "="*70)
print("TESTING MODEL SELECTION WITH LiteLLM")
print("="*70)

models_to_test = [
    "claude-3.5-sonnet",
    "gemini-2.5-flash",
    "gpt-4o-mini"
]

results = []
for model in models_to_test:
    success = test_model_selection(model)
    results.append((model, success))
    import time
    time.sleep(2)

# Summary
print("\n" + "="*70)
print("TEST RESULTS")
print("="*70)
for model, success in results:
    status = "✅ WORKING" if success else "⚠️  FALLBACK USED"
    print(f"{status} - {model}")

if all(success for _, success in results):
    print("\n🎉 ALL MODEL SELECTIONS WORKING!")
else:
    print("\n⚠️  Some models used fallbacks (check API keys/config)")
