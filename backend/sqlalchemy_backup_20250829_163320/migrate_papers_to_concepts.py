#!/usr/bin/env python3
"""
Migrate all paper tags from SQLite to MongoDB concepts
This completes the full conversion to concept-based system
"""

import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connections
SQLITE_URL = "sqlite:///data/tweets.db"
MONGODB_URL = "mongodb://localhost:27017/"

def migrate_paper_tags():
    """Migrate all paper tags to MongoDB tag_instances"""
    
    # Setup SQLite connection
    engine = create_engine(SQLITE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Setup MongoDB connection
    mongo_client = MongoClient(MONGODB_URL)
    db = mongo_client.smarttrendtracer
    
    logger.info("Starting paper tags migration to MongoDB concepts...")
    
    # Get all paper tags from SQLite
    result = session.execute(text("""
        SELECT paper_id, tag, created_at 
        FROM paper_tags
        ORDER BY paper_id, tag
    """))
    
    paper_tags = result.fetchall()
    logger.info(f"Found {len(paper_tags)} paper tags to migrate")
    
    # Get or create concept mappings
    concept_map = {}
    stats = {
        'migrated': 0,
        'already_exists': 0,
        'concept_created': 0,
        'errors': []
    }
    
    for paper_id, tag, created_at in paper_tags:
        try:
            # Normalize tag to concept slug
            tag_slug = tag.lower().replace(' ', '_').replace('-', '_')
            
            # Check if concept exists, create if not
            if tag_slug not in concept_map:
                concept = db.tag_concepts_v2.find_one({'slug': tag_slug})
                
                if not concept:
                    # Create new concept
                    concept = {
                        '_id': f'c_paper_{tag_slug}',
                        'id': f'c_paper_{tag_slug}',
                        'slug': tag_slug,
                        'display_name': tag,
                        'description': f'Auto-migrated from paper tag: {tag}',
                        'entity_type': 'concept',
                        'parents': [],  # Will be organized later
                        'children': [],
                        'created_at': datetime.utcnow(),
                        'source': 'paper_tag_migration'
                    }
                    db.tag_concepts_v2.insert_one(concept)
                    stats['concept_created'] += 1
                    logger.info(f"Created new concept: {tag_slug}")
                
                concept_map[tag_slug] = concept.get('_id') or concept.get('id')
            
            # Check if tag instance already exists
            existing = db.tag_instances.find_one({
                'content_id': str(paper_id),
                'content_type': 'paper',
                'concept_id': concept_map[tag_slug]
            })
            
            if existing:
                stats['already_exists'] += 1
                continue
            
            # Create tag instance
            tag_instance = {
                'content_id': str(paper_id),
                'content_type': 'paper',
                'concept_id': concept_map[tag_slug],
                'concept_slug': tag_slug,
                'created_at': created_at if created_at else datetime.utcnow(),
                'source': 'migration_from_sqlite'
            }
            
            db.tag_instances.insert_one(tag_instance)
            stats['migrated'] += 1
            
            if stats['migrated'] % 100 == 0:
                logger.info(f"Migrated {stats['migrated']} paper tags...")
                
        except Exception as e:
            error_msg = f"Error migrating paper {paper_id} tag {tag}: {str(e)}"
            logger.error(error_msg)
            stats['errors'].append(error_msg)
    
    # Log final statistics
    logger.info("=" * 70)
    logger.info("PAPER TAGS MIGRATION COMPLETE")
    logger.info("=" * 70)
    logger.info(f"Tags migrated: {stats['migrated']}")
    logger.info(f"Already existed: {stats['already_exists']}")
    logger.info(f"New concepts created: {stats['concept_created']}")
    logger.info(f"Errors: {len(stats['errors'])}")
    
    if stats['errors']:
        logger.info("\nFirst 10 errors:")
        for error in stats['errors'][:10]:
            logger.info(f"  - {error}")
    
    # Verify migration
    paper_count = db.tag_instances.count_documents({'content_type': 'paper'})
    logger.info(f"\nTotal paper tag instances in MongoDB: {paper_count}")
    
    session.close()
    mongo_client.close()
    
    return stats

def cleanup_old_paper_tags():
    """Remove old paper_tags table after successful migration"""
    engine = create_engine(SQLITE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Backup count for verification
        result = session.execute(text("SELECT COUNT(*) FROM paper_tags"))
        original_count = result.scalar()
        
        # Check MongoDB has the data
        mongo_client = MongoClient(MONGODB_URL)
        db = mongo_client.smarttrendtracer
        mongo_count = db.tag_instances.count_documents({'content_type': 'paper'})
        
        if mongo_count >= original_count:
            logger.info(f"MongoDB has {mongo_count} paper tags, SQLite had {original_count}")
            logger.info("Safe to remove old paper_tags table")
            
            # Comment out for safety - uncomment when ready
            # session.execute(text("DROP TABLE IF EXISTS paper_tags"))
            # session.commit()
            # logger.info("Removed old paper_tags table")
        else:
            logger.warning(f"MongoDB only has {mongo_count} tags but SQLite has {original_count}")
            logger.warning("Not removing paper_tags table - verification failed")
            
    except Exception as e:
        logger.error(f"Error in cleanup: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    # Run migration
    stats = migrate_paper_tags()
    
    # Cleanup if successful
    if stats['errors'] == []:
        logger.info("\nMigration successful, proceeding with cleanup check...")
        cleanup_old_paper_tags()
    else:
        logger.warning("\nMigration had errors, skipping cleanup")