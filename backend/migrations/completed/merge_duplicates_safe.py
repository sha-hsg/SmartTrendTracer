#!/usr/bin/env python3
"""
Safely detect and merge duplicate concepts
Handles unique constraint violations
"""

from pymongo import MongoClient
from bson import ObjectId
from difflib import SequenceMatcher
import re

client = MongoClient('mongodb://localhost:27017/')
db = client.smarttrendtracer

print("=" * 60)
print("SAFELY MERGING DUPLICATE CONCEPTS")
print("=" * 60)

def normalize_name(name):
    """Normalize name for comparison"""
    normalized = name.lower()
    normalized = re.sub(r'[^\w\s]', '', normalized)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized

def similarity(a, b):
    """Calculate similarity between two strings"""
    return SequenceMatcher(None, normalize_name(a), normalize_name(b)).ratio()

# Get all concepts
all_concepts = list(db.tag_concepts_v2.find())
print(f"\nAnalyzing {len(all_concepts)} concepts for exact duplicates...")

# Find exact duplicates only
exact_duplicates = []
checked_pairs = set()

for i, concept1 in enumerate(all_concepts):
    for concept2 in all_concepts[i+1:]:
        pair_key = tuple(sorted([str(concept1['_id']), str(concept2['_id'])]))
        if pair_key in checked_pairs:
            continue
        checked_pairs.add(pair_key)
        
        name1 = concept1.get('display_name', concept1.get('slug', ''))
        name2 = concept2.get('display_name', concept2.get('slug', ''))
        
        if not name1 or not name2:
            continue
        
        # Only exact matches after normalization
        if normalize_name(name1) == normalize_name(name2):
            exact_duplicates.append({
                'concept1': {'id': concept1['_id'], 'name': name1, 'usage': concept1.get('usage_count', 0)},
                'concept2': {'id': concept2['_id'], 'name': name2, 'usage': concept2.get('usage_count', 0)}
            })

print(f"\nFound {len(exact_duplicates)} exact duplicate pairs")

# Merge exact duplicates safely
merged_count = 0
failed_merges = []

for dup in exact_duplicates:
    # Keep the one with higher usage count
    if dup['concept1']['usage'] >= dup['concept2']['usage']:
        primary = dup['concept1']
        secondary = dup['concept2']
    else:
        primary = dup['concept2']
        secondary = dup['concept1']
    
    print(f"\nMerging '{secondary['name']}' into '{primary['name']}'...")
    
    try:
        # First, find and delete any duplicate tag_instances that would cause conflicts
        # Get all instances for the secondary concept
        secondary_instances = list(db.tag_instances.find({'concept_id': str(secondary['id'])}))
        
        for instance in secondary_instances:
            # Check if a similar instance already exists for the primary concept
            existing = db.tag_instances.find_one({
                'content_type': instance['content_type'],
                'content_id': instance['content_id'],
                'concept_id': str(primary['id'])
            })
            
            if existing:
                # Delete the duplicate instance
                db.tag_instances.delete_one({'_id': instance['_id']})
                print(f"  Deleted duplicate instance for {instance['content_type']} {instance['content_id']}")
            else:
                # Update to use primary concept
                db.tag_instances.update_one(
                    {'_id': instance['_id']},
                    {'$set': {'concept_id': str(primary['id'])}}
                )
        
        # Transfer usage count
        if secondary['usage'] > 0:
            db.tag_concepts_v2.update_one(
                {'_id': primary['id']},
                {'$inc': {'usage_count': secondary['usage']}}
            )
            print(f"  Transferred {secondary['usage']} usage count")
        
        # Update parent references
        db.tag_concepts_v2.update_many(
            {'children': secondary['id']},
            {'$set': {'children.$': primary['id']}}
        )
        
        # Update child references
        db.tag_concepts_v2.update_many(
            {'parents': secondary['id']},
            {'$set': {'parents.$': primary['id']}}
        )
        
        # Merge children lists
        secondary_concept = db.tag_concepts_v2.find_one({'_id': secondary['id']})
        if secondary_concept and secondary_concept.get('children'):
            # Remove duplicates when merging
            db.tag_concepts_v2.update_one(
                {'_id': primary['id']},
                {'$addToSet': {'children': {'$each': secondary_concept['children']}}}
            )
        
        # Delete the duplicate concept
        db.tag_concepts_v2.delete_one({'_id': secondary['id']})
        print(f"  ✅ Successfully merged")
        merged_count += 1
        
    except Exception as e:
        print(f"  ❌ Failed to merge: {e}")
        failed_merges.append({
            'primary': primary['name'],
            'secondary': secondary['name'],
            'error': str(e)
        })

print(f"\n" + "-" * 40)
print("MERGE RESULTS")
print("-" * 40)
print(f"Successfully merged: {merged_count} pairs")
print(f"Failed merges: {len(failed_merges)}")

if failed_merges:
    print("\nFailed merges:")
    for fail in failed_merges[:5]:
        print(f"  - {fail['secondary']} → {fail['primary']}: {fail['error'][:50]}...")

# Final statistics
print("\n" + "-" * 40)
print("FINAL STATISTICS")
print("-" * 40)

final_concept_count = db.tag_concepts_v2.count_documents({})
print(f"Final concept count: {final_concept_count}")
print(f"Concepts removed: {merged_count}")

# Recalculate usage counts
print("\nRecalculating usage counts...")
concepts_updated = 0

for concept in db.tag_concepts_v2.find():
    actual_count = db.tag_instances.count_documents({'concept_id': str(concept['_id'])})
    if actual_count != concept.get('usage_count', 0):
        db.tag_concepts_v2.update_one(
            {'_id': concept['_id']},
            {'$set': {'usage_count': actual_count}}
        )
        concepts_updated += 1

print(f"Updated {concepts_updated} usage counts")

print("\n" + "=" * 60)
print("SAFE MERGE COMPLETE")
print("=" * 60)