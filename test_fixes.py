#!/usr/bin/env python3
"""
Test script to verify all fixes are working
"""
import requests
import json

def test_api_endpoints():
    """Test that all critical API endpoints are working"""
    
    tests = [
        ("Ontology Tree", "http://localhost:8000/api/ontology/tree"),
        ("Hierarchy Facets", "http://localhost:8000/api/v2/tweets/tweets/hierarchy-facets"),
        ("Faceted Search", "http://localhost:8000/api/v2/tweets/tweets/faceted-search?page=1&page_size=5"),
        ("Tags List", "http://localhost:8000/api/tags"),
    ]
    
    print("Testing API Endpoints...")
    print("=" * 50)
    
    for name, url in tests:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    count = len(data)
                    print(f"✅ {name}: {count} items returned")
                elif isinstance(data, dict):
                    if 'tweets' in data:
                        print(f"✅ {name}: {len(data['tweets'])} tweets, {len(data['facets']['tags'])} tags")
                    else:
                        print(f"✅ {name}: Response received")
                else:
                    print(f"✅ {name}: Working")
            else:
                print(f"❌ {name}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: {str(e)}")
    
    print("\n" + "=" * 50)
    print("Summary:")
    print("- Backend API: http://localhost:8000")
    print("- Frontend: http://localhost:3002")
    print("\nYou can now:")
    print("1. Open http://localhost:3002/tweets to see the Faceted Tweets Dashboard")
    print("2. Open http://localhost:3002/ontology to see the Tag Ontology Manager")
    print("3. Both should now show tags and work correctly!")

if __name__ == "__main__":
    test_api_endpoints()