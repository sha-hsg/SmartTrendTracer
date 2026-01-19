#!/usr/bin/env python3
"""
Script to safely remove all SQLite tag tables after confirming migration to MongoDB
This completes the final step of the concept conversion
"""

import logging
from sqlalchemy import create_engine, text, inspect
from pymongo import MongoClient
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connections
SQLITE_URL = "sqlite:///data/tweets.db"
MONGODB_URL = "mongodb://localhost:27017/"

def check_migration_status():
    """Verify that all tags have been migrated to MongoDB"""
    
    # Setup connections
    engine = create_engine(SQLITE_URL)
    mongo_client = MongoClient(MONGODB_URL)
    db = mongo_client.smarttrendtracer
    
    logger.info("=" * 70)
    logger.info("CHECKING MIGRATION STATUS")
    logger.info("=" * 70)
    
    # Check SQLite tag tables
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    tag_tables = [t for t in tables if 'tag' in t.lower()]
    logger.info(f"\nSQLite tag tables found: {tag_tables}")
    
    stats = {}
    
    with engine.connect() as conn:
        # Check each tag table
        for table in tag_tables:
            try:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                stats[table] = count
                logger.info(f"  {table}: {count} records")
            except Exception as e:
                logger.error(f"  Error reading {table}: {e}")
                stats[table] = 0
    
    # Check MongoDB
    logger.info("\nMongoDB collections:")
    mongo_stats = {
        'tag_concepts_v2': db.tag_concepts_v2.count_documents({}),
        'tag_aliases_v2': db.tag_aliases_v2.count_documents({}),
        'tag_instances': db.tag_instances.count_documents({})
    }
    
    for collection, count in mongo_stats.items():
        logger.info(f"  {collection}: {count} documents")
    
    # Check content type breakdown in MongoDB
    logger.info("\nMongoDB tag_instances by content type:")
    for content_type in ['tweet', 'article', 'paper']:
        count = db.tag_instances.count_documents({'content_type': content_type})
        logger.info(f"  {content_type}: {count} instances")
    
    mongo_client.close()
    
    return stats, mongo_stats

def backup_tag_tables():
    """Create backup of tag tables before deletion"""
    import os
    import shutil
    from datetime import datetime
    
    # Create backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"data/tweets.db.backup_before_tag_removal_{timestamp}"
    
    if os.path.exists("data/tweets.db"):
        shutil.copy2("data/tweets.db", backup_path)
        logger.info(f"Created backup: {backup_path}")
        return backup_path
    else:
        logger.error("Database file not found!")
        return None

def remove_tag_tables(dry_run=True):
    """Remove SQLite tag tables"""
    
    engine = create_engine(SQLITE_URL)
    
    # Tables to remove
    tables_to_remove = [
        'tags',           # Tweet tags
        'paper_tags',     # Paper tags  
        'article_tags',   # Article tags
        'snippet_tags',   # Snippet tags
        'tag_hierarchy',  # Old hierarchy table
        'tag_synonyms'    # Old synonyms table
    ]
    
    logger.info("\n" + "=" * 70)
    logger.info("REMOVING SQLITE TAG TABLES")
    logger.info("=" * 70)
    
    if dry_run:
        logger.info("DRY RUN MODE - No changes will be made")
    
    with engine.connect() as conn:
        # Get existing tables
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        for table in tables_to_remove:
            if table in existing_tables:
                if dry_run:
                    logger.info(f"Would remove table: {table}")
                else:
                    try:
                        conn.execute(text(f"DROP TABLE {table}"))
                        conn.commit()
                        logger.info(f"✓ Removed table: {table}")
                    except Exception as e:
                        logger.error(f"✗ Error removing {table}: {e}")
            else:
                logger.info(f"Table not found: {table} (already removed?)")
    
    if not dry_run:
        logger.info("\nTag tables removed successfully!")
        logger.info("The system is now fully converted to MongoDB concepts")

def verify_system_health():
    """Check that the system still works without tag tables"""
    
    mongo_client = MongoClient(MONGODB_URL)
    db = mongo_client.smarttrendtracer
    
    logger.info("\n" + "=" * 70)
    logger.info("VERIFYING SYSTEM HEALTH")
    logger.info("=" * 70)
    
    # Check that we can query concepts
    try:
        concepts = list(db.tag_concepts_v2.find().limit(5))
        logger.info(f"✓ Can query concepts: Found {len(concepts)} concepts")
    except Exception as e:
        logger.error(f"✗ Error querying concepts: {e}")
        return False
    
    # Check that we can query tag instances
    try:
        instances = list(db.tag_instances.find().limit(5))
        logger.info(f"✓ Can query tag instances: Found {len(instances)} instances")
    except Exception as e:
        logger.error(f"✗ Error querying tag instances: {e}")
        return False
    
    # Check concept service
    try:
        from app.services.concept_only_tag_service import ConceptOnlyTagService
        service = ConceptOnlyTagService()
        all_concepts = service.get_all_concepts_with_counts()
        logger.info(f"✓ Concept service works: {len(all_concepts)} concepts with counts")
    except Exception as e:
        logger.error(f"✗ Error with concept service: {e}")
        return False
    
    mongo_client.close()
    logger.info("\n✓ System health check passed!")
    return True

def main():
    """Main execution"""
    
    logger.info("SQLite Tag Tables Removal Script")
    logger.info("This will complete the conversion to MongoDB concepts")
    logger.info("")
    
    # Step 1: Check migration status
    sqlite_stats, mongo_stats = check_migration_status()
    
    # Step 2: Verify MongoDB has data
    if mongo_stats['tag_instances'] == 0:
        logger.error("\nERROR: MongoDB tag_instances is empty!")
        logger.error("Migration must be completed before removing SQLite tables")
        sys.exit(1)
    
    # Step 3: Ask for confirmation
    logger.info("\n" + "=" * 70)
    logger.info("READY TO REMOVE SQLITE TAG TABLES")
    logger.info("=" * 70)
    logger.info(f"SQLite tags to remove: {sum(sqlite_stats.values())} total records")
    logger.info(f"MongoDB has: {mongo_stats['tag_instances']} tag instances")
    
    response = input("\nDo you want to proceed? (yes/no): ").strip().lower()
    
    if response != 'yes':
        logger.info("Aborted by user")
        sys.exit(0)
    
    # Step 4: Create backup
    backup_path = backup_tag_tables()
    if not backup_path:
        logger.error("Failed to create backup, aborting")
        sys.exit(1)
    
    # Step 5: Dry run first
    logger.info("\nPerforming dry run...")
    remove_tag_tables(dry_run=True)
    
    response = input("\nProceed with actual removal? (yes/no): ").strip().lower()
    
    if response != 'yes':
        logger.info("Aborted by user")
        sys.exit(0)
    
    # Step 6: Remove tables
    remove_tag_tables(dry_run=False)
    
    # Step 7: Verify system health
    if verify_system_health():
        logger.info("\n" + "=" * 70)
        logger.info("SUCCESS: SQLite tag tables removed!")
        logger.info("The system is now fully using MongoDB concepts")
        logger.info(f"Backup saved at: {backup_path}")
        logger.info("=" * 70)
    else:
        logger.error("\nWARNING: System health check failed")
        logger.error(f"You may need to restore from backup: {backup_path}")

if __name__ == "__main__":
    main()