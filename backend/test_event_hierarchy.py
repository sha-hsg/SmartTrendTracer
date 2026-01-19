#!/usr/bin/env python3
"""
Test Event entity hierarchy display
"""

from pymongo import MongoClient
from bson import ObjectId
import requests

client = MongoClient('mongodb://localhost:27017/')
db = client.smarttrendtracer

print("=" * 60)
print("TESTING EVENT ENTITY HIERARCHY")
print("=" * 60)

# Check Event entity in database
print("\n1. DATABASE CHECK...")
print("-" * 40)

event_entity = db.tag_concepts_v2.find_one({"display_name": "Event"})
if event_entity:
    print(f"Event entity ID: {event_entity['_id']}")
    print(f"Event entity type: {event_entity.get('entity_type')}")
    print(f"Children array: {event_entity.get('children', [])}")
    
    # Check if children exist
    for child_id in event_entity.get('children', []):
        child = db.tag_concepts_v2.find_one({"_id": child_id})
        if child:
            print(f"  ✅ Child found: {child['display_name']} (ID: {child_id})")
            print(f"     Parents: {child.get('parents', [])}")
            if event_entity['_id'] in child.get('parents', []):
                print(f"     ✅ Parent reference is correct")
            else:
                print(f"     ❌ Parent reference is missing!")
        else:
            print(f"  ❌ Child not found: {child_id}")

# Test API endpoint
print("\n2. API ENDPOINT CHECK...")
print("-" * 40)

try:
    response = requests.get('http://localhost:8000/api/ontology/tree')
    if response.status_code == 200:
        tree = response.json()
        
        # Find Event in tree
        def find_concept_in_tree(nodes, display_name):
            for node in nodes:
                if node.get('display_name') == display_name:
                    return node
                if 'children' in node:
                    result = find_concept_in_tree(node['children'], display_name)
                    if result:
                        return result
            return None
        
        # First find Named Entities
        named_entities = find_concept_in_tree(tree, "Named Entities")
        if named_entities:
            print(f"✅ Named Entities found with {len(named_entities.get('children', []))} children")
            
            # Look for Event in Named Entities children
            event_in_tree = None
            for child in named_entities.get('children', []):
                if child.get('display_name') == 'Event':
                    event_in_tree = child
                    break
            
            if event_in_tree:
                print(f"✅ Event found in tree")
                print(f"   Child count: {event_in_tree.get('child_count', 0)}")
                print(f"   Has children array: {'children' in event_in_tree}")
                if 'children' in event_in_tree:
                    print(f"   Children in tree: {len(event_in_tree['children'])}")
                    for child in event_in_tree.get('children', []):
                        print(f"     - {child.get('display_name')}")
                else:
                    print(f"   ❌ No children array in tree node!")
            else:
                print(f"❌ Event not found under Named Entities")
        else:
            print(f"❌ Named Entities not found in tree")
            
    else:
        print(f"❌ API error: {response.status_code}")
except Exception as e:
    print(f"❌ Error calling API: {e}")

# Check concept detail endpoint
print("\n3. CONCEPT DETAIL ENDPOINT CHECK...")
print("-" * 40)

if event_entity:
    event_id = str(event_entity['_id'])
    try:
        response = requests.get(f'http://localhost:8000/api/ontology/concept/{event_id}')
        if response.status_code == 200:
            detail = response.json()
            print(f"✅ Concept detail retrieved")
            print(f"   Children in detail: {len(detail.get('children', []))}")
            if detail.get('children'):
                for child in detail['children']:
                    print(f"     - {child.get('display_name')}")
        else:
            print(f"❌ API error: {response.status_code}")
    except Exception as e:
        print(f"❌ Error calling API: {e}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)