#!/usr/bin/env python3
"""
Merge Duplicate Nathan Lambert Authors

This script merges the two Nathan Lambert author records:
- Source (to be deleted): Nathan Lambert with subdomain "interconnects" (0 articles)
- Target (to be kept): Nathan Lambert with subdomain "robotic" (20 articles)

Usage:
    python merge_nathan_lambert.py [--yes]
"""

import sys
import argparse
from pymongo import MongoClient
from bson import ObjectId

# Add parent directory to path for imports
sys.path.insert(0, '/Users/siehan/Documents/Development/Research/SmartTrendTracer/backend')

from app.services.author_service import AuthorService


def main():
    parser = argparse.ArgumentParser(description='Merge duplicate Nathan Lambert authors')
    parser.add_argument('--yes', '-y', action='store_true', help='Auto-confirm merge without prompting')
    args = parser.parse_args()
    # Connect to MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    db = client.smarttrendtracer

    # Initialize author service
    author_service = AuthorService(db)

    print("\n" + "="*70)
    print("Nathan Lambert Author Merge")
    print("="*70 + "\n")

    # Find both Nathan Lambert records
    nathan_lamberts = list(db.substack_authors.find({
        'name': {'$regex': 'Nathan Lambert', '$options': 'i'}
    }))

    if len(nathan_lamberts) != 2:
        print(f"❌ Expected 2 Nathan Lambert records, found {len(nathan_lamberts)}")
        for author in nathan_lamberts:
            print(f"   - {author.get('name')} (ID: {author['_id']}, subdomain: {author.get('subdomain')})")
        sys.exit(1)

    # Identify source and target
    source = None
    target = None

    for author in nathan_lamberts:
        subdomain = author.get('subdomain', '')
        article_count = author.get('article_count', 0)

        print(f"Found: {author.get('name')}")
        print(f"  ID: {author['_id']}")
        print(f"  Subdomain: {subdomain}")
        print(f"  Article Count: {article_count}")
        print()

        if subdomain == 'interconnects':
            source = author
        elif subdomain == 'robotic':
            target = author

    if not source or not target:
        print("❌ Could not identify source (interconnects) and target (robotic) authors")
        sys.exit(1)

    print("Merge Plan:")
    print(f"  Source (DELETE): {source['name']} - {source.get('subdomain')} ({source.get('article_count', 0)} articles)")
    print(f"  Target (KEEP):   {target['name']} - {target.get('subdomain')} ({target.get('article_count', 0)} articles)")
    print()

    # Confirm merge
    if not args.yes:
        response = input("Proceed with merge? (yes/no): ").strip().lower()
        if response != 'yes':
            print("❌ Merge cancelled")
            sys.exit(0)
    else:
        print("Auto-confirming merge (--yes flag provided)")

    print("\nPerforming merge...")

    # Execute merge
    success = author_service.merge_authors(
        source_id=source['_id'],
        target_id=target['_id']
    )

    if success:
        print("✅ Merge completed successfully!")

        # Verify merge
        remaining = db.substack_authors.find_one({'_id': target['_id']})
        deleted = db.substack_authors.find_one({'_id': source['_id']})

        if remaining and not deleted:
            print("\nVerification:")
            print(f"  ✅ Target author still exists: {remaining.get('name')}")
            print(f"  ✅ Source author deleted: {source.get('name')}")
            print(f"  ✅ Final article count: {remaining.get('article_count', 0)}")

            # Check name variations
            variations = remaining.get('name_variations', [])
            if variations:
                print(f"  ✅ Name variations: {variations}")
        else:
            print("\n⚠️  Warning: Verification failed")
            if not remaining:
                print("  ❌ Target author not found!")
            if deleted:
                print("  ❌ Source author still exists!")
    else:
        print("❌ Merge failed - check error messages above")
        sys.exit(1)

    print()


if __name__ == '__main__':
    main()
