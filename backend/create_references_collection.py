#!/usr/bin/env python3
"""
Create a normalized references collection for SmartTrendTracer
This script creates a centralized references collection and migrates embedded references
"""

import logging
from pymongo import MongoClient, ASCENDING, TEXT
from bson import ObjectId
from datetime import datetime
from typing import Dict, List, Optional
import hashlib
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client.smarttrendtracer

def normalize_title(title: str) -> str:
    """Normalize title for deduplication"""
    if not title:
        return ""
    # Remove punctuation, lowercase, remove extra spaces
    normalized = re.sub(r'[^\w\s]', '', title.lower())
    normalized = ' '.join(normalized.split())
    return normalized

def generate_reference_hash(ref: Dict) -> str:
    """Generate a unique hash for reference deduplication"""
    # Use DOI if available (most reliable)
    if ref.get('doi') and ref['doi'].strip():
        return f"doi:{ref['doi'].strip().lower()}"
    
    # Use ArXiv ID if available
    if ref.get('arxiv_id') and ref['arxiv_id'].strip():
        return f"arxiv:{ref['arxiv_id'].strip().lower()}"
    
    # Fallback to title + year combination
    title = normalize_title(ref.get('title', ''))
    year = str(ref.get('year', '')).strip()
    
    if title:
        if year:
            return f"title:{hashlib.md5(f'{title}:{year}'.encode()).hexdigest()}"
        else:
            return f"title:{hashlib.md5(title.encode()).hexdigest()}"
    
    # Last resort: hash the entire reference
    ref_str = str(sorted(ref.items()))
    return f"raw:{hashlib.md5(ref_str.encode()).hexdigest()}"

def create_references_collection():
    """Create the normalized references collection with indexes"""
    logger.info("Creating references collection...")
    
    # Drop existing collection if it exists (for clean migration)
    if 'references' in db.list_collection_names():
        logger.warning("Dropping existing references collection...")
        db.references.drop()
    
    # Create collection
    db.create_collection('references')
    
    # Create indexes for efficient queries
    db.references.create_index([('reference_hash', ASCENDING)], unique=True)
    db.references.create_index([('doi', ASCENDING)], sparse=True)
    db.references.create_index([('arxiv_id', ASCENDING)], sparse=True)
    db.references.create_index([('title', TEXT)])
    db.references.create_index([('normalized_title', ASCENDING)])
    db.references.create_index([('year', ASCENDING)])
    db.references.create_index([('cited_by', ASCENDING)])
    db.references.create_index([('is_in_system', ASCENDING)])
    
    logger.info("References collection created with indexes")

def migrate_references():
    """Migrate embedded references to normalized collection"""
    logger.info("Starting reference migration...")
    
    # Track statistics
    stats = {
        'total_papers': 0,
        'total_references': 0,
        'unique_references': 0,
        'duplicates_found': 0,
        'papers_updated': 0
    }
    
    # Process each paper with references
    papers = db.papers.find({'references': {'$exists': True, '$ne': []}})
    
    for paper in papers:
        stats['total_papers'] += 1
        paper_id = paper['_id']
        paper_title = paper.get('title', 'Unknown')
        
        logger.info(f"Processing paper: {paper_title[:50]}...")
        
        # Track reference IDs for this paper
        paper_reference_ids = []
        
        for ref in paper.get('references', []):
            stats['total_references'] += 1
            
            # Generate reference hash for deduplication
            ref_hash = generate_reference_hash(ref)
            
            # Check if reference already exists
            existing_ref = db.references.find_one({'reference_hash': ref_hash})
            
            if existing_ref:
                # Reference exists - just add this paper as a citer
                stats['duplicates_found'] += 1
                ref_id = existing_ref['_id']
                
                # Add paper to cited_by list if not already there
                if paper_id not in existing_ref.get('cited_by', []):
                    db.references.update_one(
                        {'_id': ref_id},
                        {
                            '$addToSet': {'cited_by': paper_id},
                            '$inc': {'citation_count': 1}
                        }
                    )
            else:
                # New reference - create it
                stats['unique_references'] += 1
                
                # Normalize authors field
                authors = ref.get('authors', [])
                if isinstance(authors, str):
                    # Split string authors into array
                    authors = [a.strip() for a in authors.split(',') if a.strip()]
                
                # Create reference document
                reference_doc = {
                    'reference_hash': ref_hash,
                    'title': ref.get('title', ''),
                    'normalized_title': normalize_title(ref.get('title', '')),
                    'authors': authors,
                    'year': ref.get('year'),
                    'venue': ref.get('venue', ''),
                    'doi': ref.get('doi', ''),
                    'arxiv_id': ref.get('arxiv_id', ''),
                    'pages': ref.get('pages', ''),
                    'url': ref.get('url', ''),
                    'bibtex': ref.get('bibtex', ''),
                    'raw_citation': ref.get('raw_citation', ''),
                    'cited_by': [paper_id],
                    'citation_count': 1,
                    'is_in_system': False,  # Will be updated if paper exists
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow(),
                    'source': 'migration',
                    'grobid_id': ref.get('id', ''),  # Preserve GROBID reference ID
                    'old_sqlite_id': ref.get('old_sqlite_id')  # Preserve old ID if exists
                }
                
                # Insert reference
                result = db.references.insert_one(reference_doc)
                ref_id = result.inserted_id
            
            paper_reference_ids.append(ref_id)
        
        # Update paper with reference IDs (keep embedded for backward compatibility)
        db.papers.update_one(
            {'_id': paper_id},
            {
                '$set': {
                    'reference_ids': paper_reference_ids,
                    'references_migrated': True,
                    'migration_date': datetime.utcnow()
                }
            }
        )
        stats['papers_updated'] += 1
    
    logger.info("\n=== Migration Statistics ===")
    logger.info(f"Total papers processed: {stats['total_papers']}")
    logger.info(f"Total references found: {stats['total_references']}")
    logger.info(f"Unique references created: {stats['unique_references']}")
    logger.info(f"Duplicate references merged: {stats['duplicates_found']}")
    logger.info(f"Papers updated: {stats['papers_updated']}")
    
    return stats

