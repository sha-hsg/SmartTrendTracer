#!/usr/bin/env python3
"""Check MongoDB status and collection counts"""

from pymongo import MongoClient
from bson import ObjectId
import json

def check_mongodb_status():
    # Connect to MongoDB
    client = MongoClient()
    db = client.smarttrendtracer
    
    print("=== MongoDB Collections ===")
    collections = list(db.list_collection_names())
    print(f"Total collections: {len(collections)}")
    print(f"Collections: {', '.join(collections)}")
    
    print("\n=== Document Counts ===")
    total_documents = 0
    for coll_name in collections:
        count = db[coll_name].count_documents({})
        total_documents += count
        print(f"  {coll_name}: {count:,}")
    
    print(f"\nTotal documents: {total_documents:,}")
    
    # Check concept hierarchy integrity
    print("\n=== Concept Hierarchy Integrity ===")
    concepts = db.tag_concepts_v2
    
    # Check total concepts
    total_concepts = concepts.count_documents({})
    print(f"Total concepts: {total_concepts}")
    
    # Check root categories
    root_concepts = list(concepts.find({"parents": []}, {"slug": 1, "display_name": 1, "tag": 1}))
    print(f"Root categories: {len(root_concepts)}")
    for root in root_concepts:
        tag = root.get('tag') or root.get('slug', 'unknown')
        print(f"  - {root.get('display_name', 'No display name')} ({tag})")
    
    # Check orphaned concepts (concepts with non-existent parents)
    all_concepts = list(concepts.find({}, {"_id": 1, "slug": 1, "tag": 1, "parents": 1}))
    concept_ids = {str(c['_id']) for c in all_concepts}
    orphaned = []
    
    for concept in all_concepts:
        if concept.get('parents'):
            for parent_id in concept['parents']:
                if isinstance(parent_id, str) and parent_id not in concept_ids:
                    tag = concept.get('tag') or concept.get('slug', 'unknown')
                    orphaned.append(tag)
                    break
    
    print(f"Orphaned concepts (invalid parents): {len(orphaned)}")
    if orphaned:
        print(f"  Examples: {orphaned[:5]}")
    
    # Check for poly-hierarchy (multiple parents)
    poly_hierarchy = concepts.count_documents({"$expr": {"$gt": [{"$size": "$parents"}, 1]}})
    print(f"Concepts with multiple parents: {poly_hierarchy}")
    
    # Check tag instances mapping
    print("\n=== Tag Instance Mapping ===")
    instances = db.tag_instances
    total_instances = instances.count_documents({})
    mapped_instances = instances.count_documents({"concept_id": {"$ne": None}})
    orphan_instances = instances.count_documents({"concept_id": None})
    
    print(f"Total tag instances: {total_instances}")
    print(f"Mapped to concepts: {mapped_instances}")
    print(f"Orphaned instances: {orphan_instances}")
    
    # Check for string vs ObjectId issues
    print("\n=== ID Type Consistency ===")
    string_parent_ids = 0
    objectid_parent_ids = 0
    mixed_parent_concepts = []
    
    for concept in all_concepts:
        if concept.get('parents'):
            has_string = any(isinstance(p, str) for p in concept['parents'])
            has_objectid = any(isinstance(p, ObjectId) for p in concept['parents'])
            
            if has_string and has_objectid:
                tag = concept.get('tag') or concept.get('slug', 'unknown')
                mixed_parent_concepts.append(tag)
            elif has_string:
                string_parent_ids += 1
            elif has_objectid:
                objectid_parent_ids += 1
    
    print(f"Concepts with string parent IDs: {string_parent_ids}")
    print(f"Concepts with ObjectId parent IDs: {objectid_parent_ids}")
    print(f"Concepts with mixed ID types: {len(mixed_parent_concepts)}")
    if mixed_parent_concepts:
        print(f"  Examples: {mixed_parent_concepts[:5]}")
    
    # Check children arrays
    concepts_with_children = concepts.count_documents({"children": {"$exists": True, "$ne": []}})
    print(f"\nConcepts with children arrays: {concepts_with_children}")
    
    # Check usage counts
    concepts_with_usage = concepts.count_documents({"usage_count": {"$exists": True, "$gt": 0}})
    print(f"Concepts with usage counts: {concepts_with_usage}")

if __name__ == "__main__":
    check_mongodb_status()