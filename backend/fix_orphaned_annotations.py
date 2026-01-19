#!/usr/bin/env python3
"""
Fix orphaned annotations that have incorrect concept_id values.
These were created during SQLite migration with c_xxxx format IDs
that don't match actual MongoDB ObjectIds.
"""

from pymongo import MongoClient
from bson import ObjectId
import logging
from typing import Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_concept_by_slug_or_name(db, search_term: str):
    """
    Try to find a concept by various methods
    """
    # Clean up the search term
    # c_0001 -> likely "ai" or similar
    # c_org_hugging_face -> hugging_face
    # c_model_gpt_5 -> gpt_5
    
    if search_term.startswith('c_'):
        parts = search_term[2:].split('_', 1)
        if len(parts) > 1 and parts[0] in ['org', 'model', 'person', 'event']:
            # It's like c_org_hugging_face -> look for hugging_face
            search_slug = parts[1]
        else:
            # It's like c_0001 or c_nlp
            search_slug = search_term[2:]
    else:
        search_slug = search_term
    
    # Try various searches
    searches = [
        {'slug': search_slug},
        {'slug': search_slug.replace('_', '-')},
        {'slug': search_slug.replace('_', '.')},
        {'original_tag_text': search_slug.replace('_', '-')},
        {'original_tag_text': search_slug},
        {'name': {'$regex': search_slug.replace('_', '.*'), '$options': 'i'}},
        {'display_name': {'$regex': search_slug.replace('_', '.*'), '$options': 'i'}}
    ]
    
    for search in searches:
        concept = db.tag_concepts_v2.find_one(search)
        if concept:
            return concept
    
    return None

def map_known_concepts():
    """
    Manual mapping for common concepts
    """
    return {
        'c_0001': 'AI',  # Most common, likely AI
        'c_nlp': 'NLP',
        'c_cv': 'computer-vision',
        'c_transformer': 'transformer',
        'c_evaluation': 'evaluation',
        'c_open_source': 'open-source',
        'c_product_launch': 'product-launch',
        'c_org_openai': 'OpenAI',
        'c_org_hugging_face': 'Hugging Face',
        'c_model_gpt_5': 'GPT-5',
        'c_model_gpt_4': 'GPT-4',
        'c_person_sam_altman': 'Sam Altman',
        'c_person_ethan_mollick': 'Ethan Mollick',
    }

