#!/usr/bin/env python3
"""
Migrate concepts with string _id to proper ObjectIds
This is a critical fix as MongoDB should always use ObjectIds for _id fields
"""

from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

client = MongoClient('mongodb://localhost:27017/')
db = client.smarttrendtracer

print("=" * 60)
print("MIGRATING STRING _id FIELDS TO ObjectIds")
print("=" * 60)

# Find all concepts with string _id
all_concepts = list(db.tag_concepts_v2.find())
string_id_concepts = []

for concept in all_concepts:
    if isinstance(concept['_id'], str):
        string_id_concepts.append(concept)

print(f"\nFound {len(string_id_concepts)} concepts with string _id fields:")
for c in string_id_concepts[:10]:
    print(f"  - {c['_id']}: {c.get('display_name', c.get('slug'))}")

if not string_id_concepts:
    print("✅ All concepts already have ObjectId _id fields!")
    exit(0)

# Create mapping from old string ID to new ObjectId
id_migration_map = {}

print("\n" + "-" * 40)
print("MIGRATING CONCEPTS TO ObjectIds...")
print("-" * 40)

for old_concept in string_id_concepts:
    old_id = old_concept['_id']
    new_id = ObjectId()
    
    # Create new concept with ObjectId
    new_concept = dict(old_concept)
    new_concept['_id'] = new_id
    new_concept['_old_string_id'] = old_id  # Keep track of old ID
    
    # Insert new concept
    try:
        db.tag_concepts_v2.insert_one(new_concept)
        id_migration_map[old_id] = new_id
        print(f"  Migrated: {old_id} -> {new_id} ({new_concept.get('display_name')})")
    except Exception as e:
        print(f"  Error migrating {old_id}: {e}")

# Now update all references to these concepts
print("\n" + "-" * 40)
print("UPDATING REFERENCES TO MIGRATED CONCEPTS...")
print("-" * 40)

# Update parent/child references in all concepts
all_concepts = list(db.tag_concepts_v2.find())
references_updated = 0

for concept in all_concepts:
    updates = {}
    
    # Update parents
    if 'parents' in concept and concept['parents']:
        new_parents = []
        changed = False
        
        for parent in concept['parents']:
            if parent in id_migration_map:
                new_parents.append(id_migration_map[parent])
                changed = True
                references_updated += 1
            else:
                new_parents.append(parent)
        
        if changed:
            updates['parents'] = new_parents
    
    # Update children
    if 'children' in concept and concept['children']:
        new_children = []
        changed = False
        
        for child in concept['children']:
            if child in id_migration_map:
                new_children.append(id_migration_map[child])
                changed = True
                references_updated += 1
            else:
                new_children.append(child)
        
        if changed:
            updates['children'] = new_children
    
    # Apply updates
    if updates:
        db.tag_concepts_v2.update_one(
            {'_id': concept['_id']},
            {'$set': updates}
        )

print(f"Updated {references_updated} references")

# Update tag_instances references
print("\n" + "-" * 40)
print("UPDATING TAG INSTANCES...")
print("-" * 40)

instances_updated = 0
for old_id, new_id in id_migration_map.items():
    result = db.tag_instances.update_many(
        {'concept_id': old_id},
        {'$set': {'concept_id': str(new_id)}}
    )
    if result.modified_count > 0:
        instances_updated += result.modified_count
        print(f"  Updated {result.modified_count} instances for {old_id}")

print(f"Total instances updated: {instances_updated}")

# Update tag_aliases references
print("\n" + "-" * 40)
print("UPDATING TAG ALIASES...")
print("-" * 40)

aliases_updated = 0
for old_id, new_id in id_migration_map.items():
    result = db.tag_aliases_v2.update_many(
        {'concept_id': old_id},
        {'$set': {'concept_id': new_id}}
    )
    if result.modified_count > 0:
        aliases_updated += result.modified_count
        print(f"  Updated {result.modified_count} aliases for {old_id}")

print(f"Total aliases updated: {aliases_updated}")

# Delete old string ID concepts
print("\n" + "-" * 40)
print("REMOVING OLD STRING ID CONCEPTS...")
print("-" * 40)

for old_id in id_migration_map.keys():
    result = db.tag_concepts_v2.delete_one({'_id': old_id})
    if result.deleted_count > 0:
        print(f"  Deleted old concept: {old_id}")

# Final validation
print("\n" + "-" * 40)
print("FINAL VALIDATION...")
print("-" * 40)

# Check for any remaining string _id fields
all_concepts = list(db.tag_concepts_v2.find())
remaining_string_ids = [c for c in all_concepts if isinstance(c['_id'], str)]

if not remaining_string_ids:
    print("✅ SUCCESS! All concepts now have ObjectId _id fields!")
else:
    print(f"⚠️ Still {len(remaining_string_ids)} concepts with string _id fields")
    for c in remaining_string_ids[:5]:
        print(f"  - {c['_id']}: {c.get('display_name')}")

# Check for any remaining string references
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

print(f"\nRemaining string references in parents/children: {string_refs}")

print("\n" + "=" * 60)
print("MIGRATION COMPLETE")
print("=" * 60)