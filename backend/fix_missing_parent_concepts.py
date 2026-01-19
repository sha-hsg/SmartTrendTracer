#!/usr/bin/env python3
"""
Create missing parent concepts and fix references
"""

from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

client = MongoClient('mongodb://localhost:27017/')
db = client.smarttrendtracer

print("=" * 60)
print("CREATING MISSING PARENT CONCEPTS")
print("=" * 60)

# Map of missing parent slugs to proper display names
missing_parents = {
    'c_content_types': 'Content Types',
    'c_models_and_architectures': 'Models and Architectures',
    'c_fundamentals': 'AI/ML Fundamentals',
    'c_techniques_and_methods': 'Techniques and Methods'
}

# Find the root AI/ML Fundamentals concept
root_concept = db.tag_concepts_v2.find_one({'slug': 'ai_ml_fundamentals'})
if not root_concept:
    root_concept = db.tag_concepts_v2.find_one({'display_name': 'AI/ML Fundamentals'})

print(f"\nRoot concept found: {root_concept['display_name'] if root_concept else 'None'}")

# Create missing parent concepts
created_concepts = {}

for slug, display_name in missing_parents.items():
    # Check if concept already exists
    existing = db.tag_concepts_v2.find_one({
        '$or': [
            {'slug': slug},
            {'slug': slug.replace('c_', '')},
            {'display_name': display_name}
        ]
    })
    
    if existing:
        print(f"\n✓ Concept '{display_name}' already exists (ID: {existing['_id']})")
        created_concepts[slug] = existing['_id']
    else:
        # Create the concept
        new_concept = {
            '_id': ObjectId(),
            'slug': slug.replace('c_', ''),
            'display_name': display_name,
            'description': f"Parent category for {display_name.lower()}",
            'parents': [root_concept['_id']] if root_concept else [],
            'children': [],
            'entity_type': 'category',
            'usage_count': 0,
            'created_at': datetime.utcnow(),
            'created_by': 'system',
            'auto_generated': False
        }
        
        db.tag_concepts_v2.insert_one(new_concept)
        created_concepts[slug] = new_concept['_id']
        print(f"\n✨ Created concept '{display_name}' (ID: {new_concept['_id']})")
        
        # Add to root's children if root exists
        if root_concept:
            db.tag_concepts_v2.update_one(
                {'_id': root_concept['_id']},
                {'$addToSet': {'children': new_concept['_id']}}
            )

# Now fix all the string references
print("\n" + "-" * 40)
print("FIXING STRING REFERENCES...")
print("-" * 40)

all_concepts = list(db.tag_concepts_v2.find())
fixed_count = 0

for concept in all_concepts:
    updates = {}
    
    # Fix parents
    if 'parents' in concept and concept['parents']:
        new_parents = []
        changed = False
        
        for parent in concept['parents']:
            if isinstance(parent, str):
                # Try to map it to a created concept
                if parent in created_concepts:
                    new_parents.append(created_concepts[parent])
                    changed = True
                    fixed_count += 1
                    print(f"  Fixed: {concept['display_name']} -> parent: {parent}")
                elif len(parent) == 24 and all(c in '0123456789abcdef' for c in parent.lower()):
                    # Valid hex string, convert to ObjectId
                    new_parents.append(ObjectId(parent))
                    changed = True
                else:
                    # Skip invalid reference
                    pass
            else:
                # Already an ObjectId
                new_parents.append(parent)
        
        if changed:
            updates['parents'] = new_parents
    
    # Apply updates
    if updates:
        db.tag_concepts_v2.update_one(
            {'_id': concept['_id']},
            {'$set': updates}
        )

print(f"\nFixed {fixed_count} string references")

# Ensure the created concepts have their children properly set
print("\n" + "-" * 40)
print("UPDATING CHILDREN RELATIONSHIPS...")
print("-" * 40)

for slug, concept_id in created_concepts.items():
    # Find all concepts that have this as a parent
    children = list(db.tag_concepts_v2.find({'parents': concept_id}))
    child_ids = [c['_id'] for c in children]
    
    if child_ids:
        db.tag_concepts_v2.update_one(
            {'_id': concept_id},
            {'$set': {'children': child_ids}}
        )
        print(f"  {missing_parents[slug]}: {len(child_ids)} children")

# Final validation
print("\n" + "-" * 40)
print("FINAL VALIDATION...")
print("-" * 40)

# Check for remaining string IDs
remaining_issues = 0
all_concepts = list(db.tag_concepts_v2.find())

for concept in all_concepts:
    if 'parents' in concept and concept['parents']:
        for parent in concept['parents']:
            if isinstance(parent, str):
                remaining_issues += 1
                print(f"  Still string: {concept['display_name']} -> parent: {parent}")

if remaining_issues == 0:
    print("✅ All parent references are now proper ObjectIds!")
else:
    print(f"⚠️ Still {remaining_issues} string references remaining")

print("\n" + "=" * 60)
print("MISSING PARENT CONCEPTS FIX COMPLETE")
print("=" * 60)