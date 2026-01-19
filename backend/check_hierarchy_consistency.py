#!/usr/bin/env python3
"""
Check and fix parent-child bidirectional consistency in concept hierarchy
"""

from pymongo import MongoClient
from bson import ObjectId

client = MongoClient('mongodb://localhost:27017/')
db = client.smarttrendtracer

print("=" * 60)
print("CHECKING CONCEPT HIERARCHY CONSISTENCY")
print("=" * 60)

# Check Event entity specifically
print("\n1. CHECKING EVENT ENTITY...")
print("-" * 40)

event_entity = db.tag_concepts_v2.find_one({"display_name": "Event"})
if event_entity:
    print(f"Event entity: {event_entity['_id']}")
    print(f"Children array: {event_entity.get('children', [])}")
    print(f"Number of children in array: {len(event_entity.get('children', []))}")
    
    # Find actual children by parent relationship
    actual_children = list(db.tag_concepts_v2.find({"parents": event_entity['_id']}))
    print(f"Actual children with Event as parent: {len(actual_children)}")
    for child in actual_children:
        print(f"  - {child['display_name']} ({child['_id']})")
else:
    print("Event entity not found!")

# Check all entities for consistency
print("\n2. CHECKING ALL PARENT-CHILD CONSISTENCY...")
print("-" * 40)

inconsistent = []
all_concepts = list(db.tag_concepts_v2.find())

for concept in all_concepts:
    concept_id = concept['_id']
    stored_children = set(concept.get('children', []))
    
    # Find actual children
    actual_children_docs = list(db.tag_concepts_v2.find({"parents": concept_id}))
    actual_children = set([c['_id'] for c in actual_children_docs])
    
    if stored_children != actual_children:
        inconsistent.append({
            'name': concept['display_name'],
            'id': concept_id,
            'stored_count': len(stored_children),
            'actual_count': len(actual_children),
            'stored': stored_children,
            'actual': actual_children
        })

if inconsistent:
    print(f"Found {len(inconsistent)} concepts with inconsistent children:")
    for item in inconsistent[:10]:  # Show first 10
        print(f"\n  {item['name']}:")
        print(f"    Stored children: {item['stored_count']}")
        print(f"    Actual children: {item['actual_count']}")
        if item['actual_count'] > 0 and item['actual_count'] <= 5:
            # Show actual children names for small counts
            children_names = []
            for child_id in item['actual']:
                child = db.tag_concepts_v2.find_one({"_id": child_id})
                if child:
                    children_names.append(child['display_name'])
            print(f"    Actual children names: {', '.join(children_names)}")
else:
    print("✅ All parent-child relationships are consistent!")

# Fix the inconsistencies
print("\n3. FIXING INCONSISTENCIES...")
print("-" * 40)

if inconsistent:
    # Rebuild all children arrays from parent relationships
    parent_to_children = {}
    
    for concept in all_concepts:
        for parent_id in concept.get('parents', []):
            if parent_id not in parent_to_children:
                parent_to_children[parent_id] = []
            parent_to_children[parent_id].append(concept['_id'])
    
    # Update all concepts
    updated_count = 0
    for concept in all_concepts:
        concept_id = concept['_id']
        correct_children = parent_to_children.get(concept_id, [])
        
        # Only update if different
        current_children = concept.get('children', [])
        if set(current_children) != set(correct_children):
            db.tag_concepts_v2.update_one(
                {"_id": concept_id},
                {"$set": {"children": correct_children}}
            )
            updated_count += 1
    
    print(f"✅ Updated {updated_count} concepts with correct children arrays")
    
    # Verify Event entity again
    event_entity = db.tag_concepts_v2.find_one({"display_name": "Event"})
    if event_entity:
        print(f"\nEvent entity after fix:")
        print(f"  Children: {len(event_entity.get('children', []))}")
        actual = list(db.tag_concepts_v2.find({"parents": event_entity['_id']}))
        for child in actual:
            print(f"    - {child['display_name']}")

print("\n" + "=" * 60)
print("HIERARCHY CONSISTENCY CHECK COMPLETE")
print("=" * 60)