#!/usr/bin/env python3
"""
Merge concepts with string _id into existing concepts with ObjectIds
"""

from pymongo import MongoClient
from bson import ObjectId

client = MongoClient('mongodb://localhost:27017/')
db = client.smarttrendtracer

print("=" * 60)
print("MERGING STRING ID CONCEPTS WITH EXISTING CONCEPTS")
print("=" * 60)

# Find concepts with string _id
string_id_concepts = list(db.tag_concepts_v2.find({'_id': {'$type': 'string'}}))

print(f"\nFound {len(string_id_concepts)} concepts with string _id:")
for c in string_id_concepts:
    print(f"  - {c['_id']}: {c.get('display_name')} (slug: {c.get('slug')})")

# For each string ID concept, find or create the proper ObjectId concept
print("\n" + "-" * 40)
print("MERGING CONCEPTS...")
print("-" * 40)

id_mapping = {}

for string_concept in string_id_concepts:
    string_id = string_concept['_id']
    slug = string_concept.get('slug')
    display_name = string_concept.get('display_name')
    
    # Try to find existing concept with same slug (ObjectId)
    existing = db.tag_concepts_v2.find_one({
        '_id': {'$type': 'objectId'},
        '$or': [
            {'slug': slug},
            {'display_name': display_name}
        ]
    })
    
    if existing:
        print(f"\nMerging '{string_id}' into existing concept '{existing['_id']}'")
        id_mapping[string_id] = existing['_id']
        
        # Merge data from string concept into existing
        updates = {}
        
        # Merge children (combine unique)
        existing_children = set(existing.get('children', []))
        string_children = set(string_concept.get('children', []))
        merged_children = list(existing_children | string_children)
        if merged_children != existing.get('children', []):
            updates['children'] = merged_children
        
        # Take usage count (use max)
        if string_concept.get('usage_count', 0) > existing.get('usage_count', 0):
            updates['usage_count'] = string_concept['usage_count']
        
        # Apply updates if any
        if updates:
            db.tag_concepts_v2.update_one({'_id': existing['_id']}, {'$set': updates})
            print(f"  Updated existing concept with merged data")
        
        # Update references to string ID
        # Update parent references
        result = db.tag_concepts_v2.update_many(
            {'parents': string_id},
            {'$set': {'parents.$': existing['_id']}}
        )
        if result.modified_count:
            print(f"  Updated {result.modified_count} parent references")
        
        # Update child references
        result = db.tag_concepts_v2.update_many(
            {'children': string_id},
            {'$set': {'children.$': existing['_id']}}
        )
        if result.modified_count:
            print(f"  Updated {result.modified_count} child references")
        
        # Update tag_instances
        result = db.tag_instances.update_many(
            {'concept_id': string_id},
            {'$set': {'concept_id': str(existing['_id'])}}
        )
        if result.modified_count:
            print(f"  Updated {result.modified_count} tag instances")
        
        # Delete the string ID concept
        db.tag_concepts_v2.delete_one({'_id': string_id})
        print(f"  Deleted string ID concept")
        
    else:
        # No existing concept found - create new one with ObjectId
        print(f"\nCreating new ObjectId concept for '{string_id}'")
        
        new_id = ObjectId()
        new_concept = dict(string_concept)
        new_concept['_id'] = new_id
        del new_concept['_id']  # Remove to insert with new ID
        
        # Insert with new ObjectId
        new_concept['_id'] = new_id
        db.tag_concepts_v2.insert_one(new_concept)
        id_mapping[string_id] = new_id
        
        print(f"  Created new concept with ObjectId: {new_id}")
        
        # Update all references
        # Update parent references
        result = db.tag_concepts_v2.update_many(
            {'parents': string_id},
            {'$set': {'parents.$': new_id}}
        )
        if result.modified_count:
            print(f"  Updated {result.modified_count} parent references")
        
        # Update child references
        result = db.tag_concepts_v2.update_many(
            {'children': string_id},
            {'$set': {'children.$': new_id}}
        )
        if result.modified_count:
            print(f"  Updated {result.modified_count} child references")
        
        # Update tag_instances
        result = db.tag_instances.update_many(
            {'concept_id': string_id},
            {'$set': {'concept_id': str(new_id)}}
        )
        if result.modified_count:
            print(f"  Updated {result.modified_count} tag instances")
        
        # Delete the old string ID concept
        db.tag_concepts_v2.delete_one({'_id': string_id})
        print(f"  Deleted string ID concept")

# Final validation
print("\n" + "-" * 40)
print("FINAL VALIDATION...")
print("-" * 40)

# Check for remaining string IDs
remaining_string_ids = db.tag_concepts_v2.count_documents({'_id': {'$type': 'string'}})
print(f"Concepts with string _id: {remaining_string_ids}")

# Check for string references
all_concepts = list(db.tag_concepts_v2.find())
string_refs = 0

for concept in all_concepts:
    if 'parents' in concept and concept['parents']:
        for parent in concept['parents']:
            if isinstance(parent, str):
                string_refs += 1
    if 'children' in concept and concept['children']:
        for child in concept['children']:
            if isinstance(child, str):
                string_refs += 1

print(f"String references in parents/children: {string_refs}")

if remaining_string_ids == 0 and string_refs == 0:
    print("\n✅ SUCCESS! All concepts now use ObjectIds!")
else:
    print(f"\n⚠️ Still have {remaining_string_ids} string IDs and {string_refs} string references")

print("\n" + "=" * 60)
print("MERGE COMPLETE")
print("=" * 60)