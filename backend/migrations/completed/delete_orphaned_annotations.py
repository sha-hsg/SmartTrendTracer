#!/usr/bin/env python3
"""
Delete orphaned annotations that have incorrect concept_id values.
These duplicate valid annotations and should be removed.
"""

from pymongo import MongoClient
from bson import ObjectId
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def delete_orphaned_annotations():
    """
    Delete annotations with invalid concept_ids (c_xxxx format)
    """
    client = MongoClient('mongodb://localhost:27017/')
    db = client.smarttrendtracer
    
    # Find all annotations with c_ style concept_ids
    orphaned = db.tag_instances.find({'concept_id': {'$regex': '^c_'}})
    orphaned_count = db.tag_instances.count_documents({'concept_id': {'$regex': '^c_'}})
    
    logger.info(f"Found {orphaned_count} orphaned annotations with c_ style concept_ids")
    
    # Delete them
    result = db.tag_instances.delete_many({'concept_id': {'$regex': '^c_'}})
    
    logger.info(f"Deleted {result.deleted_count} orphaned annotations")
    
    # Also check for other invalid formats (not 24-char hex strings)
    all_concept_ids = db.tag_instances.distinct('concept_id')
    invalid_count = 0
    
    for concept_id in all_concept_ids:
        if isinstance(concept_id, ObjectId):
            continue  # Skip ObjectIds, they're valid
        
        if not isinstance(concept_id, str) or len(concept_id) != 24:
            # Not a valid ObjectId string
            count = db.tag_instances.count_documents({'concept_id': concept_id})
            logger.info(f"Invalid concept_id format: {concept_id} ({count} annotations)")
            invalid_count += count
            
            # Delete these too
            db.tag_instances.delete_many({'concept_id': concept_id})
    
    logger.info(f"Deleted {invalid_count} additional invalid annotations")
    
    # Final check
    total_annotations = db.tag_instances.count_documents({})
    
    # Verify all remaining annotations point to valid concepts
    valid_count = 0
    still_orphaned = 0
    
    for ann in db.tag_instances.find():
        try:
            concept = db.tag_concepts_v2.find_one({'_id': ObjectId(ann['concept_id'])})
            if concept:
                valid_count += 1
            else:
                still_orphaned += 1
                logger.warning(f"Still orphaned: {ann['concept_id']}")
        except:
            still_orphaned += 1
            logger.warning(f"Invalid ObjectId: {ann['concept_id']}")
    
    logger.info(f"\n{'='*60}")
    logger.info(f"CLEANUP COMPLETE")
    logger.info(f"{'='*60}")
    logger.info(f"Total annotations remaining: {total_annotations}")
    logger.info(f"Valid annotations: {valid_count}")
    logger.info(f"Still orphaned: {still_orphaned}")
    logger.info(f"{'='*60}")
    
    client.close()

if __name__ == "__main__":
    print("\nOrphaned Annotation Deletion")
    print("="*60)
    print("This will DELETE orphaned annotations with invalid concept_ids")
    print("These are duplicates from the SQLite migration.")
    print("="*60)
    
    response = input("Are you sure you want to DELETE orphaned annotations? (yes/no): ")
    if response.lower() == 'yes':
        delete_orphaned_annotations()
    else:
        print("Aborted.")