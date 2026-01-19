#!/usr/bin/env python3
"""
Inspect paper document structure to understand how tags/concepts are stored
"""

from pymongo import MongoClient
from bson import ObjectId
import json

def connect_mongodb():
    """Connect to MongoDB"""
    client = MongoClient('mongodb://localhost:27017/')
    db = client.smarttrendtracer
    return db

def inspect_papers(db):
    """Inspect paper document structure"""
    
    print("=" * 80)
    print("PAPER DOCUMENT STRUCTURE INSPECTION")
    print("=" * 80)
    
    papers_col = db.papers
    
    # Get a sample paper
    sample_paper = papers_col.find_one()
    
    if sample_paper:
        print("\n1. SAMPLE PAPER STRUCTURE")
        print("-" * 40)
        
        # Show all fields
        for field in sample_paper.keys():
            value = sample_paper[field]
            if field == '_id':
                print(f"  {field}: ObjectId(...)")
            elif isinstance(value, str) and len(value) > 100:
                print(f"  {field}: (string, {len(value)} chars)")
            elif isinstance(value, list):
                print(f"  {field}: (list, {len(value)} items)")
                if value and len(value) > 0:
                    # Show first item structure
                    first_item = value[0]
                    if isinstance(first_item, dict):
                        print(f"    First item keys: {list(first_item.keys())}")
            elif isinstance(value, dict):
                print(f"  {field}: (dict, keys: {list(value.keys())[:5]}...)")
            else:
                print(f"  {field}: {value}")
    
    # Check all papers for any tag-related fields
    print("\n2. TAG-RELATED FIELDS ACROSS ALL PAPERS")
    print("-" * 40)
    
    tag_fields = {}
    concept_fields = {}
    
    for paper in papers_col.find():
        for field in paper.keys():
            if 'tag' in field.lower():
                if field not in tag_fields:
                    tag_fields[field] = 0
                tag_fields[field] += 1
            if 'concept' in field.lower():
                if field not in concept_fields:
                    concept_fields[field] = 0
                concept_fields[field] += 1
    
    print("Tag-related fields found:")
    for field, count in tag_fields.items():
        print(f"  {field}: appears in {count} papers")
    
    print("\nConcept-related fields found:")
    for field, count in concept_fields.items():
        print(f"  {field}: appears in {count} papers")
    
    # Check tag_instances for paper entries
    print("\n3. TAG_INSTANCES FOR PAPERS")
    print("-" * 40)
    
    instances_col = db.tag_instances
    
    # Get sample paper instances
    paper_instances = list(instances_col.find({"content_type": "paper"}).limit(5))
    
    print(f"Found {instances_col.count_documents({'content_type': 'paper'})} paper tag instances")
    
    if paper_instances:
        print("\nSample paper tag instance:")
        sample = paper_instances[0]
        for key, value in sample.items():
            if key == '_id':
                print(f"  {key}: ObjectId(...)")
            elif key == 'concept_id' and value:
                print(f"  {key}: ObjectId(...)")
            else:
                print(f"  {key}: {value}")
        
        # Get the tags for a specific paper
        if paper_instances:
            content_id = paper_instances[0]['content_id']
            paper_tags = list(instances_col.find({"content_type": "paper", "content_id": content_id}))
            
            print(f"\nTags for paper {content_id}:")
            for tag_instance in paper_tags[:5]:
                print(f"  - {tag_instance.get('tag')} (concept_id: {tag_instance.get('concept_id')})")
    
    # Find papers that have tag instances
    print("\n4. PAPERS WITH TAG INSTANCES")
    print("-" * 40)
    
    papers_with_tags = instances_col.distinct("content_id", {"content_type": "paper"})
    print(f"Papers with tag instances: {len(papers_with_tags)}")
    
    # Check if these paper IDs exist in papers collection
    existing_papers = set()
    for paper in papers_col.find({}, {"_id": 1}):
        existing_papers.add(str(paper['_id']))
    
    orphaned_instances = []
    for paper_id in papers_with_tags:
        if str(paper_id) not in existing_papers:
            orphaned_instances.append(paper_id)
    
    if orphaned_instances:
        print(f"\nOrphaned tag instances (paper doesn't exist): {len(orphaned_instances)}")
        for orphan_id in orphaned_instances[:5]:
            instance_count = instances_col.count_documents({"content_type": "paper", "content_id": orphan_id})
            print(f"  Paper ID {orphan_id}: {instance_count} tag instances")

if __name__ == "__main__":
    db = connect_mongodb()
    inspect_papers(db)