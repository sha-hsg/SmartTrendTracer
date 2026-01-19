#!/usr/bin/env python3
"""
Analyze tag linkage issues between papers and concepts
"""

from pymongo import MongoClient
from bson import ObjectId
from collections import defaultdict
import json

def connect_mongodb():
    """Connect to MongoDB"""
    client = MongoClient('mongodb://localhost:27017/')
    db = client.smarttrendtracer
    return db

def analyze_linkage_issues(db):
    """Analyze linkage issues between papers and concepts"""
    
    print("=" * 80)
    print("TAG LINKAGE ANALYSIS")
    print("=" * 80)
    
    papers_col = db.papers
    concepts_col = db.tag_concepts_v2
    instances_col = db.tag_instances
    
    # 1. Check the content_id format in tag_instances
    print("\n1. TAG_INSTANCES CONTENT_ID ANALYSIS")
    print("-" * 40)
    
    paper_instances = list(instances_col.find({"content_type": "paper"}))
    
    id_types = defaultdict(int)
    for instance in paper_instances:
        content_id = instance.get('content_id')
        if isinstance(content_id, ObjectId):
            id_types['ObjectId'] += 1
        elif isinstance(content_id, str):
            try:
                # Check if it's a valid ObjectId string
                ObjectId(content_id)
                id_types['ObjectId_string'] += 1
            except:
                id_types['numeric_string'] += 1
        elif isinstance(content_id, int):
            id_types['integer'] += 1
        else:
            id_types['other'] += 1
    
    print("Content ID types in tag_instances:")
    for id_type, count in id_types.items():
        print(f"  {id_type}: {count}")
    
    # 2. Map old SQLite IDs to MongoDB IDs
    print("\n2. PAPER ID MAPPING")
    print("-" * 40)
    
    sqlite_to_mongo = {}
    mongo_to_sqlite = {}
    
    for paper in papers_col.find():
        mongo_id = str(paper['_id'])
        sqlite_id = paper.get('old_sqlite_id')
        
        if sqlite_id:
            sqlite_to_mongo[sqlite_id] = mongo_id
            mongo_to_sqlite[mongo_id] = sqlite_id
    
    print(f"Papers with old_sqlite_id mapping: {len(sqlite_to_mongo)}")
    
    # 3. Check if tag_instances use old SQLite IDs
    print("\n3. CHECKING TAG_INSTANCES LINKAGE")
    print("-" * 40)
    
    matched_instances = 0
    unmatched_instances = 0
    instance_tags_by_paper = defaultdict(list)
    
    for instance in paper_instances:
        content_id = instance.get('content_id')
        
        # Try to find the paper
        paper_mongo_id = None
        
        if isinstance(content_id, int) or (isinstance(content_id, str) and content_id.isdigit()):
            # It's likely an old SQLite ID
            sqlite_id = int(content_id)
            paper_mongo_id = sqlite_to_mongo.get(sqlite_id)
        elif isinstance(content_id, (ObjectId, str)):
            # Try as MongoDB ID
            try:
                paper_mongo_id = str(content_id)
            except:
                pass
        
        if paper_mongo_id:
            matched_instances += 1
            # Get the tag name from concept
            concept_id = instance.get('concept_id')
            if concept_id:
                concept = concepts_col.find_one({"_id": concept_id})
                if concept:
                    tag_name = concept.get('slug') or concept.get('tag')
                    instance_tags_by_paper[paper_mongo_id].append(tag_name)
        else:
            unmatched_instances += 1
    
    print(f"Matched instances (can link to paper): {matched_instances}")
    print(f"Unmatched instances (orphaned): {unmatched_instances}")
    print(f"Papers with tags via instances: {len(instance_tags_by_paper)}")
    
    # 4. Check specific concepts mentioned
    print("\n4. SEARCHING FOR SPECIFIC CONCEPTS")
    print("-" * 40)
    
    specific_searches = [
        "log-point-changes",
        "onet-task-data",
        "wage-stickiness",
        "claude",
        "pce-price-index",
        "poisson-event-study-regression",
        "real-annual-base-compensation",
        "labor-economics"
    ]
    
    for search_term in specific_searches:
        # Search in concepts
        concept = concepts_col.find_one({
            "$or": [
                {"slug": search_term},
                {"tag": search_term},
                {"slug": {"$regex": search_term, "$options": "i"}},
                {"tag": {"$regex": search_term, "$options": "i"}},
                {"display_name": {"$regex": search_term.replace("-", " "), "$options": "i"}}
            ]
        })
        
        if concept:
            concept_id = concept['_id']
            # Count instances using this concept
            instance_count = instances_col.count_documents({"concept_id": concept_id})
            paper_count = instances_col.count_documents({"concept_id": concept_id, "content_type": "paper"})
            
            print(f"  ✓ FOUND: '{search_term}'")
            print(f"    Concept: {concept.get('slug')} (display: {concept.get('display_name')})")
            print(f"    Total instances: {instance_count}, Paper instances: {paper_count}")
        else:
            print(f"  ✗ NOT FOUND: '{search_term}'")
    
    # 5. Show sample papers with their tags
    print("\n5. SAMPLE PAPERS WITH TAGS (via tag_instances)")
    print("-" * 40)
    
    sample_count = 0
    for paper_mongo_id, tags in instance_tags_by_paper.items():
        if sample_count >= 3:
            break
        
        paper = papers_col.find_one({"_id": ObjectId(paper_mongo_id)})
        if paper:
            print(f"\nPaper: {paper.get('title', 'Untitled')[:60]}...")
            print(f"  MongoDB ID: {paper_mongo_id}")
            print(f"  Old SQLite ID: {paper.get('old_sqlite_id')}")
            print(f"  Tags ({len(tags)}): {', '.join(tags[:10])}")
            sample_count += 1
    
    # 6. Generate fix recommendations
    print("\n6. RECOMMENDED FIXES")
    print("-" * 40)
    
    fixes = []
    
    if unmatched_instances > 0:
        fixes.append({
            'issue': 'Tag instances with invalid content_id',
            'count': unmatched_instances,
            'fix': 'Update content_id to use MongoDB ObjectId instead of SQLite ID'
        })
    
    papers_without_concepts = papers_col.count_documents({"$or": [
        {"concept_ids": {"$exists": False}},
        {"concept_ids": []},
        {"concept_ids": None}
    ]})
    
    if papers_without_concepts > 0:
        fixes.append({
            'issue': 'Papers with empty concept_ids field',
            'count': papers_without_concepts,
            'fix': 'Populate concept_ids from tag_instances collection'
        })
    
    missing_concepts = [s for s in specific_searches if not concepts_col.find_one({"$or": [
        {"slug": s}, {"tag": s}, {"display_name": {"$regex": s.replace("-", " "), "$options": "i"}}
    ]})]
    
    if missing_concepts:
        fixes.append({
            'issue': 'Missing concept definitions',
            'concepts': missing_concepts,
            'fix': 'Create concept entries in tag_concepts_v2'
        })
    
    for fix in fixes:
        print(f"\n  Issue: {fix['issue']}")
        if 'count' in fix:
            print(f"  Count: {fix['count']}")
        if 'concepts' in fix:
            print(f"  Missing: {', '.join(fix['concepts'])}")
        print(f"  Fix: {fix['fix']}")
    
    # Generate detailed report
    report = {
        'content_id_types': dict(id_types),
        'papers_with_mapping': len(sqlite_to_mongo),
        'matched_instances': matched_instances,
        'unmatched_instances': unmatched_instances,
        'papers_with_tags': len(instance_tags_by_paper),
        'fixes_needed': fixes
    }
    
    with open('tag_linkage_analysis.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print(f"Detailed report saved to: tag_linkage_analysis.json")
    print("=" * 80)

if __name__ == "__main__":
    db = connect_mongodb()
    analyze_linkage_issues(db)