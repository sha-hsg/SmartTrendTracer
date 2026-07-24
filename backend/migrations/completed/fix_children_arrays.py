#!/usr/bin/env python3
"""
Fix children arrays in MongoDB concepts
After reorganization, we need to rebuild the children arrays based on parent relationships
"""

from pymongo import MongoClient
from bson import ObjectId

def fix_children_arrays():
    """
    Rebuild children arrays based on parent relationships
    """
    client = MongoClient('mongodb://localhost:27017/')
    db = client.smarttrendtracer
    
    print("Fixing children arrays...")
    
    # First, clear all children arrays
    db.tag_concepts_v2.update_many({}, {'$set': {'children': []}})
    
    # Get all concepts with parents
    concepts_with_parents = db.tag_concepts_v2.find({'parents': {'$ne': []}})
    
    parent_children = {}
    
    # Build parent-to-children mapping
    for concept in concepts_with_parents:
        concept_id = concept['_id']
        for parent_id in concept.get('parents', []):
            if parent_id not in parent_children:
                parent_children[parent_id] = []
            parent_children[parent_id].append(concept_id)
    
    # Update each parent with its children
    updated_count = 0
    for parent_id, children_ids in parent_children.items():
        result = db.tag_concepts_v2.update_one(
            {'_id': parent_id},
            {'$set': {'children': children_ids}}
        )
        if result.modified_count > 0:
            parent = db.tag_concepts_v2.find_one({'_id': parent_id})
            print(f"  Updated {parent['display_name']}: {len(children_ids)} children")
            updated_count += 1
    
    print(f"\n✅ Updated {updated_count} parent concepts with children arrays")
    
    # Show statistics
    root_concepts = list(db.tag_concepts_v2.find({'parents': []}))
    print(f"\n📊 Root categories and their children:")
    for root in root_concepts:
        children_count = len(root.get('children', []))
        if children_count > 0:
            print(f"  {root['display_name']}: {children_count} children")
    
    # Verify total
    total_with_children = db.tag_concepts_v2.count_documents({'children': {'$ne': []}})
    total_with_parents = db.tag_concepts_v2.count_documents({'parents': {'$ne': []}})
    total_concepts = db.tag_concepts_v2.count_documents({})
    
    print(f"\n📈 Final statistics:")
    print(f"  Total concepts: {total_concepts}")
    print(f"  Concepts with parents: {total_with_parents}")
    print(f"  Concepts with children: {total_with_children}")

if __name__ == "__main__":
    fix_children_arrays()