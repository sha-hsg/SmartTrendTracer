#!/usr/bin/env python3
"""
Add organization tracking to concepts in MongoDB.
This helps identify concepts that were auto-created but not yet organized into the hierarchy.
"""

from pymongo import MongoClient
from datetime import datetime

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client.smarttrendtracer

def add_organization_tracking():
    """Add is_organized field to all concepts"""
    
    print("Adding organization tracking to concepts...")
    
    # First, let's analyze current concepts
    all_concepts = list(db.tag_concepts_v2.find())
    
    organized_count = 0
    unorganized_count = 0
    
    for concept in all_concepts:
        # Determine if concept is organized
        # A concept is considered organized if:
        # 1. It has parents (not a root), OR
        # 2. It's a root concept created by GPT-5 reorganizer, OR
        # 3. It has children (meaning someone intentionally placed things under it)
        
        has_parents = len(concept.get('parents', [])) > 0
        has_children = db.tag_concepts_v2.count_documents({'parents': concept['_id']}) > 0
        created_by_system = concept.get('created_by') in ['gpt-5-reorganizer', 'system', 'migration']
        
        # Concept is organized if it has parents, or is a root with children, or was created by the system
        is_organized = has_parents or (has_children and created_by_system)
        
        # Update the concept
        db.tag_concepts_v2.update_one(
            {'_id': concept['_id']},
            {
                '$set': {
                    'is_organized': is_organized,
                    'needs_review': not is_organized,  # Flag for review if not organized
                    'organization_updated_at': datetime.now() if is_organized else None
                }
            }
        )
        
        if is_organized:
            organized_count += 1
        else:
            unorganized_count += 1
            print(f"  Unorganized: {concept.get('display_name')} (ID: {concept['_id']})")
    
    print(f"\nSummary:")
    print(f"  Total concepts: {len(all_concepts)}")
    print(f"  Organized: {organized_count}")
    print(f"  Need organization: {unorganized_count}")
    
    # Create an index for faster queries
    db.tag_concepts_v2.create_index([("is_organized", 1)])
    db.tag_concepts_v2.create_index([("needs_review", 1)])
    print("\nCreated indexes for organization tracking")

def get_unorganized_concepts():
    """Get list of concepts that need organization"""
    
    unorganized = list(db.tag_concepts_v2.find(
        {'is_organized': False},
        {'display_name': 1, 'slug': 1, 'created_at': 1, 'usage_count': 1}
    ).sort('created_at', -1))
    
    print(f"\nConcepts needing organization ({len(unorganized)} total):")
    for concept in unorganized[:20]:  # Show first 20
        # Get usage count
        usage = db.tag_instances.count_documents({'concept_id': concept['_id']})
        print(f"  - {concept['display_name']} (used {usage} times)")
    
    return unorganized

if __name__ == "__main__":
    add_organization_tracking()
    get_unorganized_concepts()
    
    print("\n✅ Organization tracking added to all concepts!")
    print("\nNext steps:")
    print("1. Use the 'needs_review' field to find concepts needing organization")
    print("2. Create an LLM-powered organizer to suggest parent concepts")
    print("3. Update is_organized=true after placing in hierarchy")