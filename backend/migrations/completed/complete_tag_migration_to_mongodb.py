#!/usr/bin/env python3
"""
Complete migration of all tag data from SQLite to MongoDB.
This script migrates tweets, papers, and articles tags to MongoDB tag_instances collection.
"""

import sqlite3
from datetime import datetime
from pymongo import MongoClient, UpdateOne
from typing import List, Dict, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_sqlite_connection():
    """Get SQLite connection"""
    return sqlite3.connect('data/tweets.db')

def get_mongodb_client():
    """Get MongoDB client and database"""
    client = MongoClient('mongodb://localhost:27017/')
    return client.smarttrendtracer

def clear_existing_mongodb_tags(db):
    """Clear existing tag_instances in MongoDB to avoid duplicates"""
    logger.info("Clearing existing tag_instances in MongoDB...")
    result = db.tag_instances.delete_many({})
    logger.info(f"Deleted {result.deleted_count} existing tag instances")

def migrate_tweet_tags(sqlite_conn, mongodb_db):
    """Migrate tweet tags from SQLite to MongoDB"""
    logger.info("Migrating tweet tags...")
    
    cursor = sqlite_conn.cursor()
    cursor.execute("""
        SELECT id, tweet_id, tag, tag_type, confidence, created_at
        FROM tags
        ORDER BY id
    """)
    
    tags = cursor.fetchall()
    logger.info(f"Found {len(tags)} tweet tags to migrate")
    
    if not tags:
        return 0
    
    # Prepare documents for MongoDB
    documents = []
    for tag_id, tweet_id, tag_text, tag_type, confidence, created_at in tags:
        doc = {
            'content_type': 'tweet',
            'content_id': tweet_id,
            'tag_text': tag_text.lower() if tag_text else '',  # Normalize to lowercase
            'tag_type': tag_type or 'manual',
            'confidence': confidence,
            'created_at': created_at or datetime.now().isoformat(),
            'migrated_from_sqlite': True,
            'original_sqlite_id': tag_id
        }
        
        # Try to find matching concept
        concept = mongodb_db.tag_concepts_v2.find_one({
            '$or': [
                {'slug': tag_text.lower()},
                {'name': tag_text},
                {'slug': tag_text.replace(' ', '-').lower()}
            ]
        })
        
        if concept:
            doc['concept_id'] = str(concept['_id'])
        else:
            # Check aliases
            alias = mongodb_db.tag_aliases_v2.find_one({'alias': tag_text.lower()})
            if alias:
                doc['concept_id'] = alias['concept_id']
            else:
                doc['concept_id'] = None  # Orphan tag
        
        documents.append(doc)
    
    # Insert in batches
    batch_size = 500
    total_inserted = 0
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i+batch_size]
        result = mongodb_db.tag_instances.insert_many(batch)
        total_inserted += len(result.inserted_ids)
        logger.info(f"Inserted batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}")
    
    logger.info(f"Successfully migrated {total_inserted} tweet tags")
    return total_inserted

def migrate_paper_tags(sqlite_conn, mongodb_db):
    """Migrate paper tags from SQLite to MongoDB"""
    logger.info("Migrating paper tags...")
    
    cursor = sqlite_conn.cursor()
    cursor.execute("""
        SELECT id, paper_id, tag, tag_type, confidence, created_at
        FROM paper_tags
        ORDER BY id
    """)
    
    tags = cursor.fetchall()
    logger.info(f"Found {len(tags)} paper tags to migrate")
    
    if not tags:
        return 0
    
    # Prepare documents for MongoDB
    documents = []
    for tag_id, paper_id, tag_text, tag_type, confidence, created_at in tags:
        doc = {
            'content_type': 'paper',
            'content_id': str(paper_id),  # Convert to string for consistency
            'tag_text': tag_text.lower() if tag_text else '',
            'tag_type': tag_type or 'manual',
            'confidence': confidence,
            'created_at': created_at or datetime.now().isoformat(),
            'migrated_from_sqlite': True,
            'original_sqlite_id': tag_id
        }
        
        # Try to find matching concept
        concept = mongodb_db.tag_concepts_v2.find_one({
            '$or': [
                {'slug': tag_text.lower()},
                {'name': tag_text},
                {'slug': tag_text.replace(' ', '-').lower()}
            ]
        })
        
        if concept:
            doc['concept_id'] = str(concept['_id'])
        else:
            # Check aliases
            alias = mongodb_db.tag_aliases_v2.find_one({'alias': tag_text.lower()})
            if alias:
                doc['concept_id'] = alias['concept_id']
            else:
                doc['concept_id'] = None  # Orphan tag
        
        documents.append(doc)
    
    # Insert in batches
    batch_size = 500
    total_inserted = 0
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i+batch_size]
        result = mongodb_db.tag_instances.insert_many(batch)
        total_inserted += len(result.inserted_ids)
        logger.info(f"Inserted batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}")
    
    logger.info(f"Successfully migrated {total_inserted} paper tags")
    return total_inserted

