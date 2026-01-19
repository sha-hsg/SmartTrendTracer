#!/usr/bin/env python3
"""
Setup MongoDB collection for persistent tag reorganization tasks
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_reorganization_collection():
    """Create and configure the tag_reorganization_tasks collection"""
    
    client = MongoClient('mongodb://localhost:27017/')
    db = client.smarttrendtracer
    
    # Create collection if it doesn't exist
    if 'tag_reorganization_tasks' not in db.list_collection_names():
        logger.info("Creating tag_reorganization_tasks collection...")
        db.create_collection('tag_reorganization_tasks')
    
    collection = db.tag_reorganization_tasks
    
    # Drop existing indexes except _id
    try:
        existing_indexes = collection.list_indexes()
        for index in existing_indexes:
            if index['name'] != '_id_':
                try:
                    collection.drop_index(index['name'])
                    logger.info(f"Dropped existing index: {index['name']}")
                except:
                    pass
    except:
        pass
    
    # Create indexes for efficient querying
    indexes = [
        ('created_at', DESCENDING),  # For sorting by recency
        ('status', ASCENDING),  # For filtering by status
        ('user_id', ASCENDING),  # For user-specific queries (future use)
    ]
    
    for field, direction in indexes:
        collection.create_index([(field, direction)])
    
    # Create compound index for common queries
    collection.create_index([
        ('status', ASCENDING),
        ('created_at', DESCENDING)
    ])
    
    # Create unique index on task_id
    collection.create_index([('task_id', ASCENDING)], unique=True)
    
    logger.info("✅ tag_reorganization_tasks collection setup complete")
    
    # Show collection stats
    stats = db.command("collStats", "tag_reorganization_tasks")
    logger.info(f"Collection stats: {stats.get('count', 0)} documents, {stats.get('size', 0)} bytes")
    
    return collection

def cleanup_old_tasks(days=30):
    """Remove tasks older than specified days"""
    from datetime import timedelta
    
    client = MongoClient('mongodb://localhost:27017/')
    db = client.smarttrendtracer
    collection = db.tag_reorganization_tasks
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    result = collection.delete_many({
        'created_at': {'$lt': cutoff_date}
    })
    
    logger.info(f"Cleaned up {result.deleted_count} tasks older than {days} days")
    
    return result.deleted_count

if __name__ == '__main__':
    # Setup collection
    collection = setup_reorganization_collection()
    
    # Optional: cleanup old tasks
    # cleanup_old_tasks(30)
    
    # Show sample document structure
    sample_doc = {
        'task_id': 'example-task-id',
        'status': 'completed',  # pending, processing, completed, failed, cancelled
        'mode': 'gpt5',
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow(),
        'completed_at': None,
        'progress': {
            'current': 0,
            'total': 0,
            'messages': []
        },
        'result': None,  # Will store the full reorganization result
        'error': None,
        'debug_info': {
            'prompt': None,
            'system_prompt': None,
            'prompt_size': 0,
            'system_prompt_size': 0
        },
        'metadata': {
            'concepts_count': 0,
            'organized_count': 0,
            'unorganized_count': 0,
            'processing_time_seconds': None
        }
    }
    
    logger.info(f"\nSample document structure:\n{sample_doc}")
    logger.info("\n✅ MongoDB setup complete for tag reorganization persistence")