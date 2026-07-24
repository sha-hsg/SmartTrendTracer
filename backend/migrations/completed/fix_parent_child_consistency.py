#!/usr/bin/env python3
"""Fix parent-child bidirectional consistency"""

from pymongo import MongoClient
from bson import ObjectId

client = MongoClient('mongodb://localhost:27017/')
db = client.smarttrendtracer

print("Fixing parent-child bidirectional consistency...")

# Clear all children arrays
db.tag_concepts_v2.update_many({}, {"$set": {"children": []}})

# Rebuild from parent relationships
all_concepts = db.tag_concepts_v2.find()
parent_to_children = {}

for concept in all_concepts:
    for parent_id in concept.get('parents', []):
        if parent_id not in parent_to_children:
            parent_to_children[parent_id] = set()
        parent_to_children[parent_id].add(concept['_id'])

# Update parents with their children
for parent_id, children_ids in parent_to_children.items():
    result = db.tag_concepts_v2.update_one(
        {"_id": parent_id},
        {"$set": {"children": list(children_ids)}}
    )

print(f"✅ Updated {len(parent_to_children)} parent concepts with their children")

# Verify
inconsistent = []
for concept in db.tag_concepts_v2.find({"parents": {"$ne": []}}):
    for parent_id in concept['parents']:
        parent = db.tag_concepts_v2.find_one({"_id": parent_id})
        if not parent or not concept['_id'] in parent.get('children', []):
            inconsistent.append(concept['display_name'])
            break

if inconsistent:
    print(f"⚠️ Still have {len(inconsistent)} inconsistent concepts")
else:
    print("✅ All parent-child relationships are now consistent!")
