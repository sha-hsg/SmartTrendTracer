#!/usr/bin/env python3
"""
Final fix for all string IDs - convert string concept IDs to ObjectIds
"""

from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

client = MongoClient('mongodb://localhost:27017/')
db = client.smarttrendtracer

print("=" * 60)
print("FINAL FIX FOR ALL STRING IDs")
print("=" * 60)

# Get all concepts and create mappings
all_concepts = list(db.tag_concepts_v2.find())

# Create multiple mappings for lookup
id_mappings = {}
for c in all_concepts:
    # Map by string ID
    if '_id' in c:
        id_mappings[str(c['_id'])] = c['_id']
    
    # Map by slug
    if 'slug' in c:
        id_mappings[c['slug']] = c['_id']
    
    # Map by special c_ prefixed slugs
    if 'slug' in c:
        id_mappings[f"c_{c['slug']}"] = c['_id']
    
    # Map by display_name converted to slug format
    if 'display_name' in c:
        slug_from_display = c['display_name'].lower().replace(' ', '_').replace('/', '_').replace('&', 'and')
        id_mappings[slug_from_display] = c['_id']
        id_mappings[f"c_{slug_from_display}"] = c['_id']

# Special manual mappings for known issues
special_mappings = {
    'c_named_entities': 'named_entities',
    'c_research_entities': 'research_entities',
    'c_content_types': 'content_types'
}

# Try to find these special concepts
for special_key, search_slug in special_mappings.items():
    concept = db.tag_concepts_v2.find_one({
        '$or': [
            {'slug': search_slug},
            {'display_name': search_slug.replace('_', ' ').title()}
        ]
    })
    if concept:
        id_mappings[special_key] = concept['_id']
        print(f"Mapped {special_key} -> {concept['_id']}")

print(f"\nCreated {len(id_mappings)} ID mappings")

# Now fix all string references
print("\nFIXING ALL STRING REFERENCES...")
print("-" * 40)

total_fixed = 0
unfixable = []

for concept in all_concepts:
    updates = {}
    
    # Fix parents
    if 'parents' in concept and concept['parents']:
        new_parents = []
        changed = False
        
        for parent in concept['parents']:
            if isinstance(parent, str):
                if parent in id_mappings:
                    # Found mapping
                    new_parents.append(id_mappings[parent])
                    changed = True
                    total_fixed += 1
                    print(f"  Fixed: {concept.get('display_name', concept.get('slug'))} -> parent: {parent}")
                else:
                    # Can't map - record it
                    unfixable.append({
                        'concept': concept.get('display_name', concept.get('slug')),
                        'field': 'parents',
                        'value': parent
                    })
            elif isinstance(parent, ObjectId):
                # Already an ObjectId
                new_parents.append(parent)
        
        if changed or len(new_parents) != len(concept['parents']):
            updates['parents'] = new_parents
    
    # Fix children
    if 'children' in concept and concept['children']:
        new_children = []
        changed = False
        
        for child in concept['children']:
            if isinstance(child, str):
                if child in id_mappings:
                    # Found mapping
                    new_children.append(id_mappings[child])
                    changed = True
                    total_fixed += 1
                    print(f"  Fixed: {concept.get('display_name', concept.get('slug'))} -> child: {child}")
                else:
                    # Can't map - record it
                    unfixable.append({
                        'concept': concept.get('display_name', concept.get('slug')),
                        'field': 'children',
                        'value': child
                    })
            elif isinstance(child, ObjectId):
                # Already an ObjectId
                new_children.append(child)
        
        if changed or len(new_children) != len(concept['children']):
            updates['children'] = new_children
    
    # Apply updates
    if updates:
        db.tag_concepts_v2.update_one(
            {'_id': concept['_id']},
            {'$set': updates}
        )

print(f"\nTotal fixed: {total_fixed} string references")

if unfixable:
    print(f"\nUnfixable references ({len(unfixable)}):")
    # Group by value to see patterns
    unfixable_by_value = {}
    for item in unfixable:
        if item['value'] not in unfixable_by_value:
            unfixable_by_value[item['value']] = []
        unfixable_by_value[item['value']].append(item['concept'])
    
    for value, concepts in list(unfixable_by_value.items())[:10]:
        print(f"  '{value}' referenced by: {', '.join(concepts[:3])}")

# Final validation
print("\n" + "-" * 40)
print("FINAL VALIDATION...")
print("-" * 40)

all_concepts = list(db.tag_concepts_v2.find())
remaining_string_ids = 0

for concept in all_concepts:
    if 'parents' in concept and concept['parents']:
        for parent in concept['parents']:
            if isinstance(parent, str):
                remaining_string_ids += 1
    
    if 'children' in concept and concept['children']:
        for child in concept['children']:
            if isinstance(child, str):
                remaining_string_ids += 1

if remaining_string_ids == 0:
    print("✅ SUCCESS! All parent-child references are now ObjectIds!")
else:
    print(f"⚠️ Still {remaining_string_ids} string references remaining")

print("\n" + "=" * 60)
print("STRING ID FIX COMPLETE")
print("=" * 60)