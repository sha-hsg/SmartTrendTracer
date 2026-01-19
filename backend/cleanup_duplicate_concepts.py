#!/usr/bin/env python3
"""
Clean up duplicate and redundant concepts in the hierarchy
"""

from pymongo import MongoClient
from bson import ObjectId

def cleanup_duplicate_concepts():
    """
    Remove or merge duplicate concepts
    """
    client = MongoClient('mongodb://localhost:27017/')
    db = client.smarttrendtracer
    
    print("=" * 70)
    print("CLEANING UP DUPLICATE/REDUNDANT CONCEPTS")
    print("=" * 70)
    
    # Concepts to remove (duplicates of root categories)
    concepts_to_remove = [
        'c_applications',  # Duplicate of Applications and Tasks
        'c_data',  # Duplicate of Data and Datasets
        'c_et_research-entities',  # Duplicate/redundant category
        'c_evaluation'  # Check if this is duplicate of Evaluation and Benchmarks
    ]
    
    # Hardware should be under Ecosystem and Industry
    hardware_concept = db.tag_concepts_v2.find_one({'slug': 'hardware'})
    if hardware_concept:
        ecosystem_cat = db.tag_concepts_v2.find_one({'slug': 'ecosystem_and_industry'})
        if ecosystem_cat:
            db.tag_concepts_v2.update_one(
                {'_id': hardware_concept['_id']},
                {'$set': {'parents': [ecosystem_cat['_id']]}}
            )
            print(f"✅ Moved Hardware under Ecosystem and Industry")
    
    # Remove duplicate concepts
    for concept_id in concepts_to_remove:
        concept = db.tag_concepts_v2.find_one({'_id': concept_id})
        if concept:
            # First, reassign any children to appropriate categories
            children = concept.get('children', [])
            if children:
                print(f"\n⚠️ {concept['display_name']} has {len(children)} children to reassign")
                # Move children to AI/ML Fundamentals temporarily
                fundamentals = db.tag_concepts_v2.find_one({'slug': 'fundamentals'})
                if fundamentals:
                    for child_id in children:
                        db.tag_concepts_v2.update_one(
                            {'id': child_id},
                            {'$set': {'parents': [fundamentals['_id']]}}
                        )
            
            # Remove the duplicate concept
            db.tag_concepts_v2.delete_one({'_id': concept_id})
            print(f"✅ Removed duplicate concept: {concept['display_name']}")
    
    # Move standards (SPARQL, OWL, etc.) to Tools and Libraries
    standards = ['SPARQL', 'OWL', 'SQL', 'GGUF', 'schema.org']
    tools_cat = db.tag_concepts_v2.find_one({'slug': 'tools_and_libraries'})
    if tools_cat:
        for standard_name in standards:
            standard = db.tag_concepts_v2.find_one({'display_name': standard_name})
            if standard:
                db.tag_concepts_v2.update_one(
                    {'_id': standard['_id']},
                    {'$set': {'parents': [tools_cat['_id']]}}
                )
        print(f"✅ Moved {len(standards)} standards to Tools and Libraries")
    
    # Move experimental setups to Techniques and Methods
    experimental_setups = db.tag_concepts_v2.find({'entity_type': 'experimental-setup'})
    techniques_cat = db.tag_concepts_v2.find_one({'slug': 'techniques_and_methods'})
    if techniques_cat:
        count = 0
        for exp in experimental_setups:
            db.tag_concepts_v2.update_one(
                {'_id': exp['_id']},
                {'$set': {'parents': [techniques_cat['_id']]}}
            )
            count += 1
        if count > 0:
            print(f"✅ Moved {count} experimental setups to Techniques and Methods")
    
    # Now rebuild children arrays
    print("\n🔧 Rebuilding children arrays...")
    
    # Clear all children arrays
    db.tag_concepts_v2.update_many({}, {'$set': {'children': []}})
    
    # Build parent-to-children mapping
    concepts_with_parents = db.tag_concepts_v2.find({'parents': {'$ne': []}})
    parent_children = {}
    
    for concept in concepts_with_parents:
        concept_id = concept.get('id') or str(concept['_id'])
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
    
    print("\n✅ Cleanup complete!")
    
    # Show updated statistics
    print("\n📊 Updated category sizes:")
    categories = [
        'fundamentals',
        'models_and_architectures',
        'techniques_and_methods',
        'data_and_datasets',
        'evaluation_and_benchmarks',
        'applications_and_tasks',
        'ecosystem_and_industry',
        'tools_and_libraries',
        'responsible_ai',
        'named_entities'
    ]
    
    for cat_slug in categories:
        cat = db.tag_concepts_v2.find_one({'slug': cat_slug})
        if cat:
            children_count = len(cat.get('children', []))
            print(f"  {cat['display_name']}: {children_count} children")

if __name__ == "__main__":
    cleanup_duplicate_concepts()