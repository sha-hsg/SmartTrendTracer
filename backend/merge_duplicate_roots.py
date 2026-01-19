#!/usr/bin/env python3
"""
Merge duplicate root concepts in MongoDB
Based on analysis, we have these duplicates to merge:

1. Applications - 3 versions
2. Data - 3 versions  
3. Evaluation - 3 versions
4. Models - 2 versions
5. Techniques - 2 versions
"""

from pymongo import MongoClient
from bson import ObjectId
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def merge_duplicate_roots():
    """
    Merge duplicate root concepts, keeping the one with most children
    """
    client = MongoClient('mongodb://localhost:27017/')
    db = client.smarttrendtracer
    
    merges = [
        {
            'name': 'Applications',
            'keep': ObjectId('68af78566b4944766c2e6f08'),  # Applications & Domains (97 children)
            'merge': [
                ObjectId('68aa2d04857c1e09148ea8bd'),  # Applications and Tasks (16 children)
                ObjectId('68af7353b359e19ae14ca44a')   # Applications (7 children)
            ]
        },
        {
            'name': 'Data',
            'keep': ObjectId('68af78566b4944766c2e6f09'),  # Data & Datasets (77 children)
            'merge': [
                ObjectId('68aa2d04857c1e09148ea8bb'),  # Data and Datasets (7 children)
                ObjectId('68af7353b359e19ae14ca449')   # Data (2 children)
            ]
        },
        {
            'name': 'Evaluation',
            'keep': ObjectId('68af438b5131c4b0d0fb10fe'),  # Evaluation & Metrics (72 children)
            'merge': [
                ObjectId('68aa2d04857c1e09148ea8bc'),  # Evaluation and Benchmarks (10 children)
                ObjectId('68af7353b359e19ae14ca44b')   # Evaluation (15 children)
            ],
            'rename': 'Evaluation & Benchmarks'  # More descriptive name
        },
        {
            'name': 'Models',
            'keep': ObjectId('68af78566b4944766c2e6f06'),  # Models & Architectures (294 children)
            'merge': [
                ObjectId('68af7390d62a22930fc849ae')   # Models and Architectures (6 children)
            ]
        },
        {
            'name': 'Techniques',
            'keep': ObjectId('68af78566b4944766c2e6f07'),  # Techniques & Methods (60 children)
            'merge': [
                ObjectId('68af7390d62a22930fc849af')   # Techniques and Methods (8 children)
            ]
        }
    ]
    
    total_merged = 0
    total_children_moved = 0
    
    for merge_config in merges:
        name = merge_config['name']
        keep_id = merge_config['keep']
        merge_ids = merge_config['merge']
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Merging {name} concepts...")
        
        # Get the concept we're keeping
        keep_concept = db.tag_concepts_v2.find_one({'_id': keep_id})
        if not keep_concept:
            logger.error(f"  Could not find concept to keep: {keep_id}")
            continue
        
        logger.info(f"  Keeping: {keep_concept['display_name']} ({len(keep_concept.get('children', []))} children)")
        
        # Process each duplicate to merge
        for merge_id in merge_ids:
            merge_concept = db.tag_concepts_v2.find_one({'_id': merge_id})
            if not merge_concept:
                logger.warning(f"  Could not find concept to merge: {merge_id}")
                continue
            
            logger.info(f"  Merging: {merge_concept['display_name']} ({len(merge_concept.get('children', []))} children)")
            
            # Move all children to the keeper
            children_to_move = merge_concept.get('children', [])
            if children_to_move:
                # Update each child's parent
                for child_id in children_to_move:
                    result = db.tag_concepts_v2.update_one(
                        {'_id': child_id},
                        {'$set': {'parents': [keep_id]}}
                    )
                    if result.modified_count > 0:
                        total_children_moved += 1
                
                # Add children to keeper (using $addToSet to avoid duplicates)
                db.tag_concepts_v2.update_one(
                    {'_id': keep_id},
                    {'$addToSet': {'children': {'$each': children_to_move}}}
                )
            
            # Delete the duplicate
            result = db.tag_concepts_v2.delete_one({'_id': merge_id})
            if result.deleted_count > 0:
                total_merged += 1
                logger.info(f"    ✓ Deleted duplicate: {merge_concept['display_name']}")
        
        # Rename if specified
        if 'rename' in merge_config:
            db.tag_concepts_v2.update_one(
                {'_id': keep_id},
                {'$set': {'display_name': merge_config['rename']}}
            )
            logger.info(f"  Renamed to: {merge_config['rename']}")
    
    # Final statistics
    logger.info(f"\n{'='*60}")
    logger.info("Merge Complete!")
    logger.info(f"  Duplicates merged: {total_merged}")
    logger.info(f"  Children moved: {total_children_moved}")
    
    # Check final state
    root_count = db.tag_concepts_v2.count_documents({'parents': {'$size': 0}})
    total_count = db.tag_concepts_v2.count_documents({})
    
    logger.info(f"\nFinal State:")
    logger.info(f"  Total concepts: {total_count}")
    logger.info(f"  Root concepts: {root_count}")
    
    # List remaining root concepts
    logger.info(f"\nRemaining Root Concepts:")
    roots = list(db.tag_concepts_v2.find({'parents': {'$size': 0}}))
    for root in roots:
        children_count = len(root.get('children', []))
        logger.info(f"  - {root['display_name']}: {children_count} children")
    
    client.close()

if __name__ == "__main__":
    print("\nDuplicate Root Concept Merger")
    print("="*60)
    print("This will merge duplicate root concepts, keeping the one with most children.")
    print("\nDuplicates to merge:")
    print("  - Applications (3 versions)")
    print("  - Data (3 versions)")
    print("  - Evaluation (3 versions)")
    print("  - Models (2 versions)")
    print("  - Techniques (2 versions)")
    print("\nProceeding with merge...")
    
    merge_duplicate_roots()