#!/usr/bin/env python3
"""
Fix usage counts to match actual annotations
"""

from pymongo import MongoClient
from bson import ObjectId

client = MongoClient('mongodb://localhost:27017/')
db = client.smarttrendtracer

print("Fixing usage counts to match actual annotations...")

# Get actual usage counts from tag_instances
actual_usage = {}
for instance in db.tag_instances.find():
    concept_id = instance.get('concept_id')
    if concept_id:
        if concept_id not in actual_usage:
            actual_usage[concept_id] = {'tweet': 0, 'paper': 0, 'article': 0}
        
        content_type = instance.get('content_type', 'unknown')
        if content_type in actual_usage[concept_id]:
            actual_usage[concept_id][content_type] += 1

# Update all concepts with correct usage counts
updated = 0
zeroed = 0

for concept in db.tag_concepts_v2.find():
    concept_id = str(concept['_id'])
    
    if concept_id in actual_usage:
        # Has actual usage
        usage = actual_usage[concept_id]
        total = sum(usage.values())
        
        db.tag_concepts_v2.update_one(
            {'_id': concept['_id']},
            {'$set': {
                'usage_count': total,
                'tweet_count': usage['tweet'],
                'paper_count': usage['paper'],
                'article_count': usage['article']
            }}
        )
        updated += 1
    else:
        # No actual usage - set to 0
        if concept.get('usage_count', 0) > 0:
            db.tag_concepts_v2.update_one(
                {'_id': concept['_id']},
                {'$set': {
                    'usage_count': 0,
                    'tweet_count': 0,
                    'paper_count': 0,
                    'article_count': 0
                }}
            )
            zeroed += 1

print(f"✅ Updated {updated} concepts with actual usage counts")
print(f"✅ Zeroed {zeroed} concepts with phantom usage")

# Verify
total_annotations = db.tag_instances.count_documents({})
concepts_with_usage = db.tag_concepts_v2.count_documents({'usage_count': {'$gt': 0}})
total_usage = list(db.tag_concepts_v2.aggregate([
    {'$group': {'_id': None, 'total': {'$sum': '$usage_count'}}}
]))[0]['total']

print(f"\nVerification:")
print(f"  Total annotations: {total_annotations}")
print(f"  Concepts with usage: {concepts_with_usage}")
print(f"  Sum of all usage_counts: {total_usage}")
print(f"  Match: {'✅ YES' if total_annotations == total_usage else '❌ NO'}")
