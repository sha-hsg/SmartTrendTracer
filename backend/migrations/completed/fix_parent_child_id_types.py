#!/usr/bin/env python3
"""
Fix parent-child ID type inconsistencies in MongoDB
Converts all string-based parent IDs to proper ObjectIds
"""

from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

client = MongoClient('mongodb://localhost:27017/')
db = client.smarttrendtracer

print("=" * 60)
print("FIXING PARENT-CHILD ID TYPE INCONSISTENCIES")
print("=" * 60)

# First, let's analyze the current state
print("\n1. ANALYZING CURRENT STATE...")
print("-" * 40)

# Find concepts with string parent IDs
concepts_with_issues = []
all_concepts = list(db.tag_concepts_v2.find())

# Create a mapping of all valid concept IDs
valid_concept_ids = {str(c['_id']): c['_id'] for c in all_concepts}
concept_by_slug = {c.get('slug', c.get('tag')): c['_id'] for c in all_concepts}

for concept in all_concepts:
    # Check parents field
    if 'parents' in concept and concept['parents']:
        for i, parent in enumerate(concept['parents']):
            if isinstance(parent, str):
                concepts_with_issues.append({
                    'concept_id': concept['_id'],
                    'concept_name': concept.get('display_name', concept.get('tag')),
                    'field': 'parents',
                    'index': i,
                    'string_value': parent
                })
    
    # Check children field  
    if 'children' in concept and concept['children']:
        for i, child in enumerate(concept['children']):
            if isinstance(child, str):
                concepts_with_issues.append({
                    'concept_id': concept['_id'],
                    'concept_name': concept.get('display_name', concept.get('tag')),
                    'field': 'children', 
                    'index': i,
                    'string_value': child
                })

print(f"Found {len(concepts_with_issues)} string ID references to fix")

if concepts_with_issues:
    print("\nSample issues (first 5):")
    for issue in concepts_with_issues[:5]:
        print(f"  - {issue['concept_name']}: {issue['field']}[{issue['index']}] = '{issue['string_value']}'")

# Now fix the issues
print("\n2. FIXING ID TYPE INCONSISTENCIES...")
print("-" * 40)

fixed_count = 0
unfixable_count = 0
unfixable_refs = []

for concept in all_concepts:
    updates = {}
    
    # Fix parents
    if 'parents' in concept and concept['parents']:
        new_parents = []
        for parent in concept['parents']:
            if isinstance(parent, str):
                # Try to convert to ObjectId
                if len(parent) == 24 and all(c in '0123456789abcdef' for c in parent.lower()):
                    # Valid ObjectId hex string
                    new_parents.append(ObjectId(parent))
                    fixed_count += 1
                elif parent in valid_concept_ids:
                    # It's a string ID that maps to a real concept
                    new_parents.append(valid_concept_ids[parent])
                    fixed_count += 1
                elif parent in concept_by_slug:
                    # It's a slug that maps to a real concept
                    new_parents.append(concept_by_slug[parent])
                    fixed_count += 1
                else:
                    # Can't resolve this reference - skip it
                    unfixable_count += 1
                    unfixable_refs.append({
                        'concept': concept.get('display_name'),
                        'field': 'parents',
                        'value': parent
                    })
            else:
                # Already an ObjectId
                new_parents.append(parent)
        
        if new_parents != concept['parents']:
            updates['parents'] = new_parents
    
    # Fix children
    if 'children' in concept and concept['children']:
        new_children = []
        for child in concept['children']:
            if isinstance(child, str):
                # Try to convert to ObjectId
                if len(child) == 24 and all(c in '0123456789abcdef' for c in child.lower()):
                    # Valid ObjectId hex string
                    new_children.append(ObjectId(child))
                    fixed_count += 1
                elif child in valid_concept_ids:
                    # It's a string ID that maps to a real concept
                    new_children.append(valid_concept_ids[child])
                    fixed_count += 1
                elif child in concept_by_slug:
                    # It's a slug that maps to a real concept
                    new_children.append(concept_by_slug[child])
                    fixed_count += 1
                else:
                    # Can't resolve this reference - skip it
                    unfixable_count += 1
                    unfixable_refs.append({
                        'concept': concept.get('display_name'),
                        'field': 'children',
                        'value': child
                    })
            else:
                # Already an ObjectId
                new_children.append(child)
        
        if new_children != concept['children']:
            updates['children'] = new_children
    
    # Apply updates if any
    if updates:
        db.tag_concepts_v2.update_one(
            {'_id': concept['_id']},
            {'$set': updates}
        )

print(f"\nFixed {fixed_count} string ID references")
print(f"Could not resolve {unfixable_count} references")

if unfixable_refs:
    print("\nUnfixable references (first 10):")
    for ref in unfixable_refs[:10]:
        print(f"  - {ref['concept']} -> {ref['field']}: '{ref['value']}'")

# Ensure bidirectional consistency
print("\n3. ENSURING BIDIRECTIONAL CONSISTENCY...")
print("-" * 40)

# Reload concepts after fixes
all_concepts = list(db.tag_concepts_v2.find())
concepts_by_id = {c['_id']: c for c in all_concepts}

inconsistencies_fixed = 0

for concept in all_concepts:
    concept_id = concept['_id']
    
    # Check parent -> child consistency
    if 'parents' in concept and concept['parents']:
        for parent_id in concept['parents']:
            if parent_id in concepts_by_id:
                parent = concepts_by_id[parent_id]
                if 'children' not in parent:
                    parent['children'] = []
                if concept_id not in parent['children']:
                    # Add this concept as a child of its parent
                    db.tag_concepts_v2.update_one(
                        {'_id': parent_id},
                        {'$addToSet': {'children': concept_id}}
                    )
                    inconsistencies_fixed += 1
    
    # Check child -> parent consistency
    if 'children' in concept and concept['children']:
        for child_id in concept['children']:
            if child_id in concepts_by_id:
                child = concepts_by_id[child_id]
                if 'parents' not in child:
                    child['parents'] = []
                if concept_id not in child['parents']:
                    # Add this concept as a parent of its child
                    db.tag_concepts_v2.update_one(
                        {'_id': child_id},
                        {'$addToSet': {'parents': concept_id}}
                    )
                    inconsistencies_fixed += 1

print(f"Fixed {inconsistencies_fixed} bidirectional inconsistencies")

# Final validation
print("\n4. FINAL VALIDATION...")
print("-" * 40)

# Check for any remaining string IDs
remaining_issues = 0
all_concepts = list(db.tag_concepts_v2.find())

for concept in all_concepts:
    if 'parents' in concept and concept['parents']:
        for parent in concept['parents']:
            if isinstance(parent, str):
                remaining_issues += 1
    
    if 'children' in concept and concept['children']:
        for child in concept['children']:
            if isinstance(child, str):
                remaining_issues += 1

if remaining_issues == 0:
    print("✅ All parent-child references are now proper ObjectIds!")
else:
    print(f"⚠️ Still {remaining_issues} string references remaining (likely invalid references)")

# Count final statistics
total_parent_refs = sum(len(c.get('parents', [])) for c in all_concepts)
total_child_refs = sum(len(c.get('children', [])) for c in all_concepts)

print(f"\nFinal statistics:")
print(f"  Total concepts: {len(all_concepts)}")
print(f"  Total parent references: {total_parent_refs}")
print(f"  Total child references: {total_child_refs}")

print("\n" + "=" * 60)
print("PARENT-CHILD ID TYPE FIX COMPLETE")
print("=" * 60)