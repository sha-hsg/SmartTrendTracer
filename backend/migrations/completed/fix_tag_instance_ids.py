#!/usr/bin/env python3
"""
Fix tag_instances to use consistent ObjectId types for concept_id.
This ensures accurate usage counting.
"""

from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from typing import Dict, List

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['smarttrendtracer']
instances_collection = db['tag_instances']
concepts_collection = db['tag_concepts_v2']

def fix_concept_id_types():
    """Convert all string concept_ids to ObjectIds in tag_instances."""
    print("Fixing concept_id types in tag_instances...")
    
    # Count instances with string IDs
    all_instances = list(instances_collection.find({}))
    string_ids = 0
    object_ids = 0
    fixed = 0
    
    for instance in all_instances:
        concept_id = instance.get('concept_id')
        
        if concept_id is None:
            continue
            
        if isinstance(concept_id, str):
            string_ids += 1
            try:
                # Convert string to ObjectId
                obj_id = ObjectId(concept_id)
                
                # Verify this concept exists
                if concepts_collection.find_one({'_id': obj_id}):
                    instances_collection.update_one(
                        {'_id': instance['_id']},
                        {'$set': {'concept_id': obj_id}}
                    )
                    fixed += 1
                else:
                    print(f"  Warning: Concept {concept_id} not found")
            except:
                print(f"  Error: Invalid ObjectId string: {concept_id}")
        elif isinstance(concept_id, ObjectId):
            object_ids += 1
    
    print(f"\nID Type Summary:")
    print(f"  String IDs: {string_ids}")
    print(f"  ObjectIds: {object_ids}")
    print(f"  Fixed: {fixed}")
    
    return fixed

def recalculate_all_usage_counts():
    """Recalculate usage counts for all concepts."""
    print("\nRecalculating usage counts...")
    
    # Reset all counts to 0
    concepts_collection.update_many({}, {'$set': {'usage_count': 0}})
    
    # Count instances for each concept
    pipeline = [
        {'$match': {'concept_id': {'$ne': None}}},
        {'$group': {
            '_id': '$concept_id',
            'count': {'$sum': 1}
        }}
    ]
    
    usage_counts = list(instances_collection.aggregate(pipeline))
    
    # Update each concept with its count
    updated = 0
    for item in usage_counts:
        concept_id = item['_id']
        count = item['count']
        
        result = concepts_collection.update_one(
            {'_id': concept_id},
            {'$set': {
                'usage_count': count,
                'usage_count_updated': datetime.utcnow()
            }}
        )
        if result.modified_count > 0:
            updated += 1
    
    print(f"  Updated {updated} concepts with usage counts")
    
    # Set remaining concepts to 0 (already done above)
    zero_count = concepts_collection.count_documents({'usage_count': 0})
    print(f"  {zero_count} concepts have zero usage")
    
    return updated

def verify_counts():
    """Verify that usage counts are now accurate."""
    print("\n=== Verifying Usage Counts ===")
    
    # Check a sample of concepts
    mismatches = 0
    samples_checked = 0
    
    for concept in concepts_collection.find().limit(50):
        actual_count = instances_collection.count_documents({'concept_id': concept['_id']})
        stored_count = concept.get('usage_count', 0)
        
        samples_checked += 1
        if actual_count != stored_count:
            mismatches += 1
            print(f"  ✗ {concept['display_name']}: stored={stored_count}, actual={actual_count}")
    
    if mismatches == 0:
        print(f"  ✓ All {samples_checked} sampled concepts have correct counts!")
    else:
        print(f"  ✗ Found {mismatches}/{samples_checked} mismatches")
    
    # Show top used concepts
    print("\nTop 10 Most Used Concepts:")
    top_concepts = concepts_collection.find({'usage_count': {'$gt': 0}}).sort('usage_count', -1).limit(10)
    for concept in top_concepts:
        print(f"  {concept['display_name']}: {concept['usage_count']} uses")
    
    # Overall statistics
    total_instances = instances_collection.count_documents({})
    total_with_concept = instances_collection.count_documents({'concept_id': {'$ne': None}})
    total_usage = sum([c.get('usage_count', 0) for c in concepts_collection.find()])
    
    print(f"\nOverall Statistics:")
    print(f"  Total tag instances: {total_instances}")
    print(f"  Instances with concept: {total_with_concept}")
    print(f"  Sum of usage counts: {total_usage}")
    print(f"  Match: {'✓' if total_with_concept == total_usage else '✗'}")
    
    return mismatches == 0 and total_with_concept == total_usage

def main():
    print("🔧 FIXING USAGE COUNT SYNCHRONIZATION")
    print("="*50)
    
    # Step 1: Fix concept_id types
    fixed = fix_concept_id_types()
    
    # Step 2: Recalculate all usage counts
    updated = recalculate_all_usage_counts()
    
    # Step 3: Verify accuracy
    success = verify_counts()
    
    if success:
        print("\n✅ Usage counts are now perfectly synchronized!")
    else:
        print("\n⚠️ Some discrepancies remain. May need manual investigation.")
    
    print("\nNext steps: Test the LLM reorganization system.")

if __name__ == "__main__":
    main()