#!/usr/bin/env python3
"""
Migrate all tag instances from old concepts to new GPT-5 concepts
"""

from pymongo import MongoClient
from bson import ObjectId
import json

def migrate_tags_to_gpt5_concepts():
    """
    Remap all tag_instances from old concept IDs to new GPT-5 concept IDs
    based on slug matching and aliases
    """
    
    client = MongoClient('mongodb://localhost:27017/')
    db = client.smarttrendtracer
    
    print("Starting tag migration to GPT-5 concepts...")
    
    # Build mapping from old concepts to new concepts
    old_to_new_map = {}
    
    # Get all concepts
    all_concepts = list(db.tag_concepts_v2.find())
    
    # Separate old and new concepts
    # New concepts have the GPT-5 structure (created recently)
    # Old concepts are the original ones
    
    # Build a slug-to-concept map for new concepts
    new_concept_by_slug = {}
    new_concept_by_display = {}
    
    # GPT-5 root slugs to identify new concepts
    gpt5_root_slugs = [
        'fundamentals', 'models_and_architectures', 'techniques_and_methods',
        'data', 'applications', 'evaluation', 'ecosystem_and_industry', 'responsible_ai'
    ]
    
    # Find new concepts (those with GPT-5 root as parent or are GPT-5 roots)
    new_concepts = []
    for concept in all_concepts:
        slug = concept.get('slug', '')
        if slug in gpt5_root_slugs:
            new_concepts.append(concept)
            new_concept_by_slug[slug] = concept
            if concept.get('display_name'):
                new_concept_by_display[concept['display_name'].lower()] = concept
    
    # Find all children of GPT-5 roots
    for concept in all_concepts:
        parents = concept.get('parents', [])
        for parent_id in parents:
            parent = db.tag_concepts_v2.find_one({'_id': parent_id})
            if parent and parent.get('slug') in gpt5_root_slugs:
                new_concepts.append(concept)
                new_concept_by_slug[concept.get('slug', '')] = concept
                if concept.get('display_name'):
                    new_concept_by_display[concept['display_name'].lower()] = concept
                break
    
    print(f"Found {len(new_concepts)} new GPT-5 concepts")
    
    # Build alias map for new concepts
    alias_to_concept = {}
    for alias in db.tag_aliases_v2.find():
        alias_text = alias.get('alias_text', '').lower()
        concept_id = alias.get('concept_id')
        if concept_id:
            # Check if this alias points to a new concept
            for new_concept in new_concepts:
                if new_concept['_id'] == concept_id:
                    alias_to_concept[alias_text] = new_concept
                    break
    
    print(f"Found {len(alias_to_concept)} aliases for new concepts")
    
    # Now map old concepts to new concepts
    unmapped_concepts = []
    
    for concept in all_concepts:
        # Skip if it's already a new concept
        if concept in new_concepts:
            continue
        
        old_id = concept['_id']
        slug = concept.get('slug', '').lower()
        display_name = concept.get('display_name', '').lower()
        
        # Try to find matching new concept
        new_concept = None
        
        # 1. Try exact slug match
        if slug in new_concept_by_slug:
            new_concept = new_concept_by_slug[slug]
        
        # 2. Try display name match
        elif display_name in new_concept_by_display:
            new_concept = new_concept_by_display[display_name]
        
        # 3. Try alias match
        elif slug in alias_to_concept:
            new_concept = alias_to_concept[slug]
        elif display_name in alias_to_concept:
            new_concept = alias_to_concept[display_name]
        
        # 4. Try normalized matching (remove hyphens, underscores)
        if not new_concept:
            normalized_slug = slug.replace('-', '').replace('_', '').replace(' ', '')
            for new_slug, new_c in new_concept_by_slug.items():
                if new_slug.replace('-', '').replace('_', '').replace(' ', '') == normalized_slug:
                    new_concept = new_c
                    break
        
        if new_concept:
            old_to_new_map[str(old_id)] = new_concept['_id']
            print(f"  Mapped: {concept.get('display_name', slug)} -> {new_concept.get('display_name')}")
        else:
            unmapped_concepts.append(concept)
    
    print(f"\nCreated {len(old_to_new_map)} mappings")
    print(f"Unmapped concepts: {len(unmapped_concepts)}")
    
    if unmapped_concepts[:10]:
        print("\nSample unmapped concepts:")
        for concept in unmapped_concepts[:10]:
            print(f"  - {concept.get('display_name', concept.get('slug'))}")
    
    # Now update all tag_instances
    print("\nUpdating tag instances...")
    
    total_updated = 0
    total_skipped = 0
    
    for old_id_str, new_id in old_to_new_map.items():
        # Update all tag instances with this old concept ID
        result = db.tag_instances.update_many(
            {'concept_id': old_id_str},
            {'$set': {'concept_id': str(new_id)}}
        )
        
        if result.modified_count > 0:
            total_updated += result.modified_count
            print(f"  Updated {result.modified_count} instances")
    
    # Check for remaining unmapped instances
    unmapped_instances = db.tag_instances.count_documents({
        'concept_id': {'$nin': [str(c['_id']) for c in new_concepts]}
    })
    
    print("\n" + "="*50)
    print("MIGRATION COMPLETE!")
    print(f"  Total instances updated: {total_updated}")
    print(f"  Unmapped instances remaining: {unmapped_instances}")
    
    # Final statistics
    print("\nFinal Statistics:")
    print(f"  Total concepts: {db.tag_concepts_v2.count_documents({})}")
    print(f"  Total aliases: {db.tag_aliases_v2.count_documents({})}")
    print(f"  Total tag instances: {db.tag_instances.count_documents({})}")
    
    # Count instances by root category
    print("\nInstances by root category:")
    for root_slug in gpt5_root_slugs:
        root = db.tag_concepts_v2.find_one({'slug': root_slug})
        if root:
            # Count all instances under this root
            count = db.tag_instances.count_documents({'concept_id': str(root['_id'])})
            
            # Also count children
            children = db.tag_concepts_v2.find({'parents': root['_id']})
            for child in children:
                count += db.tag_instances.count_documents({'concept_id': str(child['_id'])})
            
            print(f"  {root.get('display_name')}: {count} instances")
    
    return {
        'updated': total_updated,
        'unmapped': unmapped_instances,
        'mapping_count': len(old_to_new_map)
    }

if __name__ == "__main__":
    result = migrate_tags_to_gpt5_concepts()