"""
API-based test suite for LLM Manager migrations
Tests actual API endpoints that use the migrated services
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

print("🧪 LLM Migration API Test Suite")
print("=" * 80)
print(f"Testing against: {BASE_URL}")
print()

# Helper function to test API endpoints
def test_endpoint(name, method, endpoint, data=None, expected_fields=None):
    """Test an API endpoint and verify response"""
    print(f"Testing: {name}")
    print(f"   Endpoint: {method} {endpoint}")

    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=30)
        elif method == "POST":
            response = requests.post(f"{BASE_URL}{endpoint}", json=data, timeout=30)
        else:
            print(f"   ❌ Unsupported method: {method}")
            return False

        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()

            # Check expected fields
            if expected_fields:
                missing = [f for f in expected_fields if f not in result]
                if missing:
                    print(f"   ⚠️  Missing fields: {missing}")
                else:
                    print(f"   ✅ All expected fields present")

            # Print response preview
            if isinstance(result, dict):
                preview = {k: str(v)[:50] + "..." if len(str(v)) > 50 else v
                          for k, v in list(result.items())[:3]}
                print(f"   Response preview: {json.dumps(preview, indent=6)}")
            elif isinstance(result, list):
                print(f"   Response: {len(result)} items")

            return True
        else:
            print(f"   ❌ Error: {response.text[:100]}")
            return False

    except requests.exceptions.ConnectionError:
        print(f"   ❌ Connection error - is the server running?")
        return False
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False

# Check if server is running
print("0️⃣  Checking server status...")
try:
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    if response.status_code == 200:
        print("   ✅ Server is running\n")
    else:
        print("   ⚠️  Server responded with non-200 status\n")
except:
    print("   ❌ Server is not running!")
    print("   Please start the server with: python app/main.py\n")
    exit(1)

print("=" * 80)
print()

# Test 1: Tag Suggestions (tags_mongodb.py - migrated)
print("1️⃣  Tag Suggestions API (tags_mongodb.py)")
# This would need a real tweet ID, skipping for now
print("   ℹ️  Skipping (requires valid tweet ID)")
print()

# Test 2: RAG Search (rag_service_concepts.py - migrated)
print("2️⃣  RAG Search API (rag_concepts.py)")
test_endpoint(
    name="RAG Index Stats",
    method="GET",
    endpoint="/api/rag/stats",
    expected_fields=["document_count", "source_types"]
)
print()

# Test 3: Concept Suggestions (concepts_suggestions_mongodb.py - migrated)
print("3️⃣  Concept Suggestions API (concepts_suggestions_mongodb.py)")
# This would need a real tweet ID, skipping for now
print("   ℹ️  Skipping (requires valid tweet ID)")
print()

# Test 4: Analytics Trends (analytics_trends_mongodb.py - migrated)
print("4️⃣  Analytics Trends API (analytics_trends_mongodb.py)")
test_endpoint(
    name="Content Summary",
    method="GET",
    endpoint="/api/analytics/summary?period=7days",
    expected_fields=["summary", "statistics"]
)
print()

# Test 5: Papers API (papers_mongodb.py - uses migrated services)
print("5️⃣  Papers API (papers_mongodb.py)")
test_endpoint(
    name="List Papers",
    method="GET",
    endpoint="/api/papers/?limit=5",
    expected_fields=["papers", "total"]
)
print()

# Test 6: Articles API (articles_mongodb.py - migrated)
print("6️⃣  Articles API (articles_mongodb.py)")
test_endpoint(
    name="List Articles",
    method="GET",
    endpoint="/api/substack/articles?limit=5",
    expected_fields=[] # Structure varies
)
print()

# Test 7: Ontology API (uses ontology_ai_service.py - Phase 1 migrated)
print("7️⃣  Ontology API (ontology_ai_service.py)")
test_endpoint(
    name="Get Concepts",
    method="GET",
    endpoint="/api/ontology/concepts",
    expected_fields=[]  # Returns array
)
print()

# Test 8: Statistics API (statistics_mongodb.py)
print("8️⃣  Statistics API")
test_endpoint(
    name="Collection Statistics",
    method="GET",
    endpoint="/api/statistics/",
    expected_fields=["tweets", "articles", "papers"]
)
print()

print("=" * 80)
print("✅ API Test Suite Complete!")
print("\nNext: Test actual LLM functionality with real data")
print("=" * 80)
