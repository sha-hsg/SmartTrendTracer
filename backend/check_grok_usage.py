#!/usr/bin/env python3
"""
Check why Grok-2.5 shows 0 usage
"""

from pymongo import MongoClient
from bson import ObjectId

client = MongoClient('mongodb://localhost:27017/')
db = client.smarttrendtracer

print("=" * 60)
print("INVESTIGATING GROK USAGE STATISTICS")
print("=" * 60)

# Find all Grok-related concepts
print("\n1. ALL GROK-RELATED CONCEPTS...")
print("-" * 40)

grok_concepts = list(db.tag_concepts_v2.find({
    "$or": [
        {"display_name": {"$regex": "Grok", "$options": "i"}},
        {"slug": {"$regex": "grok", "$options": "i"}}
    ]
}))

for concept in grok_concepts:
    print(f"\nConcept: {concept['display_name']}")
    print(f"  ID: {concept['_id']}")
    print(f"  Slug: {concept.get('slug')}")
    print(f"  Usage count: {concept.get('usage_count', 0)}")
    
    # Check actual instances
    concept_id_str = str(concept['_id'])
    instances = list(db.tag_instances.find({"concept_id": concept_id_str}))
    print(f"  Actual instances: {len(instances)}")
    
    # Check if there are any aliases
    aliases = list(db.tag_aliases_v2.find({"concept_id": concept['_id']}))
    if aliases:
        print(f"  Aliases: {[a['alias_text'] for a in aliases]}")

# Check for any tag_instances with Grok in the tag_text
print("\n2. TAG INSTANCES WITH 'GROK' IN TEXT...")
print("-" * 40)

grok_instances = list(db.tag_instances.find({
    "tag_text": {"$regex": "Grok", "$options": "i"}
}).limit(10))

print(f"Found {len(grok_instances)} instances with 'Grok' in tag_text")
for instance in grok_instances:
    print(f"  - Tag: '{instance['tag_text']}'")
    print(f"    Concept ID: {instance.get('concept_id')}")
    print(f"    Content type: {instance.get('content_type')}")
    
    # Check if the concept exists
    if instance.get('concept_id'):
        concept = db.tag_concepts_v2.find_one({"_id": ObjectId(instance['concept_id'])} if len(instance['concept_id']) == 24 else {"_id": instance['concept_id']})
        if concept:
            print(f"    Maps to: {concept['display_name']}")
        else:
            print(f"    ⚠️ Concept not found!")

# Check if there's a mismatch problem
print("\n3. CHECKING FOR DUPLICATES OR MISMATCHES...")
print("-" * 40)

# Get all unique Grok variations in tag_instances
pipeline = [
    {"$match": {"tag_text": {"$regex": "Grok", "$options": "i"}}},
    {"$group": {"_id": "$tag_text", "count": {"$sum": 1}}}
]

variations = list(db.tag_instances.aggregate(pipeline))
print(f"Unique Grok variations in tag_instances:")
for var in sorted(variations, key=lambda x: x['count'], reverse=True):
    print(f"  '{var['_id']}': {var['count']} instances")

# Check if we need to consolidate
print("\n4. SUGGESTED FIXES...")
print("-" * 40)

# Find the main Grok concepts that should be consolidated
grok_25 = db.tag_concepts_v2.find_one({"slug": "grok_25"})
grok_2_5 = db.tag_concepts_v2.find_one({"slug": "grok_2_5"})

if grok_25 and grok_2_5:
    print(f"Found both 'grok_25' and 'grok_2_5' concepts")
    print(f"  'Grok-25' has {grok_25.get('usage_count', 0)} usage")
    print(f"  'Grok-2.5' has {grok_2_5.get('usage_count', 0)} usage")
    print(f"\n  Suggestion: Merge these into one concept with aliases")
    
print("\n" + "=" * 60)
print("INVESTIGATION COMPLETE")
print("=" * 60)