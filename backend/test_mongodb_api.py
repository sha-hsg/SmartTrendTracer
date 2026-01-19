#!/usr/bin/env python3
"""
Test the MongoDB-based tag ontology API
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/ontology"

def test_stats():
    """Test the stats endpoint"""
    print("\n" + "="*60)
    print("Testing /stats endpoint")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/stats")
        if response.status_code == 200:
            data = response.json()
            print("✅ Stats retrieved successfully:")
            print(json.dumps(data, indent=2))
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
    except requests.exceptions.ConnectionError:
        print("❌ Server not running")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_tree():
    """Test the tree endpoint"""
    print("\n" + "="*60)
    print("Testing /tree endpoint")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/tree")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Tree retrieved: {len(data)} root concepts")
            if data:
                first = data[0]
                print(f"\nFirst root concept:")
                print(f"  ID: {first['id']}")
                print(f"  Display Name: {first['display_name']}")
                print(f"  Children: {len(first.get('children', []))}")
                print(f"  Synonyms: {first.get('synonyms', [])[:3]}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
    except requests.exceptions.ConnectionError:
        print("❌ Server not running")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_concept_detail():
    """Test concept detail endpoint"""
    print("\n" + "="*60)
    print("Testing /concept/{id} endpoint")
    print("="*60)
    
    try:
        # First get a concept ID
        response = requests.get(f"{BASE_URL}/concepts")
        if response.status_code == 200 and response.json():
            concept_id = response.json()[0]['id']
            
            # Get the detail
            detail_response = requests.get(f"{BASE_URL}/concept/{concept_id}")
            if detail_response.status_code == 200:
                data = detail_response.json()
                print(f"✅ Concept detail retrieved for: {concept_id}")
                print(f"  Display Name: {data['display_name']}")
                print(f"  Parent: {data.get('parent')}")
                print(f"  Children: {len(data.get('children', []))}")
                print(f"  Synonyms: {len(data.get('synonyms', []))}")
                print(f"  Usage Stats: {data.get('usage_stats')}")
            else:
                print(f"❌ Error getting detail: {detail_response.status_code}")
                print(detail_response.text)
        else:
            print(f"❌ Could not get concepts list")
    except requests.exceptions.ConnectionError:
        print("❌ Server not running")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_search():
    """Test search endpoint"""
    print("\n" + "="*60)
    print("Testing /search endpoint")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/search", params={"query": "gpt"})
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Search results: {len(data)} concepts found")
            for result in data[:3]:
                print(f"  - {result['display_name']} ({result['match_type']})")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
    except requests.exceptions.ConnectionError:
        print("❌ Server not running")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("\n" + "="*60)
    print("MongoDB Tag Ontology API Test")
    print("="*60)
    print(f"Testing API at: {BASE_URL}")
    
    # Run tests
    test_stats()
    test_tree()
    test_concept_detail()
    test_search()
    
    print("\n" + "="*60)
    print("✅ All tests completed")
    print("="*60)

if __name__ == "__main__":
    main()