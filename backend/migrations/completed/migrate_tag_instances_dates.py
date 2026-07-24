#!/usr/bin/env python3
"""
One-off migration: Convert all string `created_at` in tag_instances to native datetime.

After this migration, all `created_at` values will be BSON Date objects,
enabling proper date range queries without cross-type comparison bugs.

Usage:
    cd backend
    python migrate_tag_instances_dates.py
"""

from datetime import datetime, timezone
from pymongo import MongoClient
import sys

def migrate():
    client = MongoClient("mongodb://localhost:27017")
    db = client.smarttrendtracer

    # Count string vs datetime records
    string_count = db.tag_instances.count_documents({'created_at': {'$type': 'string'}})
    date_count = db.tag_instances.count_documents({'created_at': {'$type': 'date'}})
    total = db.tag_instances.count_documents({})

    print(f"Total tag_instances: {total}")
    print(f"  String created_at: {string_count}")
    print(f"  Native datetime:   {date_count}")
    print(f"  Other/missing:     {total - string_count - date_count}")

    if string_count == 0:
        print("\nNo string dates to convert. Migration already complete.")
        return

    print(f"\nConverting {string_count} string dates to native datetime...")

    # Process in batches
    batch_size = 1000
    converted = 0
    errors = 0

    cursor = db.tag_instances.find(
        {'created_at': {'$type': 'string'}},
        {'_id': 1, 'created_at': 1}
    ).batch_size(batch_size)

    from pymongo import UpdateOne
    ops = []

    for doc in cursor:
        try:
            date_str = doc['created_at']
            # Parse ISO format string to datetime
            if date_str.endswith('Z'):
                date_str = date_str[:-1] + '+00:00'
            dt = datetime.fromisoformat(date_str)
            # Ensure timezone-aware
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

            ops.append(UpdateOne(
                {'_id': doc['_id']},
                {'$set': {'created_at': dt}}
            ))
            converted += 1

            if len(ops) >= batch_size:
                db.tag_instances.bulk_write(ops)
                ops = []
                print(f"  Converted {converted}/{string_count}...")

        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"  Error converting {doc['_id']}: {e} (value: {doc['created_at']!r})")

    # Flush remaining
    if ops:
        db.tag_instances.bulk_write(ops)

    print(f"\nDone! Converted: {converted}, Errors: {errors}")

    # Verify
    remaining_strings = db.tag_instances.count_documents({'created_at': {'$type': 'string'}})
    print(f"Remaining string dates: {remaining_strings}")

if __name__ == '__main__':
    migrate()
