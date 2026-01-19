#!/usr/bin/env python3
"""
Consolidate duplicate Grok concepts
"""

from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

client = MongoClient('mongodb://localhost:27017/')
db = client.smarttrendtracer

print("=" * 60)
print("CONSOLIDATING GROK CONCEPTS")
print("=" * 60)

# Find all Grok concepts
grok_concepts = list(db.tag_concepts_v2.find({
    "$or": [
        {"display_name": {"$regex": "^Grok", "$options": "i"}},
        {"slug": {"$regex": "^grok", "$options": "i"}}
    ]
}))

print(f"\nFound {len(grok_concepts)} Grok concepts:")
for c in grok_concepts:
    print(f"  - {c['display_name']} (slug: {c.get('slug')}, usage: {c.get('usage_count', 0)})")

# Consolidation mapping
consolidations = [
    {
        "primary": "Grok-25",  # Keep the one with usage
        "slug": "grok_25",
        "display": "Grok-2.5",  # Better display name
        "duplicates": ["Grok-2.5", "Grok 25", "Grok2.5"],
        "aliases": ["Grok-25", "Grok-2.5", "Grok 2.5", "grok25", "grok2.5"]
    },
    {
        "primary": "Grok-2",
        "slug": "grok_2", 
        "display": "Grok-2",
        "duplicates": ["Grok2", "Grok 2"],
        "aliases": ["Grok-2", "Grok2", "Grok 2", "grok2"]
    }
]

print("\n" + "-" * 40)
print("CONSOLIDATING...")
print("-" * 40)

for consolidation in consolidations:
    print(f"\nProcessing {consolidation['display']}...")
    
    # Find primary concept
    primary = db.tag_concepts_v2.find_one({"slug": consolidation['slug']})
    if not primary:
        primary = db.tag_concepts_v2.find_one({"display_name": consolidation['primary']})
    
    if not primary:
        print(f"  ⚠️ Primary concept not found")
        continue
    
    print(f"  Primary: {primary['display_name']} (ID: {primary['_id']})")
    
    # Update display name to better format
    db.tag_concepts_v2.update_one(
        {"_id": primary['_id']},
        {"$set": {"display_name": consolidation['display']}}
    )
    
    # Find and merge duplicates
    for dup_name in consolidation['duplicates']:
        dup = db.tag_concepts_v2.find_one({
            "$or": [
                {"display_name": dup_name},
                {"slug": dup_name.lower().replace(" ", "_").replace(".", "_").replace("-", "_")}
            ],
            "_id": {"$ne": primary['_id']}
        })
        
        if dup:
            print(f"  Merging duplicate: {dup['display_name']}")
            
            # Transfer usage count
            dup_usage = dup.get('usage_count', 0)
            if dup_usage > 0:
                db.tag_concepts_v2.update_one(
                    {"_id": primary['_id']},
                    {"$inc": {"usage_count": dup_usage}}
                )
            
            # Transfer tag_instances
            result = db.tag_instances.update_many(
                {"concept_id": str(dup['_id'])},
                {"$set": {"concept_id": str(primary['_id'])}}
            )
            if result.modified_count > 0:
                print(f"    Transferred {result.modified_count} instances")
            
            # Delete duplicate
            db.tag_concepts_v2.delete_one({"_id": dup['_id']})
            print(f"    Deleted duplicate concept")
    
    # Add aliases
    for alias_text in consolidation['aliases']:
        # Check if alias already exists
        existing = db.tag_aliases_v2.find_one({
            "concept_id": primary['_id'],
            "alias_text": alias_text
        })
        
        if not existing:
            db.tag_aliases_v2.insert_one({
                "concept_id": primary['_id'],
                "alias_text": alias_text,
                "alias_type": "synonym",
                "confidence": 1.0,
                "created_at": datetime.utcnow()
            })
            print(f"  Added alias: {alias_text}")

# Recalculate usage counts for all Grok concepts
print("\n" + "-" * 40)
print("RECALCULATING USAGE COUNTS...")
print("-" * 40)

remaining_grok = list(db.tag_concepts_v2.find({
    "$or": [
        {"display_name": {"$regex": "^Grok", "$options": "i"}},
        {"slug": {"$regex": "^grok", "$options": "i"}}
    ]
}))

for concept in remaining_grok:
    concept_id_str = str(concept['_id'])
    actual_count = db.tag_instances.count_documents({"concept_id": concept_id_str})
    
    db.tag_concepts_v2.update_one(
        {"_id": concept['_id']},
        {"$set": {"usage_count": actual_count}}
    )
    print(f"  {concept['display_name']}: {actual_count} instances")

print("\n" + "=" * 60)
print("CONSOLIDATION COMPLETE")
print("=" * 60)