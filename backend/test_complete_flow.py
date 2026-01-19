#!/usr/bin/env python3
"""
Test the complete paper analysis flow with different models
Simulates what happens when user selects a model and clicks Generate
"""
import requests
import json
import time

API_BASE = "http://localhost:8000/api"
PAPER_ID = "6921a98ae1b933c06cb3525a"

def test_analysis(analysis_type, model_name):
    """Test generating an analysis with a specific model"""
    print(f"\n{'='*70}")
    print(f"Testing: {analysis_type} with {model_name}")
    print('='*70)

    payload = {
        "analysis_type": analysis_type,
        "regenerate": True,
        "model": model_name
    }

    start_time = time.time()

    try:
        response = requests.post(
            f"{API_BASE}/papers/{PAPER_ID}/analyses/generate",
            json=payload,
            timeout=120
        )

        elapsed = time.time() - start_time
        result = response.json()

        print(f"✓ Status: {response.status_code}")
        print(f"✓ Time: {elapsed:.2f}s")
        print(f"✓ Model requested: {model_name}")
        print(f"✓ Model used: {result.get('model_used', 'N/A')}")

        if result.get('content'):
            content_preview = result['content'][:150].replace('\n', ' ')
            print(f"✓ Content generated: {len(result['content'])} chars")
            print(f"  Preview: {content_preview}...")
            return True
        else:
            print(f"✗ FAILED: No content generated")
            print(f"  Response: {json.dumps(result, indent=2)}")
            return False

    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False

# Test different models from the dropdown
test_cases = [
    ("evaluation", "claude-3.5-sonnet"),      # Default model
    ("layman_summary", "gpt-4o-mini"),         # Fast GPT model
    ("mollick_summary", "gemini-2.5-flash"),   # Fast Gemini model
]

print("\n" + "="*70)
print("TESTING PAPER ANALYSIS MODEL SELECTION")
print("="*70)
print(f"Paper: 'Early science acceleration experiments with GPT-5'")
print(f"Paper ID: {PAPER_ID}")

results = []
for analysis_type, model in test_cases:
    success = test_analysis(analysis_type, model)
    results.append((analysis_type, model, success))
    time.sleep(1)  # Brief pause between tests

# Summary
print("\n" + "="*70)
print("TEST SUMMARY")
print("="*70)
passed = sum(1 for _, _, success in results if success)
total = len(results)

for analysis_type, model, success in results:
    status = "✓ PASS" if success else "✗ FAIL"
    print(f"{status} - {analysis_type} with {model}")

print(f"\nResults: {passed}/{total} tests passed")

if passed == total:
    print("\n🎉 ALL TESTS PASSED! Model selection is working correctly.")
else:
    print(f"\n⚠️  {total - passed} test(s) failed. Check logs above for details.")
