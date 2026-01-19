#!/usr/bin/env python3
"""
Fix children arrays that contain ObjectIds instead of string IDs
"""

from pymongo import MongoClient
from bson import ObjectId

def fix_objectid_children():
    """
    Convert ObjectId children to string IDs for consistency
    """
    client = MongoClient('mongodb://localhost:27017/')
    db = client.smarttrendtracer
    
    print("Fixing ObjectId children arrays...")
    
    # Find all concepts
    all_concepts = list(db.tag_concepts_v2.find())
    
    fixed_count = 0
    
    for concept in all_concepts:
        children = concept.get('children', [])
        if not children:
            continue
        
        # Check if any children are ObjectIds
        has_objectids = any(isinstance(child, ObjectId) for child in children)
        
        if has_objectids:
            # Convert ObjectIds to their corresponding concept IDs
            new_children = []
            for child in children:
                if isinstance(child, ObjectId):
                    # Look up the concept with this ObjectId
                    child_concept = db.tag_concepts_v2.find_one({'_id': child})
                    if child_concept:
                        # Use the concept's id field if it exists, otherwise use _id as string
                        if 'id' in child_concept:
                            new_children.append(child_concept['id'])
                        else:
                            new_children.append(str(child_concept['_id']))
                else:
                    new_children.append(child)
            
            # Update the concept with string IDs
            db.tag_concepts_v2.update_one(
                {'_id': concept['_id']},
                {'$set': {'children': new_children}}
            )
            
            print(f"Fixed {concept['display_name']}: converted {len(children)} ObjectIds to string IDs")
            fixed_count += 1
    
    print(f"\n✅ Fixed {fixed_count} concepts with ObjectId children")
    
    # Verify specific categories
    print("\n📊 Verifying key categories:")
    
    for slug in ['ecosystem_and_industry', 'data_and_datasets', 'applications_and_tasks']:
        cat = db.tag_concepts_v2.find_one({'slug': slug})
        if cat:
            children = cat.get('children', [])
            print(f"\n{cat['display_name']}:")
            print(f"  Children count: {len(children)}")
            if children:
                # Show first 3 children
                for child_id in children[:3]:
                    if isinstance(child_id, str):
                        child = db.tag_concepts_v2.find_one({'id': child_id})
                        if not child:
                            child = db.tag_concepts_v2.find_one({'_id': child_id})
                        if child:
                            print(f"    - {child.get('display_name', 'Unknown')}")

if __name__ == "__main__":
    fix_objectid_children()