def migrate_article_tags(sqlite_conn, mongodb_db):
    """Migrate article tags from SQLite to MongoDB"""
    logger.info("Migrating article tags...")
    
    cursor = sqlite_conn.cursor()
    cursor.execute("""
        SELECT id, article_id, tag, tag_type, confidence, created_at
        FROM article_tags
        ORDER BY id
    """)
    
    tags = cursor.fetchall()
    logger.info(f"Found {len(tags)} article tags to migrate")
    
    if not tags:
        return 0
    
    # Prepare documents for MongoDB
    documents = []
    for tag_id, article_id, tag_text, tag_type, confidence, created_at in tags:
        doc = {
            'content_type': 'article',
            'content_id': str(article_id),  # Convert to string for consistency
            'tag_text': tag_text.lower() if tag_text else '',
            'tag_type': tag_type or 'manual',
            'confidence': confidence,
            'created_at': created_at or datetime.now().isoformat(),
            'migrated_from_sqlite': True,
            'original_sqlite_id': tag_id
        }
        
        # Try to find matching concept
        concept = mongodb_db.tag_concepts_v2.find_one({
            '$or': [
                {'slug': tag_text.lower()},
                {'name': tag_text},
                {'slug': tag_text.replace(' ', '-').lower()}
            ]
        })
        
        if concept:
            doc['concept_id'] = str(concept['_id'])
        else:
            # Check aliases
            alias = mongodb_db.tag_aliases_v2.find_one({'alias': tag_text.lower()})
            if alias:
                doc['concept_id'] = alias['concept_id']
            else:
                doc['concept_id'] = None  # Orphan tag
        
        documents.append(doc)
    
    # Insert in batches
    batch_size = 500
    total_inserted = 0
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i+batch_size]
        result = mongodb_db.tag_instances.insert_many(batch)
        total_inserted += len(result.inserted_ids)
        logger.info(f"Inserted batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}")
    
    logger.info(f"Successfully migrated {total_inserted} article tags")
    return total_inserted

def create_indexes(mongodb_db):
    """Create necessary indexes for performance"""
    logger.info("Creating indexes...")
    
    # Create compound index for content lookups
    mongodb_db.tag_instances.create_index([
        ('content_type', 1),
        ('content_id', 1)
    ])
    
    # Create index for tag_text searches
    mongodb_db.tag_instances.create_index('tag_text')
    
    # Create index for concept_id lookups
    mongodb_db.tag_instances.create_index('concept_id')
    
    # Create index for orphan tags
    mongodb_db.tag_instances.create_index([
        ('concept_id', 1),
        ('content_type', 1)
    ])
    
    logger.info("Indexes created successfully")

