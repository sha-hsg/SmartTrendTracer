#!/usr/bin/env python3
"""
Check Named Entities hierarchy and usage statistics
"""

from pymongo import MongoClient
from bson import ObjectId

client = MongoClient('mongodb://localhost:27017/')
db = client.smarttrendtracer

print("=" * 60)
print("CHECKING NAMED ENTITIES AND USAGE STATISTICS")
print("=" * 60)

# Check Named Entities and its children
print("\n1. NAMED ENTITIES HIERARCHY...")
print("-" * 40)

named_entities = db.tag_concepts_v2.find_one({"display_name": "Named Entities"})
if named_entities:
    print(f"Named Entities ID: {named_entities['_id']}")
    print(f"Position: {'Root' if not named_entities.get('parents') else 'Child'}")
    
    # Get children
    children = list(db.tag_concepts_v2.find({"parents": named_entities['_id']}))
    print(f"\nChildren ({len(children)}):")
    for child in sorted(children, key=lambda x: x['display_name']):
        print(f"  - {child['display_name']} (type: {child.get('entity_type')})")
        
        # Get grandchildren count
        grandchildren = list(db.tag_concepts_v2.find({"parents": child['_id']}))
        if grandchildren:
            print(f"    Has {len(grandchildren)} items")

# Check specific concepts with usage
print("\n2. CHECKING USAGE STATISTICS...")
print("-" * 40)

test_concepts = ["Grok-2.5", "Grok-25", "Grok 2.5", "Christopher Manning", "GPT", "OpenAI"]

for concept_name in test_concepts:
    # Try different variations
    concept = db.tag_concepts_v2.find_one({
        "$or": [
            {"display_name": concept_name},
            {"display_name": {"$regex": f"^{concept_name}$", "$options": "i"}},
            {"slug": concept_name.lower().replace(" ", "_").replace(".", "_")}
        ]
    })
    
    if concept:
        print(f"\n'{concept['display_name']}':")
        print(f"  ID: {concept['_id']}")
        print(f"  Slug: {concept.get('slug')}")
        print(f"  Usage count field: {concept.get('usage_count', 0)}")
        
        # Check actual usage in tag_instances
        concept_id_str = str(concept['_id'])
        
        # Count by content type
        tweet_count = db.tag_instances.count_documents({
            "concept_id": concept_id_str,
            "content_type": "tweet"
        })
        paper_count = db.tag_instances.count_documents({
            "concept_id": concept_id_str,
            "content_type": "paper"
        })
        article_count = db.tag_instances.count_documents({
            "concept_id": concept_id_str,
            "content_type": "article"
        })
        
        total_actual = tweet_count + paper_count + article_count
        
        print(f"  Actual usage:")
        print(f"    Tweets: {tweet_count}")
        print(f"    Papers: {paper_count}")
        print(f"    Articles: {article_count}")
        print(f"    Total: {total_actual}")
        
        if total_actual != concept.get('usage_count', 0):
            print(f"  ⚠️ MISMATCH: Field says {concept.get('usage_count', 0)}, actual is {total_actual}")
        
        # Show sample instances
        if total_actual > 0:
            sample = db.tag_instances.find_one({"concept_id": concept_id_str})
            if sample:
                print(f"  Sample instance: {sample.get('content_type')} - {sample.get('content_id')}")
    else:
        print(f"\n'{concept_name}': NOT FOUND")

# Check if there are orphan instances
print("\n3. CHECKING FOR ORPHAN INSTANCES...")
print("-" * 40)

orphan_count = db.tag_instances.count_documents({"concept_id": None})
print(f"Orphan instances (no concept_id): {orphan_count}")

# Sample some orphans
if orphan_count > 0:
    orphans = list(db.tag_instances.find({"concept_id": None}).limit(5))
    print("\nSample orphans:")
    for orphan in orphans:
        print(f"  - Tag: '{orphan.get('tag_text')}' on {orphan.get('content_type')}")

print("\n" + "=" * 60)
print("ANALYSIS COMPLETE")
print("=" * 60)