def fix_orphaned_annotations():
    """
    Fix annotations with wrong concept_ids
    """
    client = MongoClient('mongodb://localhost:27017/')
    db = client.smarttrendtracer
    
    # Get all unique orphaned concept_ids
    orphaned = db.tag_instances.aggregate([
        {'$group': {'_id': '$concept_id', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}
    ])
    
    orphaned_list = list(orphaned)
    total_orphaned = 0
    fixed_count = 0
    unfixable = []
    
    # Known mappings
    known_mappings = map_known_concepts()
    
    for item in orphaned_list:
        concept_id = item['_id']
        count = item['count']
        
        # Skip valid ObjectIds that exist
        if len(concept_id) == 24:
            try:
                concept = db.tag_concepts_v2.find_one({'_id': ObjectId(concept_id)})
                if concept:
                    continue  # This one is fine
            except:
                pass
        
        # Check if concept exists by ID
        concept = db.tag_concepts_v2.find_one({'id': concept_id})
        if concept:
            # Update annotations to use the ObjectId
            # Need to handle duplicates - delete orphaned ones and keep valid ones
            new_concept_id = str(concept['_id'])
            
            # Get all annotations with this concept_id
            annotations = list(db.tag_instances.find({'concept_id': concept_id}))
            
            for ann in annotations:
                # Check if this combination already exists with correct concept_id
                existing = db.tag_instances.find_one({
                    'content_type': ann['content_type'],
                    'content_id': ann['content_id'],
                    'concept_id': new_concept_id
                })
                
                if existing:
                    # Delete the orphaned duplicate
                    db.tag_instances.delete_one({'_id': ann['_id']})
                    logger.info(f"Deleted duplicate annotation for {concept['display_name']}")
                else:
                    # Update to correct concept_id
                    db.tag_instances.update_one(
                        {'_id': ann['_id']},
                        {'$set': {'concept_id': new_concept_id}}
                    )
                    fixed_count += 1
            
            logger.info(f"Fixed {fixed_count} annotations for {concept['display_name']} (was {concept_id})")
            continue
        
        # Try to find by mapping
        search_term = known_mappings.get(concept_id, concept_id)
        concept = find_concept_by_slug_or_name(db, search_term)
        
        if concept:
            new_concept_id = str(concept['_id'])
            annotations = list(db.tag_instances.find({'concept_id': concept_id}))
            mapped_count = 0
            
            for ann in annotations:
                # Check for existing annotation with correct concept_id
                existing = db.tag_instances.find_one({
                    'content_type': ann['content_type'],
                    'content_id': ann['content_id'],
                    'concept_id': new_concept_id
                })
                
                if existing:
                    db.tag_instances.delete_one({'_id': ann['_id']})
                    logger.debug(f"Deleted duplicate for mapping {concept_id} -> {concept['display_name']}")
                else:
                    db.tag_instances.update_one(
                        {'_id': ann['_id']},
                        {'$set': {'concept_id': new_concept_id}}
                    )
                    mapped_count += 1
                    fixed_count += 1
            
            logger.info(f"Mapped {mapped_count} annotations: {concept_id} -> {concept['display_name']}")
        else:
            total_orphaned += count
            unfixable.append((concept_id, count))
            logger.warning(f"Could not find concept for {concept_id} ({count} annotations)")
    
    # Report
    logger.info(f"\n{'='*60}")
    logger.info(f"ANNOTATION FIX COMPLETE")
    logger.info(f"{'='*60}")
    logger.info(f"Fixed: {fixed_count} annotations")
    logger.info(f"Still orphaned: {total_orphaned} annotations")
    
    if unfixable:
        logger.info(f"\nTop unfixable concept IDs:")
        for concept_id, count in unfixable[:10]:
            logger.info(f"  {concept_id}: {count} annotations")
        
        # Try to create concepts for the most used orphans
        logger.info(f"\nCreating concepts for top orphaned annotations...")
        for concept_id, count in unfixable[:5]:
            if count < 10:
                continue  # Skip low-usage ones
            
            # Parse the concept_id to guess what it should be
            display_name = concept_id
            slug = concept_id
            entity_type = 'concept'
            
            if concept_id.startswith('c_'):
                parts = concept_id[2:].split('_', 1)
                if len(parts) > 1:
                    if parts[0] == 'org':
                        entity_type = 'organisation'
                        display_name = parts[1].replace('_', ' ').title()
                        slug = parts[1]
                    elif parts[0] == 'model':
                        entity_type = 'model'
                        display_name = parts[1].replace('_', ' ').upper()
                        slug = parts[1]
                    elif parts[0] == 'person':
                        entity_type = 'person'
                        display_name = parts[1].replace('_', ' ').title()
                        slug = parts[1]
                    else:
                        display_name = concept_id[2:].replace('_', ' ').title()
                        slug = concept_id[2:]
            
            # Create the concept
            new_concept = {
                'slug': slug.lower(),
                'display_name': display_name,
                'description': f'Auto-created for orphaned annotations ({count} uses)',
                'entity_type': entity_type,
                'parents': [],
                'children': [],
                'status': 'active',
                'needs_review': True,
                'created_by': 'orphan_fix_script'
            }
            
            result = db.tag_concepts_v2.insert_one(new_concept)
            new_id = str(result.inserted_id)
            
            # Update annotations
            update_result = db.tag_instances.update_many(
                {'concept_id': concept_id},
                {'$set': {'concept_id': new_id}}
            )
            
            logger.info(f"Created concept '{display_name}' and linked {update_result.modified_count} annotations")
            fixed_count += update_result.modified_count
    
    # Final check
    remaining_orphans = 0
    for item in db.tag_instances.aggregate([
        {'$group': {'_id': '$concept_id', 'count': {'$sum': 1}}}
    ]):
        concept_id = item['_id']
        if len(concept_id) == 24:
            try:
                if not db.tag_concepts_v2.find_one({'_id': ObjectId(concept_id)}):
                    remaining_orphans += item['count']
            except:
                remaining_orphans += item['count']
        else:
            if not db.tag_concepts_v2.find_one({'id': concept_id}):
                remaining_orphans += item['count']
    
    logger.info(f"\n{'='*60}")
    logger.info(f"FINAL STATUS")
    logger.info(f"Total annotations: {db.tag_instances.count_documents({})}")
    logger.info(f"Fixed/created: {fixed_count}")
    logger.info(f"Remaining orphans: {remaining_orphans}")
    logger.info(f"{'='*60}")
    
    client.close()

if __name__ == "__main__":
    print("\nOrphaned Annotation Fixer")
    print("="*60)
    print("This will fix annotations with incorrect concept_ids")
    print("from the SQLite migration.")
    print("="*60)
    
    fix_orphaned_annotations()