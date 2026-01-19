#!/usr/bin/env python3
"""
Fix paper tag integrity issues:
1. Update tag_instances content_id from SQLite IDs to MongoDB ObjectIds
2. Populate paper.concept_ids from tag_instances
3. Ensure bi-directional consistency
"""

from pymongo import MongoClient
from bson import ObjectId
from collections import defaultdict
from datetime import datetime
import json

def connect_mongodb():
    """Connect to MongoDB"""
    client = MongoClient('mongodb://localhost:27017/')
    db = client.smarttrendtracer
    return db

def fix_tag_integrity(db, dry_run=True):
    """Fix tag integrity issues"""
    
    print("=" * 80)
    print("PAPER TAG INTEGRITY FIX")
    print(f"Mode: {'DRY RUN' if dry_run else 'ACTUAL FIX'}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)
    
    papers_col = db.papers
    concepts_col = db.tag_concepts_v2
    instances_col = db.tag_instances
    
    stats = {
        'instances_updated': 0,
        'papers_updated': 0,
        'errors': []
    }
    
    # 1. Build SQLite ID to MongoDB ID mapping
    print("\n1. BUILDING ID MAPPING")
    print("-" * 40)
    
    sqlite_to_mongo = {}
    mongo_to_sqlite = {}
    
    for paper in papers_col.find():
        mongo_id = paper['_id']
        sqlite_id = paper.get('old_sqlite_id')
        
        if sqlite_id:
            sqlite_to_mongo[sqlite_id] = mongo_id
            mongo_to_sqlite[str(mongo_id)] = sqlite_id
    
    print(f"Mapped {len(sqlite_to_mongo)} papers with SQLite IDs")
    
    # 2. Fix tag_instances content_id field
    print("\n2. FIXING TAG_INSTANCES CONTENT_ID")
    print("-" * 40)
    
    paper_instances = list(instances_col.find({"content_type": "paper"}))
    print(f"Processing {len(paper_instances)} paper tag instances...")
    
    for instance in paper_instances:
        content_id = instance.get('content_id')
        needs_update = False
        new_content_id = None
        
        # Check if it's a numeric string (SQLite ID)
        if isinstance(content_id, str) and content_id.isdigit():
            sqlite_id = int(content_id)
            mongo_id = sqlite_to_mongo.get(sqlite_id)
            
            if mongo_id:
                new_content_id = str(mongo_id)
                needs_update = True
        elif isinstance(content_id, int):
            sqlite_id = content_id
            mongo_id = sqlite_to_mongo.get(sqlite_id)
            
            if mongo_id:
                new_content_id = str(mongo_id)
                needs_update = True
        
        if needs_update and new_content_id:
            if not dry_run:
                instances_col.update_one(
                    {"_id": instance['_id']},
                    {"$set": {"content_id": new_content_id}}
                )
            stats['instances_updated'] += 1
    
    print(f"Updated {stats['instances_updated']} tag instances")
    
    # 3. Populate paper.concept_ids from tag_instances
    print("\n3. POPULATING PAPER CONCEPT_IDS")
    print("-" * 40)
    
    # Group tag instances by paper
    paper_concepts = defaultdict(set)
    
    for instance in instances_col.find({"content_type": "paper"}):
        content_id = instance.get('content_id')
        concept_id = instance.get('concept_id')
        
        if content_id and concept_id:
            # Handle both old and new content_id formats
            if isinstance(content_id, str):
                if content_id.isdigit():
                    # Old SQLite ID
                    sqlite_id = int(content_id)
                    mongo_id = sqlite_to_mongo.get(sqlite_id)
                    if mongo_id:
                        paper_concepts[str(mongo_id)].add(concept_id)
                else:
                    # MongoDB ID string
                    paper_concepts[content_id].add(concept_id)
    
    print(f"Found concepts for {len(paper_concepts)} papers")
    
    # Update papers with their concept_ids
    for paper_id_str, concept_ids in paper_concepts.items():
        try:
            paper_id = ObjectId(paper_id_str)
            concept_list = list(concept_ids)
            
            if not dry_run:
                papers_col.update_one(
                    {"_id": paper_id},
                    {"$set": {"concept_ids": concept_list}}
                )
            stats['papers_updated'] += 1
            
        except Exception as e:
            stats['errors'].append(f"Error updating paper {paper_id_str}: {str(e)}")
    
    print(f"Updated {stats['papers_updated']} papers with concept_ids")
    
    # 4. Verify the fix
    print("\n4. VERIFICATION")
    print("-" * 40)
    
    if not dry_run:
        # Count papers with populated concept_ids
        papers_with_concepts = papers_col.count_documents({
            "concept_ids": {"$exists": True, "$ne": [], "$ne": None}
        })
        
        # Count valid tag instances
        valid_instances = 0
        for instance in instances_col.find({"content_type": "paper"}):
            content_id = instance.get('content_id')
            try:
                paper = papers_col.find_one({"_id": ObjectId(content_id)})
                if paper:
                    valid_instances += 1
            except:
                pass
        
        print(f"Papers with concept_ids: {papers_with_concepts}")
        print(f"Valid tag instances: {valid_instances}")
    else:
        print("Dry run - no actual changes made")
    
    # 5. Show sample of specific concepts
    print("\n5. SPECIFIC CONCEPTS STATUS")
    print("-" * 40)
    
    specific_concepts = [
        "log_point_changes",
        "onet_task_data", 
        "wage_stickiness",
        "claude",
        "pce_price_index",
        "poisson_event_study_regression",
        "real_annual_base_compensation",
        "labor_economics"
    ]
    
    for concept_slug in specific_concepts:
        concept = concepts_col.find_one({"slug": concept_slug})
        if concept:
            concept_id = concept['_id']
            instance_count = instances_col.count_documents({
                "concept_id": concept_id,
                "content_type": "paper"
            })
            print(f"  {concept_slug}: {instance_count} paper instances")
    
    # Save report
    report = {
        'timestamp': datetime.now().isoformat(),
        'dry_run': dry_run,
        'stats': stats,
        'papers_with_mapping': len(sqlite_to_mongo),
        'paper_concepts_found': len(paper_concepts)
    }
    
    report_file = 'tag_integrity_fix_report.json'
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print("\n" + "=" * 80)
    print("FIX COMPLETE" if not dry_run else "DRY RUN COMPLETE")
    print(f"Report saved to: {report_file}")
    print("=" * 80)
    
    return stats

if __name__ == "__main__":
    import sys
    
    db = connect_mongodb()
    
    # Check for --fix flag to actually apply changes
    dry_run = '--fix' not in sys.argv
    
    if dry_run:
        print("\nRunning in DRY RUN mode (no changes will be made)")
        print("To apply fixes, run: python fix_paper_tag_integrity.py --fix\n")
    else:
        response = input("\n⚠️  This will modify the database. Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            sys.exit(0)
    
    fix_tag_integrity(db, dry_run=dry_run)