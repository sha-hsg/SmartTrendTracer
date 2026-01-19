#!/usr/bin/env python3
"""Test paper analysis with model selection"""
import requests
import json

# Test data
paper_id = "6921a98ae1b933c06cb3525a"
payload = {
    "analysis_type": "summary",
    "regenerate": True,
    "model": "claude-3.5-sonnet"
}

# Make request
print(f"Testing paper analysis with model: {payload['model']}")
print(f"Paper ID: {paper_id}")
print(f"Analysis type: {payload['analysis_type']}")
print("-" * 60)

try:
    response = requests.post(
        f"http://localhost:8000/api/papers/{paper_id}/analyses/generate",
        json=payload,
        timeout=60
    )

    print(f"Status Code: {response.status_code}")
    print("-" * 60)

    result = response.json()
    print("Response:")
    print(json.dumps(result, indent=2))

    # Check if content was generated
    if result.get("content"):
        print("\n✓ SUCCESS! Content was generated:")
        print(result["content"][:200] + "...")
    else:
        print("\n✗ FAILED! No content generated")
        print(f"Model used: {result.get('model_used')}")

except Exception as e:
    print(f"ERROR: {e}")
