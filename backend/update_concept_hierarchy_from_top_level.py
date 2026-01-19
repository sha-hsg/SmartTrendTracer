"""
Update existing MongoDB Concept Hierarchy with structure from top_level.json
This ensures Named Entities and Research Entities match the schema definition
"""

import json
from pymongo import MongoClient
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_concept_hierarchy():
    """Update MongoDB concept hierarchy to match top_level.json"""
    
    # Connect to MongoDB
    client = MongoClient("mongodb://localhost:27017/")
    db = client.smarttrendtracer
    concepts_col = db.tag_concepts_v2
    
    # Load top_level.json
    with open('top_level.json', 'r') as f:
        top_level = json.load(f)
    
    # Track updates
    stats = {
        'created': 0,
        'updated': 0,
        'skipped': 0,
        'errors': 0
    }
    
    # Process each main category (named-entities, research-entities)
    for category_key, category_data in top_level['entity_types'].items():
        logger.info(f"\nProcessing category: {category_key}")
        
        # Check if main category exists
        main_concept = concepts_col.find_one({"slug": category_key})
        
        if not main_concept:
            # Create main category
            main_concept_id = f"c_{category_key.replace('-', '_')}"
            main_concept = {
                "_id": main_concept_id,
                "id": main_concept_id,
                "slug": category_key,
                "display_name": category_data['display_name'],
                "description": category_data['description'],
                "entity_type": "category",
                "parents": [],  # Top-level categories have no parents
                "children": [],
                "level": category_data['level'],
                "icon": category_data.get('icon', '🏷️'),
                "color": category_data.get('color', '#6B7280'),
                "usage_count": 0,
                "status": "active",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "metadata": {
                    "source": "top_level.json",
                    "version": top_level['version']
                }
            }
            concepts_col.insert_one(main_concept)
            stats['created'] += 1
            logger.info(f"  Created main category: {category_key}")
        else:
            # Update existing category
            updates = {
                "display_name": category_data['display_name'],
                "description": category_data['description'],
                "icon": category_data.get('icon', main_concept.get('icon', '🏷️')),
                "color": category_data.get('color', main_concept.get('color', '#6B7280')),
                "level": category_data['level'],
                "updated_at": datetime.utcnow()
            }
            concepts_col.update_one(
                {"_id": main_concept['_id']},
                {"$set": updates}
            )
            stats['updated'] += 1
            logger.info(f"  Updated main category: {category_key}")
        
        main_concept_id = main_concept.get('_id', main_concept.get('id'))
        
        # Process children
        children_ids = []
        for child_key, child_data in category_data.get('children', {}).items():
            logger.info(f"    Processing child: {child_key}")
            
            # Generate child concept ID
            child_concept_id = f"c_et_{child_key}"
            
            # Check if child exists
            child_concept = concepts_col.find_one({
                "$or": [
                    {"_id": child_concept_id},
                    {"id": child_concept_id},
                    {"slug": child_key}
                ]
            })
            
            if not child_concept:
                # Create child concept
                child_concept = {
                    "_id": child_concept_id,
                    "id": child_concept_id,
                    "slug": child_key,
                    "display_name": child_data['display_name'],
                    "description": child_data['description'],
                    "entity_type": child_key,  # The entity type is the key itself
                    "parents": [main_concept_id],
                    "children": [],
                    "level": child_data['level'],
                    "icon": child_data.get('icon', '🏷️'),
                    "color": child_data.get('color', '#6B7280'),
                    "usage_count": 0,
                    "status": "active",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "metadata": {
                        "source": "top_level.json",
                        "version": top_level['version'],
                        "extraction_hints": child_data.get('extraction_hints', []),
                        "validation_rules": child_data.get('validation_rules', {})
                    }
                }
                concepts_col.insert_one(child_concept)
                stats['created'] += 1
                logger.info(f"      Created child: {child_key}")
            else:
                # Update existing child
                updates = {
                    "display_name": child_data['display_name'],
                    "description": child_data['description'],
                    "entity_type": child_key,
                    "icon": child_data.get('icon', child_concept.get('icon', '🏷️')),
                    "color": child_data.get('color', child_concept.get('color', '#6B7280')),
                    "level": child_data['level'],
                    "updated_at": datetime.utcnow(),
                    "metadata.extraction_hints": child_data.get('extraction_hints', []),
                    "metadata.validation_rules": child_data.get('validation_rules', {})
                }
                
                # Ensure parent relationship exists
                if main_concept_id not in child_concept.get('parents', []):
                    updates['parents'] = child_concept.get('parents', []) + [main_concept_id]
                
                concepts_col.update_one(
                    {"_id": child_concept['_id']},
                    {"$set": updates}
                )
                stats['updated'] += 1
                logger.info(f"      Updated child: {child_key}")
            
            children_ids.append(child_concept_id)
        
        # Update main category's children list
        if children_ids:
            concepts_col.update_one(
                {"_id": main_concept_id},
                {"$set": {"children": children_ids}}
            )
            logger.info(f"  Updated children list for {category_key}: {children_ids}")
    
    # Print summary
    logger.info("\n" + "="*50)
    logger.info("Update Summary:")
    logger.info(f"  Created: {stats['created']} concepts")
    logger.info(f"  Updated: {stats['updated']} concepts")
    logger.info(f"  Skipped: {stats['skipped']} concepts")
    logger.info(f"  Errors: {stats['errors']}")
    
    # Verify the hierarchy
    logger.info("\n" + "="*50)
    logger.info("Verifying Named Entities Hierarchy:")
    named_entities = concepts_col.find_one({"slug": "named-entities"})
    if named_entities:
        logger.info(f"  Named Entities ID: {named_entities['_id']}")
        logger.info(f"  Children: {named_entities.get('children', [])}")
        
        for child_id in named_entities.get('children', []):
            child = concepts_col.find_one({"_id": child_id})
            if child:
                logger.info(f"    - {child['slug']}: {child['display_name']} ({child.get('entity_type', 'unknown')})")
    
    logger.info("\nVerifying Research Entities Hierarchy:")
    research_entities = concepts_col.find_one({"slug": "research-entities"})
    if research_entities:
        logger.info(f"  Research Entities ID: {research_entities['_id']}")
        logger.info(f"  Children: {research_entities.get('children', [])}")
        
        for child_id in research_entities.get('children', []):
            child = concepts_col.find_one({"_id": child_id})
            if child:
                logger.info(f"    - {child['slug']}: {child['display_name']} ({child.get('entity_type', 'unknown')})")
    
    return stats

if __name__ == "__main__":
    stats = update_concept_hierarchy()
    print(f"\nUpdate complete! Created: {stats['created']}, Updated: {stats['updated']}")