def verify_migration(sqlite_conn, mongodb_db):
    """Verify the migration was successful"""
    logger.info("\nVerifying migration...")
    
    cursor = sqlite_conn.cursor()
    
    # Check tweet tags
    cursor.execute("SELECT COUNT(*) FROM tags")
    sqlite_tweet_count = cursor.fetchone()[0]
    mongo_tweet_count = mongodb_db.tag_instances.count_documents({'content_type': 'tweet'})
    
    # Check paper tags
    cursor.execute("SELECT COUNT(*) FROM paper_tags")
    sqlite_paper_count = cursor.fetchone()[0]
    mongo_paper_count = mongodb_db.tag_instances.count_documents({'content_type': 'paper'})
    
    # Check article tags
    cursor.execute("SELECT COUNT(*) FROM article_tags")
    sqlite_article_count = cursor.fetchone()[0]
    mongo_article_count = mongodb_db.tag_instances.count_documents({'content_type': 'article'})
    
    # Count orphan tags
    orphan_count = mongodb_db.tag_instances.count_documents({'concept_id': None})
    resolved_count = mongodb_db.tag_instances.count_documents({'concept_id': {'$ne': None}})
    
    logger.info("\n" + "="*50)
    logger.info("MIGRATION VERIFICATION REPORT")
    logger.info("="*50)
    logger.info(f"\nTweet Tags:")
    logger.info(f"  SQLite:  {sqlite_tweet_count}")
    logger.info(f"  MongoDB: {mongo_tweet_count}")
    logger.info(f"  Match:   {'✓' if sqlite_tweet_count == mongo_tweet_count else '✗'}")
    
    logger.info(f"\nPaper Tags:")
    logger.info(f"  SQLite:  {sqlite_paper_count}")
    logger.info(f"  MongoDB: {mongo_paper_count}")
    logger.info(f"  Match:   {'✓' if sqlite_paper_count == mongo_paper_count else '✗'}")
    
    logger.info(f"\nArticle Tags:")
    logger.info(f"  SQLite:  {sqlite_article_count}")
    logger.info(f"  MongoDB: {mongo_article_count}")
    logger.info(f"  Match:   {'✓' if sqlite_article_count == mongo_article_count else '✗'}")
    
    total_sqlite = sqlite_tweet_count + sqlite_paper_count + sqlite_article_count
    total_mongo = mongo_tweet_count + mongo_paper_count + mongo_article_count
    
    logger.info(f"\nTotal Tags:")
    logger.info(f"  SQLite:  {total_sqlite}")
    logger.info(f"  MongoDB: {total_mongo}")
    logger.info(f"  Match:   {'✓' if total_sqlite == total_mongo else '✗'}")
    
    logger.info(f"\nTag Resolution:")
    logger.info(f"  Resolved to concepts: {resolved_count} ({resolved_count*100/total_mongo:.1f}%)")
    logger.info(f"  Orphan tags:         {orphan_count} ({orphan_count*100/total_mongo:.1f}%)")
    
    logger.info("="*50)
    
    return total_sqlite == total_mongo

def main():
    """Main migration function"""
    logger.info("Starting complete tag migration to MongoDB...")
    
    try:
        # Get connections
        sqlite_conn = get_sqlite_connection()
        mongodb_db = get_mongodb_client()
        
        # Clear existing MongoDB tags to avoid duplicates
        clear_existing_mongodb_tags(mongodb_db)
        
        # Migrate each type
        tweet_count = migrate_tweet_tags(sqlite_conn, mongodb_db)
        paper_count = migrate_paper_tags(sqlite_conn, mongodb_db)
        article_count = migrate_article_tags(sqlite_conn, mongodb_db)
        
        # Create indexes
        create_indexes(mongodb_db)
        
        # Verify migration
        success = verify_migration(sqlite_conn, mongodb_db)
        
        if success:
            logger.info("\n✅ Migration completed successfully!")
            logger.info(f"Total tags migrated: {tweet_count + paper_count + article_count}")
            logger.info("\nNext steps:")
            logger.info("1. Update backend APIs to use MongoDB tag_instances")
            logger.info("2. Test all tag operations")
            logger.info("3. Once verified, remove SQLite tag tables")
        else:
            logger.error("\n❌ Migration verification failed! Check the counts above.")
            logger.error("The data has been migrated but counts don't match.")
            logger.error("Please investigate before proceeding.")
        
        # Close connections
        sqlite_conn.close()
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return success

if __name__ == "__main__":
    main()