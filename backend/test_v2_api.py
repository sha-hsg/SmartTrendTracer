#!/usr/bin/env python3
"""
Test script to verify the v2 API returns all required fields
"""
import requests
import json
from typing import Dict, Any, List

BASE_URL = "http://localhost:8000/api/ontology"

def print_result(name: str, data: Any):
    """Pretty print API result"""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}")
    if isinstance(data, dict) or isinstance(data, list):
        print(json.dumps(data, indent=2)[:1000])  # Limit output
    else:
        print(data)

def test_tree_endpoint():
    """Test /tree endpoint returns proper structure"""
    response = requests.get(f"{BASE_URL}/tree")
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            first_concept = data[0]
            print_result("/tree endpoint - First concept", first_concept)
            
            # Check required fields
            required_fields = ['id', 'tag', 'display_name', 'synonyms']
            missing = [f for f in required_fields if f not in first_concept]
            if missing:
                print(f"⚠️  Missing fields: {missing}")
            else:
                print("✅ All required fields present")
                
            # Check synonyms is array
            if 'synonyms' in first_concept:
                if isinstance(first_concept['synonyms'], list):
                    print(f"✅ synonyms is array with {len(first_concept['synonyms'])} items")
                else:
                    print(f"❌ synonyms is not an array: {type(first_concept['synonyms'])}")
        else:
            print("❌ /tree endpoint returned empty or non-list data")
    else:
        print(f"❌ /tree endpoint failed: {response.status_code}")

def test_concepts_endpoint():
    """Test /concepts endpoint"""
    response = requests.get(f"{BASE_URL}/concepts")
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            first_concept = data[0]
            print_result("/concepts endpoint - First concept", first_concept)
            
            # Check for synonyms field
            if 'synonyms' in first_concept:
                print(f"✅ synonyms field present: {first_concept['synonyms'][:3] if first_concept['synonyms'] else '[]'}")
            else:
                print("❌ synonyms field missing")
                
            if 'tag' in first_concept:
                print(f"✅ tag field present: {first_concept['tag']}")
            else:
                print("❌ tag field missing")
        else:
            print("❌ /concepts endpoint returned empty data")
    else:
        print(f"❌ /concepts endpoint failed: {response.status_code}")

def test_concept_detail():
    """Test /concept/{id} endpoint"""
    # First get a concept ID
    response = requests.get(f"{BASE_URL}/concepts")
    if response.status_code == 200 and response.json():
        concept_id = response.json()[0]['id']
        
        # Now get the detail
        detail_response = requests.get(f"{BASE_URL}/concept/{concept_id}")
        if detail_response.status_code == 200:
            data = detail_response.json()
            print_result(f"/concept/{concept_id} endpoint", data)
            
            # Check critical fields
            critical_fields = ['id', 'tag', 'display_name', 'synonyms', 'parent', 'children']
            for field in critical_fields:
                if field in data:
                    field_type = type(data[field]).__name__
                    if field == 'synonyms':
                        if isinstance(data[field], list):
                            print(f"✅ {field}: list with {len(data[field])} items")
                        else:
                            print(f"❌ {field}: expected list, got {field_type}")
                    elif field == 'children':
                        if isinstance(data[field], list):
                            print(f"✅ {field}: list with {len(data[field])} items")
                        else:
                            print(f"❌ {field}: expected list, got {field_type}")
                    else:
                        print(f"✅ {field}: {field_type}")
                else:
                    print(f"❌ {field}: missing")
                    
            # Check parent structure if present
            if data.get('parent'):
                parent = data['parent']
                if isinstance(parent, dict):
                    parent_fields = ['id', 'tag', 'display_name']
                    missing_parent = [f for f in parent_fields if f not in parent]
                    if missing_parent:
                        print(f"⚠️  Parent missing fields: {missing_parent}")
                    else:
                        print("✅ Parent has all required fields")
                else:
                    print(f"❌ Parent is not a dict: {type(parent)}")
        else:
            print(f"❌ /concept/{concept_id} failed: {detail_response.status_code}")
    else:
        print("❌ Could not get concept list to test detail endpoint")

def test_search_endpoint():
    """Test /search endpoint"""
    response = requests.get(f"{BASE_URL}/search", params={"query": "a"})
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            first_result = data[0]
            print_result("/search endpoint - First result", first_result)
            
            # Check for required fields
            if 'synonyms' in first_result:
                print(f"✅ synonyms field present and is list: {isinstance(first_result['synonyms'], list)}")
            else:
                print("❌ synonyms field missing")
                
            if 'tag' in first_result:
                print(f"✅ tag field present: {first_result['tag']}")
            else:
                print("❌ tag field missing")
        else:
            print("⚠️  /search endpoint returned empty results")
    else:
        print(f"❌ /search endpoint failed: {response.status_code}")

def main():
    print("Testing Tag Ontology v2 API Endpoints")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")
    
    try:
        # Test each endpoint
        test_tree_endpoint()
        test_concepts_endpoint()
        test_concept_detail()
        test_search_endpoint()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()