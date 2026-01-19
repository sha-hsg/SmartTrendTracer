#!/usr/bin/env python3
"""
Test the concept detail endpoint
"""
import requests
import json
from sqlalchemy import create_engine, text

# First, get a concept ID from the database
engine = create_engine('sqlite:///data/tweets.db')
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT id, display_name, parents, children
        FROM tag_concepts_v2
        WHERE children != '[]' AND children IS NOT NULL
        LIMIT 1
    """))
    row = result.fetchone()
    if row:
        concept_id = row[0]
        display_name = row[1]
        parents = row[2]
        children = row[3]
        
        print(f"Testing with concept: {concept_id} - {display_name}")
        print(f"Parents: {parents}")
        print(f"Children: {children}")
        print("-" * 60)
        
        # Try to fetch via API
        try:
            response = requests.get(f"http://localhost:8000/api/ontology/concept/{concept_id}")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("\n✅ Success! Response structure:")
                print(f"  - id: {data.get('id')}")
                print(f"  - display_name: {data.get('display_name')}")
                print(f"  - parent: {data.get('parent')}")
                print(f"  - children count: {len(data.get('children', []))}")
                print(f"  - synonyms count: {len(data.get('synonyms', []))}")
            else:
                print(f"\n❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Server not running. Start the server with:")
            print("   python app/main.py")
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print("No concepts with children found in database")