#!/usr/bin/env python3
"""
Script to calculate and store readability scores for all papers in the database.
This is a one-time calculation that stores the scores in MongoDB.
"""

import logging
from pymongo import MongoClient, UpdateOne
from app.services.readability_service import ReadabilityService
from tqdm import tqdm

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_and_store_readability():
    """Calculate readability scores for all papers and store in database"""
    
    # Connect to MongoDB
    client = MongoClient("mongodb://localhost:27017/")
    db = client.smarttrendtracer
    
    # Initialize readability service
    readability_service = ReadabilityService()
    
    # Get all papers that have content but no readability scores
    papers = list(db.papers.find({
        'content': {'$exists': True, '$ne': None, '$ne': ''},
        '$or': [
            {'readability': {'$exists': False}},
            {'readability': None},
            {'readability': {}}
        ]
    }, {'_id': 1, 'title': 1, 'content': 1}))
    
    logger.info(f"Found {len(papers)} papers without readability scores")
    
    if not papers:
        logger.info("All papers already have readability scores!")
        
        # Check papers with readability scores
        papers_with_scores = db.papers.count_documents({
            'readability': {'$exists': True, '$ne': None, '$ne': {}}
        })
        logger.info(f"Papers with readability scores: {papers_with_scores}")
        return
    
    # Prepare bulk updates
    bulk_updates = []
    success_count = 0
    error_count = 0
    
    for paper in tqdm(papers, desc="Calculating readability"):
        try:
            # Calculate readability metrics
            readability_metrics = readability_service.get_readability_metrics(paper['content'])
            
            # Only update if we got valid metrics
            if readability_metrics and any(v is not None for v in readability_metrics.values()):
                bulk_updates.append(
                    UpdateOne(
                        {'_id': paper['_id']},
                        {'$set': {'readability': readability_metrics}}
                    )
                )
                success_count += 1
                
                # Log sample output for first few papers
                if success_count <= 3:
                    logger.info(f"Paper: {paper['title'][:50]}...")
                    logger.info(f"  Flesch Reading Ease: {readability_metrics.get('flesch_reading_ease')}")
                    logger.info(f"  Grade Level: {readability_metrics.get('flesch_kincaid_grade')}")
                    logger.info(f"  Difficulty: {readability_metrics.get('difficulty')}")
                    logger.info(f"  Academic Level: {readability_metrics.get('academic_level')}")
            else:
                logger.warning(f"Could not calculate readability for paper {paper['_id']}: {paper['title'][:50]}...")
                error_count += 1
                
        except Exception as e:
            logger.error(f"Error processing paper {paper['_id']}: {e}")
            error_count += 1
            continue
        
        # Execute bulk updates every 50 papers to avoid memory issues
        if len(bulk_updates) >= 50:
            result = db.papers.bulk_write(bulk_updates)
            logger.info(f"Updated {result.modified_count} papers")
            bulk_updates = []
    
    # Execute remaining updates
    if bulk_updates:
        result = db.papers.bulk_write(bulk_updates)
        logger.info(f"Updated {result.modified_count} papers")
    
    logger.info(f"Completed! Successfully calculated readability for {success_count} papers")
    if error_count > 0:
        logger.warning(f"Failed to calculate readability for {error_count} papers")
    
    # Show statistics
    total_with_scores = db.papers.count_documents({
        'readability': {'$exists': True, '$ne': None, '$ne': {}}
    })
    total_papers = db.papers.count_documents({})
    logger.info(f"Total papers with readability scores: {total_with_scores}/{total_papers}")
    
    # Show distribution of difficulty levels
    difficulty_distribution = db.papers.aggregate([
        {'$match': {'readability.difficulty': {'$exists': True}}},
        {'$group': {'_id': '$readability.difficulty', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}
    ])
    
    logger.info("Difficulty distribution:")
    for item in difficulty_distribution:
        logger.info(f"  {item['_id']}: {item['count']} papers")

def recalculate_all():
    """Force recalculation of all readability scores (useful if algorithm changes)"""
    
    client = MongoClient("mongodb://localhost:27017/")
    db = client.smarttrendtracer
    
    # Clear all existing readability scores
    result = db.papers.update_many(
        {},
        {'$unset': {'readability': ""}}
    )
    logger.info(f"Cleared readability scores from {result.modified_count} papers")
    
    # Now calculate all
    calculate_and_store_readability()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--recalculate':
        logger.info("Recalculating all readability scores...")
        recalculate_all()
    else:
        logger.info("Calculating readability scores for papers without them...")
        calculate_and_store_readability()