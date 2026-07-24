#!/usr/bin/env python3
"""
Fix entity hierarchy - move entities under their proper subcategories
"""

from pymongo import MongoClient
from bson import ObjectId

def fix_entity_hierarchy():
    """
    Move person, organisation, and location entities under their proper subcategories
    """
    client = MongoClient('mongodb://localhost:27017/')
    db = client.smarttrendtracer
    
    print("Fixing entity hierarchy...")
    
    # Get the subcategory IDs
    person_cat = db.tag_concepts_v2.find_one({'slug': 'person', 'entity_type': 'person'})
    org_cat = db.tag_concepts_v2.find_one({'slug': 'organisation', 'entity_type': 'organisation'})
    location_cat = db.tag_concepts_v2.find_one({'slug': 'location', 'entity_type': 'location'})
    
    if not person_cat or not org_cat or not location_cat:
        print("Error: Could not find all subcategories")
        return
    
    person_id = person_cat['_id']
    org_id = org_cat['_id']
    location_id = location_cat['_id']
    
    print(f"Found subcategories:")
    print(f"  Person: {person_id}")
    print(f"  Organisation: {org_id}")
    print(f"  Location: {location_id}")
    
    # Update all person entities to have Person as parent
    person_result = db.tag_concepts_v2.update_many(
        {
            'entity_type': 'person',
            'slug': {'$ne': 'person'}  # Don't update the Person category itself
        },
        {'$set': {'parents': [person_id]}}
    )
    print(f"\n✅ Updated {person_result.modified_count} person entities")
    
    # Update all organisation entities to have Organisation as parent
    org_result = db.tag_concepts_v2.update_many(
        {
            'entity_type': 'organisation',
            'slug': {'$ne': 'organisation'}  # Don't update the Organisation category itself
        },
        {'$set': {'parents': [org_id]}}
    )
    print(f"✅ Updated {org_result.modified_count} organisation entities")
    
    # Update all location entities to have Location as parent
    location_result = db.tag_concepts_v2.update_many(
        {
            'entity_type': 'location',
            'slug': {'$ne': 'location'}  # Don't update the Location category itself
        },
        {'$set': {'parents': [location_id]}}
    )
    print(f"✅ Updated {location_result.modified_count} location entities")
    
    # Now rebuild the children arrays
    print("\nRebuilding children arrays...")
    
    # Clear all children arrays first
    db.tag_concepts_v2.update_many({}, {'$set': {'children': []}})
    
    # Get all concepts with parents
    concepts_with_parents = db.tag_concepts_v2.find({'parents': {'$ne': []}})
    
    parent_children = {}
    
    # Build parent-to-children mapping
    for concept in concepts_with_parents:
        concept_id = concept['_id']
        for parent_id in concept.get('parents', []):
            if parent_id not in parent_children:
                parent_children[parent_id] = []
            parent_children[parent_id].append(concept_id)
    
    # Update each parent with its children
    for parent_id, children_ids in parent_children.items():
        db.tag_concepts_v2.update_one(
            {'_id': parent_id},
            {'$set': {'children': children_ids}}
        )
    
    # Show results
    print("\n📊 Updated hierarchy:")
    
    # Check Person subcategory
    person_cat = db.tag_concepts_v2.find_one({'_id': person_id})
    print(f"\nPerson category now has {len(person_cat.get('children', []))} children")
    if person_cat.get('children'):
        sample_children = list(db.tag_concepts_v2.find(
            {'_id': {'$in': person_cat['children'][:5]}},
            {'display_name': 1}
        ))
        for child in sample_children:
            print(f"  - {child['display_name']}")
    
    # Check Organisation subcategory
    org_cat = db.tag_concepts_v2.find_one({'_id': org_id})
    print(f"\nOrganisation category now has {len(org_cat.get('children', []))} children")
    if org_cat.get('children'):
        sample_children = list(db.tag_concepts_v2.find(
            {'_id': {'$in': org_cat['children'][:5]}},
            {'display_name': 1}
        ))
        for child in sample_children:
            print(f"  - {child['display_name']}")
    
    # Check Location subcategory
    location_cat = db.tag_concepts_v2.find_one({'_id': location_id})
    print(f"\nLocation category now has {len(location_cat.get('children', []))} children")
    if location_cat.get('children'):
        sample_children = list(db.tag_concepts_v2.find(
            {'_id': {'$in': location_cat['children'][:5]}},
            {'display_name': 1}
        ))
        for child in sample_children:
            print(f"  - {child['display_name']}")
    
    print("\n✅ Entity hierarchy fixed!")

if __name__ == "__main__":
    fix_entity_hierarchy()