#!/usr/bin/env python3
"""
Detect and merge duplicate concepts based on similar names
"""

from pymongo import MongoClient
from bson import ObjectId
from difflib import SequenceMatcher
import re

client = MongoClient('mongodb://localhost:27017/')
db = client.smarttrendtracer

print("=" * 60)
print("DETECTING AND MERGING DUPLICATE CONCEPTS")
print("=" * 60)

def normalize_name(name):
    """Normalize name for comparison"""
    # Convert to lowercase
    normalized = name.lower()
    # Remove special characters but keep spaces
    normalized = re.sub(r'[^\w\s]', '', normalized)
    # Replace multiple spaces with single space
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized

def similarity(a, b):
    """Calculate similarity between two strings"""
    return SequenceMatcher(None, normalize_name(a), normalize_name(b)).ratio()

# Get all concepts
all_concepts = list(db.tag_concepts_v2.find())
print(f"\nAnalyzing {len(all_concepts)} concepts for duplicates...")

# Find potential duplicates
potential_duplicates = []
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
        
        # Check for high similarity
        sim = similarity(name1, name2)
        if sim > 0.85:  # 85% similarity threshold
            potential_duplicates.append({
                'concept1': {'id': concept1['_id'], 'name': name1, 'usage': concept1.get('usage_count', 0)},
                'concept2': {'id': concept2['_id'], 'name': name2, 'usage': concept2.get('usage_count', 0)},
                'similarity': sim
            })

# Sort by similarity
potential_duplicates.sort(key=lambda x: x['similarity'], reverse=True)

if not potential_duplicates:
    print("\n✅ No duplicate concepts found!")
else:
    print(f"\nFound {len(potential_duplicates)} potential duplicate pairs:")
    print("-" * 40)
    
    # Show all duplicates
    for dup in potential_duplicates:
        print(f"\n'{dup['concept1']['name']}' (usage: {dup['concept1']['usage']})")
        print(f"  ↔ '{dup['concept2']['name']}' (usage: {dup['concept2']['usage']})")
        print(f"  Similarity: {dup['similarity']:.2%}")

# Auto-merge exact duplicates (100% similarity)
print("\n" + "-" * 40)
print("AUTO-MERGING EXACT DUPLICATES...")
print("-" * 40)

merged_count = 0
for dup in potential_duplicates:
    if dup['similarity'] >= 1.0:  # Exact match after normalization
        # Keep the one with higher usage count
        if dup['concept1']['usage'] >= dup['concept2']['usage']:
            primary = dup['concept1']
            secondary = dup['concept2']
        else:
            primary = dup['concept2']
            secondary = dup['concept1']
        
        print(f"\nMerging '{secondary['name']}' into '{primary['name']}'")
        
        # Transfer usage count
        if secondary['usage'] > 0:
            db.tag_concepts_v2.update_one(
                {'_id': primary['id']},
                {'$inc': {'usage_count': secondary['usage']}}
            )
            print(f"  Transferred {secondary['usage']} usage count")
        
        # Transfer tag_instances
        result = db.tag_instances.update_many(
            {'concept_id': str(secondary['id'])},
            {'$set': {'concept_id': str(primary['id'])}}
        )
        if result.modified_count > 0:
            print(f"  Transferred {result.modified_count} tag instances")
        
        # Transfer parent references
        result = db.tag_concepts_v2.update_many(
            {'children': secondary['id']},
            {'$set': {'children.$': primary['id']}}
        )
        if result.modified_count > 0:
            print(f"  Updated {result.modified_count} parent references")
        
        # Transfer child references
        result = db.tag_concepts_v2.update_many(
            {'parents': secondary['id']},
            {'$set': {'parents.$': primary['id']}}
        )
        if result.modified_count > 0:
            print(f"  Updated {result.modified_count} child references")
        
        # Merge children lists
        secondary_concept = db.tag_concepts_v2.find_one({'_id': secondary['id']})
        if secondary_concept and secondary_concept.get('children'):
            db.tag_concepts_v2.update_one(
                {'_id': primary['id']},
                {'$addToSet': {'children': {'$each': secondary_concept['children']}}}
            )
        
        # Delete the duplicate
        db.tag_concepts_v2.delete_one({'_id': secondary['id']})
        print(f"  Deleted duplicate concept")
        merged_count += 1

print(f"\nMerged {merged_count} exact duplicate pairs")

# Check for special cases that need manual review
print("\n" + "-" * 40)
print("CONCEPTS REQUIRING MANUAL REVIEW...")
print("-" * 40)

# Find similar but not exact matches
review_needed = [d for d in potential_duplicates if 0.85 < d['similarity'] < 1.0]

if review_needed:
    print(f"\n{len(review_needed)} pairs need manual review (85-99% similar):")
    for dup in review_needed[:10]:  # Show first 10
        print(f"\n  '{dup['concept1']['name']}' vs '{dup['concept2']['name']}'")
        print(f"    Similarity: {dup['similarity']:.2%}")
        print(f"    Usage: {dup['concept1']['usage']} vs {dup['concept2']['usage']}")
    
    if len(review_needed) > 10:
        print(f"\n  ... and {len(review_needed) - 10} more pairs")

# Final statistics
print("\n" + "=" * 60)
print("DUPLICATE DETECTION COMPLETE")
print("=" * 60)

final_concept_count = db.tag_concepts_v2.count_documents({})
print(f"\nFinal concept count: {final_concept_count}")
print(f"Concepts removed: {len(all_concepts) - final_concept_count}")
print(f"Exact duplicates merged: {merged_count}")
print(f"Pairs needing manual review: {len(review_needed)}")