def check_existing_papers():
    """Check which references already exist as papers in the system"""
    logger.info("\nChecking which references are already in the system...")
    
    updated = 0
    
    # Get all references
    references = db.references.find({})
    
    for ref in references:
        # Try to find matching paper by DOI
        if ref.get('doi'):
            paper = db.papers.find_one({'doi': ref['doi']})
            if paper:
                db.references.update_one(
                    {'_id': ref['_id']},
                    {
                        '$set': {
                            'is_in_system': True,
                            'paper_id': paper['_id']
                        }
                    }
                )
                updated += 1
                continue
        
        # Try to find by ArXiv ID
        if ref.get('arxiv_id'):
            paper = db.papers.find_one({'arxiv_id': ref['arxiv_id']})
            if paper:
                db.references.update_one(
                    {'_id': ref['_id']},
                    {
                        '$set': {
                            'is_in_system': True,
                            'paper_id': paper['_id']
                        }
                    }
                )
                updated += 1
                continue
        
        # Try to find by normalized title and year
        if ref.get('normalized_title') and ref.get('year'):
            # Use exact match for long titles to avoid regex errors
            title = ref.get('title', '')
            if len(title) > 100:
                # For long titles, use normalized comparison
                paper = db.papers.find_one({
                    'year': ref['year']
                })
                # Check title similarity manually
                if paper and paper.get('title'):
                    if normalize_title(paper['title']) == ref['normalized_title']:
                        paper_match = paper
                    else:
                        paper_match = None
                else:
                    paper_match = None
            else:
                # For short titles, use regex
                paper_match = db.papers.find_one({
                    'title': {'$regex': re.escape(title), '$options': 'i'},
                    'year': ref['year']
                })
            
            if paper_match:
                db.references.update_one(
                    {'_id': ref['_id']},
                    {
                        '$set': {
                            'is_in_system': True,
                            'paper_id': paper['_id']
                        }
                    }
                )
                updated += 1
    
    logger.info(f"Found {updated} references that already exist as papers in the system")
    return updated

def create_paper_citations_collection():
    """Create a collection for tracking paper-to-paper citations"""
    logger.info("\nCreating paper_citations collection...")
    
    if 'paper_citations' in db.list_collection_names():
        db.paper_citations.drop()
    
    db.create_collection('paper_citations')
    
    # Create indexes
    db.paper_citations.create_index([('citing_paper', ASCENDING)])
    db.paper_citations.create_index([('cited_paper', ASCENDING)])
    db.paper_citations.create_index([('citing_paper', ASCENDING), ('cited_paper', ASCENDING)], unique=True)
    
    # Populate with known citations
    citations_created = 0
    references = db.references.find({'is_in_system': True})
    
    for ref in references:
        for citing_paper_id in ref.get('cited_by', []):
            try:
                db.paper_citations.insert_one({
                    'citing_paper': citing_paper_id,
                    'cited_paper': ref['paper_id'],
                    'reference_id': ref['_id'],
                    'created_at': datetime.utcnow()
                })
                citations_created += 1
            except:
                pass  # Ignore duplicates
    
    logger.info(f"Created {citations_created} paper-to-paper citation links")
    return citations_created

def main():
    """Run the migration"""
    logger.info("Starting reference architecture migration...")
    
    # Step 1: Create references collection
    create_references_collection()
    
    # Step 2: Migrate references
    stats = migrate_references()
    
    # Step 3: Check which references are already papers
    in_system = check_existing_papers()
    
    # Step 4: Create paper citations tracking
    citations = create_paper_citations_collection()
    
    # Final report
    logger.info("\n" + "="*50)
    logger.info("MIGRATION COMPLETE!")
    logger.info("="*50)
    logger.info(f"✅ Created normalized references collection")
    logger.info(f"✅ Migrated {stats['unique_references']} unique references")
    logger.info(f"✅ Merged {stats['duplicates_found']} duplicates")
    logger.info(f"✅ Found {in_system} references already in system as papers")
    logger.info(f"✅ Created {citations} paper-to-paper citation links")
    
    # Show sample queries
    logger.info("\n" + "="*50)
    logger.info("SAMPLE QUERIES YOU CAN NOW RUN:")
    logger.info("="*50)
    print("""
    # Find all papers citing "Attention is all you need"
    db.references.findOne({title: /attention is all you need/i})
    
    # Get all unique references in the system
    db.references.count()
    
    # Find most cited references
    db.references.find().sort({citation_count: -1}).limit(10)
    
    # Find references that can be imported as papers
    db.references.find({is_in_system: false, doi: {$ne: ""}})
    
    # Get citation network for a paper
    db.paper_citations.find({citing_paper: ObjectId("...")})
    """)

if __name__ == "__main__":
    main()