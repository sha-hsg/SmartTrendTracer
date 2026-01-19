#!/usr/bin/env python3
"""
Fix broken alias references by mapping old string IDs to new ObjectIds.
This script:
1. Creates a mapping from old IDs (c_0001, etc.) to new ObjectIds
2. Updates all aliases to use the correct ObjectIds
3. Removes aliases for concepts that no longer exist
"""

import json
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from typing import Dict, List, Optional

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['smarttrendtracer']
concepts_collection = db['tag_concepts_v2']
aliases_collection = db['tag_aliases_v2']

def build_id_mapping() -> Dict[str, ObjectId]:
    """Build mapping from old string IDs to new ObjectIds."""
    id_mapping = {}
    
    # First, try to map by the 'id' field if it exists
    concepts_with_old_id = concepts_collection.find({'id': {'$exists': True}})
    for concept in concepts_with_old_id:
        old_id = concept.get('id')
        if old_id:
            id_mapping[old_id] = concept['_id']
    
    # Also map by slug for common patterns
    all_concepts = concepts_collection.find({})
    for concept in all_concepts:
        slug = concept.get('slug', '')
        # Map common ID patterns
        if slug:
            # Try c_ prefix pattern
            possible_ids = [
                f"c_{slug}",
                f"c_{slug.replace('-', '_')}",
                slug,
                slug.replace('-', '_')
            ]
            for pid in possible_ids:
                if pid not in id_mapping:
                    id_mapping[pid] = concept['_id']
    
    return id_mapping

def fix_aliases():
    """Fix all alias references to use correct ObjectIds."""
    print("Building ID mapping...")
    id_mapping = build_id_mapping()
    print(f"Found {len(id_mapping)} ID mappings")
    
    # Get all aliases
    all_aliases = list(aliases_collection.find({}))
    print(f"\nProcessing {len(all_aliases)} aliases...")
    
    fixed_count = 0
    removed_count = 0
    already_correct = 0
    
    for alias in all_aliases:
        concept_id = alias.get('concept_id')
        
        # Check if it's already an ObjectId
        if isinstance(concept_id, ObjectId):
            # Verify it exists
            if concepts_collection.find_one({'_id': concept_id}):
                already_correct += 1
                continue
            else:
                # ObjectId but concept doesn't exist
                aliases_collection.delete_one({'_id': alias['_id']})
                removed_count += 1
                print(f"  ✗ Removed orphaned alias: {alias.get('alias_text', 'unknown')}")
                continue
        
        # It's a string ID, need to fix it
        if concept_id in id_mapping:
            new_id = id_mapping[concept_id]
            aliases_collection.update_one(
                {'_id': alias['_id']},
                {'$set': {'concept_id': new_id}}
            )
            fixed_count += 1
            print(f"  ✓ Fixed: {alias.get('alias_text', 'unknown')} -> {new_id}")
        else:
            # Try to find concept by matching alias text to concept slug/name
            alias_text = alias.get('alias_text', '').lower()
            found_concept = None
            
            # Try exact slug match
            found_concept = concepts_collection.find_one({'slug': alias_text})
            
            # Try slug with underscores instead of hyphens
            if not found_concept:
                found_concept = concepts_collection.find_one({'slug': alias_text.replace('_', '-')})
            
            # Try display name match (case insensitive)
            if not found_concept:
                found_concept = concepts_collection.find_one({
                    'display_name': {'$regex': f'^{alias_text}$', '$options': 'i'}
                })
            
            if found_concept:
                aliases_collection.update_one(
                    {'_id': alias['_id']},
                    {'$set': {'concept_id': found_concept['_id']}}
                )
                fixed_count += 1
                print(f"  ✓ Matched by name: {alias.get('alias_text', 'unknown')} -> {found_concept['display_name']}")
            else:
                # Can't find matching concept, remove the alias
                aliases_collection.delete_one({'_id': alias['_id']})
                removed_count += 1
                print(f"  ✗ Removed unmatched alias: {alias.get('alias_text', 'unknown')}")
    
    print(f"\n=== Alias Fix Summary ===")
    print(f"Already correct: {already_correct}")
    print(f"Fixed: {fixed_count}")
    print(f"Removed: {removed_count}")
    print(f"Total processed: {len(all_aliases)}")
    
    return fixed_count, removed_count

def verify_aliases():
    """Verify all aliases now point to valid concepts."""
    print("\n=== Verifying Aliases ===")
    
    total_aliases = aliases_collection.count_documents({})
    broken_aliases = 0
    
    for alias in aliases_collection.find():
        concept_id = alias.get('concept_id')
        if not concepts_collection.find_one({'_id': concept_id}):
            broken_aliases += 1
            print(f"  ❌ Still broken: {alias.get('alias_text', 'unknown')}")
    
    print(f"\nTotal aliases: {total_aliases}")
    print(f"Broken aliases: {broken_aliases}")
    print(f"Success rate: {((total_aliases - broken_aliases) / total_aliases * 100):.1f}%")
    
    return broken_aliases == 0

def main():
    print("🔧 FIXING ALIAS REFERENCES")
    print("="*50)
    
    # Fix aliases
    fixed, removed = fix_aliases()
    
    # Verify the fix
    success = verify_aliases()
    
    if success:
        print("\n✅ All alias references fixed successfully!")
    else:
        print("\n⚠️ Some aliases still have issues. May need manual review.")
    
    print("\nYou can now proceed with fixing usage counts.")

if __name__ == "__main__":
    main()