#!/usr/bin/env python3
"""
Check and fix tag consistency across all content types

Uses MongoDB for data storage (migrated from SQLite January 2026)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from collections import defaultdict
import argparse
from app.database.mongodb import get_database

def analyze_tag_inconsistencies():
    """Analyze tag inconsistencies across the system"""
    db = get_database()

    print("\n" + "="*60)
    print("TAG CONSISTENCY ANALYSIS")
    print("="*60)

    # 1. Count concepts and instances
    concept_count = db.tag_concepts_v2.count_documents({})
    alias_count = db.tag_aliases_v2.count_documents({})
    instance_count = db.tag_instances.count_documents({})

    print(f"\nTag System Statistics:")
    print(f"  Concepts: {concept_count}")
    print(f"  Aliases:  {alias_count}")
    print(f"  Tag Instances: {instance_count}")

    # 2. Count instances by content type
    print(f"\nTag Instances by Content Type:")
    pipeline = [
        {'$group': {'_id': '$content_type', 'count': {'$sum': 1}}}
    ]
    for result in db.tag_instances.aggregate(pipeline):
        print(f"  {result['_id']}: {result['count']}")

    # 3. Find orphaned tag instances (no concept_id)
    orphan_count = db.tag_instances.count_documents({'concept_id': None})
    print(f"\nOrphaned instances (no concept): {orphan_count}")

    # Show sample orphaned tags
    if orphan_count > 0:
        orphans = list(db.tag_instances.find({'concept_id': None}).limit(10))
        print("  Sample orphaned tags:")
        for o in orphans:
            print(f"    - {o.get('tag_value', 'unknown')} ({o.get('content_type')})")

    # 4. Find concepts without instances
    concepts_with_usage = set()
    for inst in db.tag_instances.find({'concept_id': {'$ne': None}}, {'concept_id': 1}):
        concepts_with_usage.add(str(inst.get('concept_id')))

    all_concept_ids = set()
    for c in db.tag_concepts_v2.find({}, {'_id': 1}):
        all_concept_ids.add(str(c['_id']))

    unused_concepts = all_concept_ids - concepts_with_usage
    print(f"\nConcepts without any instances: {len(unused_concepts)}")

    # 5. Check for duplicate concepts by slug
    print("\nDuplicate Check (by slug):")
    pipeline = [
        {'$group': {'_id': '$slug', 'count': {'$sum': 1}, 'ids': {'$push': '$_id'}}},
        {'$match': {'count': {'$gt': 1}}}
    ]
    duplicates = list(db.tag_concepts_v2.aggregate(pipeline))
    if duplicates:
        print(f"  Found {len(duplicates)} duplicate slugs:")
        for dup in duplicates[:10]:
            print(f"    - '{dup['_id']}' appears {dup['count']} times")
    else:
        print("  No duplicate slugs found")

    # 6. Check hierarchy consistency
    print("\nHierarchy Consistency Check:")
    root_concepts = db.tag_concepts_v2.count_documents({
        '$or': [{'parents': {'$exists': False}}, {'parents': []}, {'parents': None}]
    })
    print(f"  Root concepts (no parents): {root_concepts}")

    # Check for concepts with non-existent parents
    orphaned_children = 0
    for concept in db.tag_concepts_v2.find({'parents': {'$exists': True, '$ne': []}}):
        parents = concept.get('parents', [])
        if isinstance(parents, list):
            for parent_id in parents:
                if not db.tag_concepts_v2.find_one({'_id': parent_id}):
                    orphaned_children += 1
                    break
    print(f"  Concepts with invalid parent references: {orphaned_children}")

    return {
        'concept_count': concept_count,
        'alias_count': alias_count,
        'instance_count': instance_count,
        'orphan_count': orphan_count,
        'unused_concepts': len(unused_concepts),
        'duplicate_slugs': len(duplicates)
    }

def fix_tag_consistency(dry_run: bool = True):
    """Fix tag consistency issues"""
    db = get_database()

    print("\n" + "="*60)
    print(f"TAG CONSISTENCY FIX ({'DRY RUN' if dry_run else 'APPLYING CHANGES'})")
    print("="*60)

    if dry_run:
        print("\nDRY RUN MODE - No changes will be made")
    else:
        print("\nAPPLYING FIXES - Database will be modified")

    # Fix 1: Link orphaned instances to concepts by slug matching
    orphans = list(db.tag_instances.find({'concept_id': None}))
    linked_count = 0

    for orphan in orphans:
        tag_value = orphan.get('tag_value', '')
        if not tag_value:
            continue

        # Try to find matching concept by slug
        slug = tag_value.lower().replace(' ', '-').replace('_', '-')
        concept = db.tag_concepts_v2.find_one({'slug': slug})

        if not concept:
            # Try by display_name
            concept = db.tag_concepts_v2.find_one({
                'display_name': {'$regex': f'^{tag_value}$', '$options': 'i'}
            })

        if concept:
            linked_count += 1
            if not dry_run:
                db.tag_instances.update_one(
                    {'_id': orphan['_id']},
                    {'$set': {'concept_id': concept['_id']}}
                )

    print(f"\n{'Would link' if dry_run else 'Linked'} {linked_count} orphaned instances to concepts")

    if dry_run:
        print("\nRun with --fix to apply changes")

    return True

def test_tag_filtering(test_tag: str = None):
    """Test tag filtering with the MongoDB system"""
    db = get_database()

    print("\n" + "="*60)
    print("TAG FILTERING TEST")
    print("="*60)

    if not test_tag:
        test_tag = "AI"

    print(f"\nTesting filtering with tag: '{test_tag}'")

    # Find concept by slug or display_name
    slug = test_tag.lower().replace(' ', '-')
    concept = db.tag_concepts_v2.find_one({
        '$or': [
            {'slug': slug},
            {'display_name': {'$regex': f'^{test_tag}$', '$options': 'i'}}
        ]
    })

    if concept:
        print(f"\nFound concept: '{concept.get('display_name')}'")
        print(f"  Slug: {concept.get('slug')}")
        print(f"  Entity type: {concept.get('entity_type', 'N/A')}")

        # Get parents
        parents = concept.get('parents', [])
        if parents:
            print(f"  Parents: {len(parents)}")
            for pid in parents[:5]:
                parent = db.tag_concepts_v2.find_one({'_id': pid})
                if parent:
                    print(f"    - {parent.get('display_name')}")

        # Get children
        children = list(db.tag_concepts_v2.find({'parents': concept['_id']}))
        if children:
            print(f"  Children: {len(children)}")
            for child in children[:5]:
                print(f"    - {child.get('display_name')}")

        # Get aliases
        aliases = list(db.tag_aliases_v2.find({'concept_id': concept['_id']}))
        if aliases:
            print(f"  Aliases: {[a.get('alias') for a in aliases]}")

        # Get usage stats
        instances = db.tag_instances.count_documents({'concept_id': concept['_id']})
        print(f"\nUsage Statistics:")
        print(f"  Total instances: {instances}")

        # By content type
        pipeline = [
            {'$match': {'concept_id': concept['_id']}},
            {'$group': {'_id': '$content_type', 'count': {'$sum': 1}}}
        ]
        for result in db.tag_instances.aggregate(pipeline):
            print(f"    {result['_id']}: {result['count']}")

    else:
        print(f"\nNo concept found for tag '{test_tag}'")
        print("  Try searching for a different tag")

def main():
    parser = argparse.ArgumentParser(description='Check and fix tag consistency')
    parser.add_argument('--analyze', action='store_true', help='Analyze tag inconsistencies')
    parser.add_argument('--fix', action='store_true', help='Fix tag consistency issues')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be fixed without making changes')
    parser.add_argument('--test', type=str, help='Test tag filtering with a specific tag')

    args = parser.parse_args()

    # Default to analyze if no action specified
    if not args.analyze and not args.fix and not args.test:
        args.analyze = True

    try:
        if args.analyze:
            stats = analyze_tag_inconsistencies()
            print("\n" + "="*60)
            print("SUMMARY")
            print("="*60)
            print(f"Total concepts: {stats['concept_count']}")
            print(f"Total aliases: {stats['alias_count']}")
            print(f"Total tag instances: {stats['instance_count']}")
            print(f"Orphaned instances: {stats['orphan_count']}")
            print(f"Unused concepts: {stats['unused_concepts']}")

        if args.fix or args.dry_run:
            fix_tag_consistency(dry_run=args.dry_run or not args.fix)

        if args.test:
            test_tag_filtering(args.test)

        print("\nTag consistency check complete")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
