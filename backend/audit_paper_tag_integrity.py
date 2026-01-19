#!/usr/bin/env python3
"""
MongoDB Paper Tag Integrity Audit
Verifies integrity between paper tags and the concept system
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

def audit_paper_tags(db):
    """Audit paper tags and concept integrity"""
    
    print("=" * 80)
    print("MONGODB PAPER TAG INTEGRITY AUDIT")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)
    
    # Collections
    papers_col = db.papers
    concepts_col = db.tag_concepts_v2
    instances_col = db.tag_instances
    
    # 1. Get all unique tags from papers
    print("\n1. ANALYZING PAPERS COLLECTION")
    print("-" * 40)
    
    paper_tags = defaultdict(list)  # tag -> list of paper IDs
    all_paper_tags = set()
    paper_count = 0
    
    for paper in papers_col.find():
        paper_count += 1
        paper_id = str(paper['_id'])
        
        # Check different possible tag fields
        tags = []
        if 'tags' in paper:
            if isinstance(paper['tags'], list):
                tags.extend(paper['tags'])
        if 'concepts' in paper:
            if isinstance(paper['concepts'], list):
                tags.extend(paper['concepts'])
        
        for tag in tags:
            # Handle both string and dict formats
            if isinstance(tag, dict):
                tag_value = tag.get('tag') or tag.get('slug') or tag.get('concept')
            else:
                tag_value = str(tag)
            
            if tag_value:
                all_paper_tags.add(tag_value)
                paper_tags[tag_value].append(paper_id)
    
    print(f"Total papers analyzed: {paper_count}")
    print(f"Unique tags found in papers: {len(all_paper_tags)}")
    
    # 2. Get all concepts from tag_concepts_v2
    print("\n2. ANALYZING TAG_CONCEPTS_V2 COLLECTION")
    print("-" * 40)
    
    existing_concepts = {}  # slug -> concept document
    concept_by_tag = {}  # tag -> concept document
    
    for concept in concepts_col.find():
        slug = concept.get('slug', '')
        tag = concept.get('tag', '')
        
        if slug:
            existing_concepts[slug] = concept
        if tag:
            concept_by_tag[tag] = concept
    
    print(f"Total concepts in tag_concepts_v2: {len(existing_concepts)}")
    
    # 3. Find orphaned tags (tags in papers but not in concepts)
    print("\n3. ORPHANED TAGS ANALYSIS")
    print("-" * 40)
    
    orphaned_tags = []
    for tag in all_paper_tags:
        # Check both slug and tag fields
        if tag not in existing_concepts and tag not in concept_by_tag:
            orphaned_tags.append({
                'tag': tag,
                'paper_count': len(paper_tags[tag]),
                'paper_ids': paper_tags[tag][:3]  # First 3 paper IDs as examples
            })
    
    orphaned_tags.sort(key=lambda x: x['paper_count'], reverse=True)
    
    print(f"Orphaned tags found: {len(orphaned_tags)}")
    if orphaned_tags:
        print("\nTop orphaned tags (not in tag_concepts_v2):")
        for i, orphan in enumerate(orphaned_tags[:10], 1):
            print(f"  {i}. '{orphan['tag']}' - used in {orphan['paper_count']} paper(s)")
    
    # 4. Check specific missing concepts
    print("\n4. CHECKING SPECIFIC CONCEPTS")
    print("-" * 40)
    
    specific_concepts = [
        "Log Point Changes",
        "Onet Task Data",
        "O*NET Task Data",
        "Wage Stickiness",
        "Claude",
        "Pce Price Index",
        "PCE Price Index",
        "Poisson Event Study Regression",
        "Real Annual Base Compensation",
        "Labor Economics"
    ]
    
    for concept_name in specific_concepts:
        # Check various forms
        slug_form = concept_name.lower().replace(" ", "-").replace("*", "")
        
        found_in_concepts = (
            concept_name in existing_concepts or 
            concept_name in concept_by_tag or
            slug_form in existing_concepts or
            slug_form in concept_by_tag
        )
        
        found_in_papers = concept_name in all_paper_tags or slug_form in all_paper_tags
        
        status = "✓ EXISTS" if found_in_concepts else "✗ MISSING"
        paper_usage = f"Used in {len(paper_tags.get(concept_name, []))} papers" if found_in_papers else "Not used in papers"
        
        print(f"  {status} - '{concept_name}' - {paper_usage}")
    
    # 5. Analyze tag_instances collection
    print("\n5. TAG_INSTANCES ANALYSIS")
    print("-" * 40)
    
    # Count instances by content type
    instance_stats = instances_col.aggregate([
        {"$group": {
            "_id": "$content_type",
            "count": {"$sum": 1},
            "with_concept": {"$sum": {"$cond": [{"$ne": ["$concept_id", None]}, 1, 0]}},
            "orphaned": {"$sum": {"$cond": [{"$eq": ["$concept_id", None]}, 1, 0]}}
        }}
    ])
    
    total_instances = 0
    total_orphaned = 0
    
    for stat in instance_stats:
        content_type = stat['_id'] or 'unknown'
        total_instances += stat['count']
        total_orphaned += stat['orphaned']
        
        print(f"  {content_type}: {stat['count']} total, {stat['with_concept']} linked, {stat['orphaned']} orphaned")
    
    print(f"\nTotal tag_instances: {total_instances}")
    print(f"Orphaned instances (no concept_id): {total_orphaned}")
    
    # 6. Check paper-specific instances
    print("\n6. PAPER TAG_INSTANCES VERIFICATION")
    print("-" * 40)
    
    paper_instances = list(instances_col.find({"content_type": "paper"}))
    print(f"Paper tag instances: {len(paper_instances)}")
    
    # Verify that paper instances match actual paper tags
    paper_instance_tags = defaultdict(set)
    for instance in paper_instances:
        content_id = instance.get('content_id')
        tag = instance.get('tag')
        if content_id and tag:
            paper_instance_tags[str(content_id)].add(tag)
    
    # Compare with actual paper tags
    mismatched_papers = 0
    for paper in papers_col.find():
        paper_id = str(paper['_id'])
        
        # Get actual tags from paper
        actual_tags = set()
        if 'tags' in paper and isinstance(paper['tags'], list):
            for tag in paper['tags']:
                if isinstance(tag, dict):
                    tag_value = tag.get('tag') or tag.get('slug') or tag.get('concept')
                else:
                    tag_value = str(tag)
                if tag_value:
                    actual_tags.add(tag_value)
        
        # Get instance tags
        instance_tags = paper_instance_tags.get(paper_id, set())
        
        # Check for mismatches
        if actual_tags != instance_tags:
            mismatched_papers += 1
            if mismatched_papers <= 3:  # Show first 3 examples
                print(f"\n  Mismatch for paper {paper_id}:")
                print(f"    Tags in paper doc: {list(actual_tags)[:5]}")
                print(f"    Tags in instances: {list(instance_tags)[:5]}")
    
    if mismatched_papers > 0:
        print(f"\nTotal papers with tag mismatches: {mismatched_papers}")
    
    # 7. Generate recommendations
    print("\n7. RECOMMENDATIONS")
    print("-" * 40)
    
    recommendations = []
    
    if orphaned_tags:
        recommendations.append({
            'issue': 'Orphaned tags in papers',
            'count': len(orphaned_tags),
            'action': 'Create concept entries for orphaned tags or update paper tags',
            'priority': 'HIGH'
        })
    
    if total_orphaned > 0:
        recommendations.append({
            'issue': 'Orphaned tag instances',
            'count': total_orphaned,
            'action': 'Link orphaned instances to concepts or remove them',
            'priority': 'MEDIUM'
        })
    
    if mismatched_papers > 0:
        recommendations.append({
            'issue': 'Tag instance mismatches',
            'count': mismatched_papers,
            'action': 'Synchronize tag_instances with paper documents',
            'priority': 'MEDIUM'
        })
    
    for rec in recommendations:
        print(f"\n  [{rec['priority']}] {rec['issue']}")
        print(f"    Count: {rec['count']}")
        print(f"    Action: {rec['action']}")
    
    # 8. Export detailed report
    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_papers': paper_count,
            'unique_tags_in_papers': len(all_paper_tags),
            'total_concepts': len(existing_concepts),
            'orphaned_tags': len(orphaned_tags),
            'total_tag_instances': total_instances,
            'orphaned_instances': total_orphaned,
            'papers_with_mismatches': mismatched_papers
        },
        'orphaned_tags': orphaned_tags[:20],  # Top 20 orphaned tags
        'recommendations': recommendations
    }
    
    with open('paper_tag_integrity_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print("\n" + "=" * 80)
    print("AUDIT COMPLETE")
    print(f"Detailed report saved to: paper_tag_integrity_report.json")
    print("=" * 80)
    
    return report

if __name__ == "__main__":
    db = connect_mongodb()
    report = audit_paper_tags(db)