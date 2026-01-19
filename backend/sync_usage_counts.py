#!/usr/bin/env python3
"""
Synchronize usage counts for all concepts
Ensures stored usage_count matches actual tag_instances
"""

from pymongo import MongoClient
from bson import ObjectId

client = MongoClient('mongodb://localhost:27017/')
db = client.smarttrendtracer

print("=" * 60)
print("SYNCHRONIZING USAGE COUNTS")
print("=" * 60)

# Get all concepts
all_concepts = list(db.tag_concepts_v2.find())
print(f"\nProcessing {len(all_concepts)} concepts...")

mismatched = []
zero_but_used = []
total_instances = 0

for concept in all_concepts:
    concept_id = concept['_id']
    concept_id_str = str(concept_id)
    
    # Count actual instances
    actual_count = db.tag_instances.count_documents({'concept_id': concept_id_str})
    stored_count = concept.get('usage_count', 0)
    
    total_instances += actual_count
    
    if actual_count != stored_count:
        mismatched.append({
            'concept': concept.get('display_name', concept.get('slug')),
            'stored': stored_count,
            'actual': actual_count,
            'diff': actual_count - stored_count
        })
        
        # Update the count
        db.tag_concepts_v2.update_one(
            {'_id': concept_id},
            {'$set': {'usage_count': actual_count}}
        )
        
        if stored_count == 0 and actual_count > 0:
            zero_but_used.append(concept.get('display_name', concept.get('slug')))

print(f"\n" + "-" * 40)
print("SYNCHRONIZATION RESULTS")
print("-" * 40)

if mismatched:
    print(f"\nFixed {len(mismatched)} mismatched counts:")
    
    # Sort by difference to show biggest issues first
    mismatched.sort(key=lambda x: abs(x['diff']), reverse=True)
    
    for item in mismatched[:20]:  # Show top 20
        print(f"  {item['concept']}: {item['stored']} → {item['actual']} (diff: {item['diff']:+d})")
    
    if len(mismatched) > 20:
        print(f"  ... and {len(mismatched) - 20} more")
else:
    print("\n✅ All usage counts were already synchronized!")

if zero_but_used:
    print(f"\n{len(zero_but_used)} concepts had 0 count but actual usage:")
    for name in zero_but_used[:10]:
        print(f"  - {name}")
    if len(zero_but_used) > 10:
        print(f"  ... and {len(zero_but_used) - 10} more")

# Summary statistics
print(f"\n" + "-" * 40)
print("FINAL STATISTICS")
print("-" * 40)

# Recount after updates
concepts_with_usage = db.tag_concepts_v2.count_documents({'usage_count': {'$gt': 0}})
concepts_without_usage = db.tag_concepts_v2.count_documents({'usage_count': 0})
total_stored_usage = sum(c.get('usage_count', 0) for c in db.tag_concepts_v2.find())

print(f"Total concepts: {len(all_concepts)}")
print(f"Concepts with usage: {concepts_with_usage}")
print(f"Concepts without usage: {concepts_without_usage}")
print(f"Total tag instances: {total_instances}")
print(f"Total stored usage count: {total_stored_usage}")

if total_instances == total_stored_usage:
    print("\n✅ SUCCESS! All usage counts are now synchronized!")
else:
    print(f"\n⚠️ Warning: Total instances ({total_instances}) != Total stored ({total_stored_usage})")
    print("   This might indicate orphaned tag_instances")

# Check for orphaned instances
print(f"\n" + "-" * 40)
print("CHECKING FOR ORPHANED INSTANCES...")
print("-" * 40)

orphaned_count = db.tag_instances.count_documents({'concept_id': None})
print(f"Instances with null concept_id: {orphaned_count}")

# Check for instances pointing to non-existent concepts
all_concept_ids = {str(c['_id']) for c in all_concepts}
all_instances = list(db.tag_instances.find({'concept_id': {'$ne': None}}, {'concept_id': 1}).limit(10000))

invalid_refs = []
for instance in all_instances:
    if instance['concept_id'] not in all_concept_ids:
        invalid_refs.append(instance['concept_id'])

if invalid_refs:
    unique_invalid = set(invalid_refs)
    print(f"Instances with invalid concept_id: {len(invalid_refs)} ({len(unique_invalid)} unique)")
    for ref in list(unique_invalid)[:5]:
        print(f"  - {ref}")
else:
    print("✅ No invalid concept references found")

print("\n" + "=" * 60)
print("USAGE COUNT SYNCHRONIZATION COMPLETE")
print("=" * 60)