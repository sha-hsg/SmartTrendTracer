#!/usr/bin/env python3
"""
Fixed script to correctly update usage counts and content type counts.
This version properly handles ObjectId keys instead of converting to strings.
"""

from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

client = MongoClient('mongodb://localhost:27017/')
db = client.smarttrendtracer

print("🔧 FIXING CONCEPT COUNTS (CORRECTED VERSION)")
print("=" * 50)

# Get actual usage counts from tag_instances using ObjectId as keys
print("Counting actual usage from tag_instances...")
actual_usage = {}

for instance in db.tag_instances.find():
    concept_id = instance.get('concept_id')
    if concept_id:
        # Ensure concept_id is ObjectId
        if isinstance(concept_id, str):
            try:
                concept_id = ObjectId(concept_id)
            except:
                continue
        
        # Use ObjectId as key, not string
        if concept_id not in actual_usage:
            actual_usage[concept_id] = {'tweet': 0, 'paper': 0, 'article': 0, 'total': 0}
        
        content_type = instance.get('content_type', 'unknown')
        if content_type in actual_usage[concept_id]:
            actual_usage[concept_id][content_type] += 1
            actual_usage[concept_id]['total'] += 1

print(f"Found usage data for {len(actual_usage)} concepts")

# Update all concepts with correct usage counts
updated = 0
zeroed = 0

print("\nUpdating concept counts...")

for concept in db.tag_concepts_v2.find():
    concept_id = concept['_id']  # Keep as ObjectId, don't convert to string!
    
    if concept_id in actual_usage:
        # Has actual usage
        usage = actual_usage[concept_id]
        
        # Show what we're updating
        old_counts = {
            'usage': concept.get('usage_count', 0),
            'tweet': concept.get('tweet_count', 0),
            'paper': concept.get('paper_count', 0),
            'article': concept.get('article_count', 0)
        }
        
        new_counts = {
            'usage': usage['total'],
            'tweet': usage['tweet'],
            'paper': usage['paper'],
            'article': usage['article']
        }
        
        # Only update if counts changed
        if old_counts != new_counts:
            db.tag_concepts_v2.update_one(
                {'_id': concept_id},
                {'$set': {
                    'usage_count': usage['total'],
                    'tweet_count': usage['tweet'],
                    'paper_count': usage['paper'],
                    'article_count': usage['article'],
                    'usage_count_updated': datetime.utcnow()
                }}
            )
            
            # Show what changed
            display_name = concept.get('display_name', concept.get('name', 'Unknown'))
            print(f"  ✓ {display_name}: usage({old_counts['usage']}→{new_counts['usage']}) paper({old_counts['paper']}→{new_counts['paper']}) tweet({old_counts['tweet']}→{new_counts['tweet']}) article({old_counts['article']}→{new_counts['article']})")
            updated += 1
    else:
        # No actual usage - set to 0 only if currently non-zero
        old_total = concept.get('usage_count', 0) + concept.get('tweet_count', 0) + concept.get('paper_count', 0) + concept.get('article_count', 0)
        if old_total > 0:
            db.tag_concepts_v2.update_one(
                {'_id': concept_id},
                {'$set': {
                    'usage_count': 0,
                    'tweet_count': 0,
                    'paper_count': 0,
                    'article_count': 0,
                    'usage_count_updated': datetime.utcnow()
                }}
            )
            display_name = concept.get('display_name', concept.get('name', 'Unknown'))
            print(f"  ✓ {display_name}: Zeroed phantom counts")
            zeroed += 1

print(f"\n=== SUMMARY ===")
print(f"Updated: {updated} concepts")
print(f"Zeroed: {zeroed} concepts")

# Verification
print(f"\n=== VERIFICATION ===")
total_annotations = db.tag_instances.count_documents({})
concepts_with_usage = db.tag_concepts_v2.count_documents({'usage_count': {'$gt': 0}})
sum_usage_counts = list(db.tag_concepts_v2.aggregate([
    {'$group': {'_id': None, 'total': {'$sum': '$usage_count'}}}
]))[0]['total']

print(f"Total annotations: {total_annotations}")
print(f"Concepts with usage: {concepts_with_usage}")
print(f"Sum of all usage_counts: {sum_usage_counts}")
print(f"Match: {'✅ YES' if total_annotations == sum_usage_counts else '❌ NO'}")

# Check specific case - Ontologies
ontologies_concept = db.tag_concepts_v2.find_one({'display_name': 'Ontologies'})
if ontologies_concept:
    print(f"\n=== ONTOLOGIES CONCEPT CHECK ===")
    print(f"Usage count: {ontologies_concept.get('usage_count', 0)}")
    print(f"Paper count: {ontologies_concept.get('paper_count', 0)}")
    print(f"Tweet count: {ontologies_concept.get('tweet_count', 0)}")
    print(f"Article count: {ontologies_concept.get('article_count', 0)}")
    
    # Check actual instances
    actual_ontologies_instances = db.tag_instances.count_documents({'concept_id': ontologies_concept['_id']})
    print(f"Actual instances: {actual_ontologies_instances}")
    
    instances_by_type = list(db.tag_instances.aggregate([
        {'$match': {'concept_id': ontologies_concept['_id']}},
        {'$group': {'_id': '$content_type', 'count': {'$sum': 1}}}
    ]))
    print(f"Instances by type: {instances_by_type}")

print(f"\n✅ Usage counts have been fixed!")