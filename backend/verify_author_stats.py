#!/usr/bin/env python3
"""
Verify and fix author statistics
"""

from pymongo import MongoClient
from bson import ObjectId

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client.smarttrendtracer

print("=== Author Statistics Verification ===\n")

# Get all authors with article count > 0
authors = list(db.substack_authors.find({'article_count': {'$gt': 0}}).sort('article_count', -1))

mismatches = 0
for author in authors:
    author_id = author['_id']
    name = author.get('name', 'Unknown')
    stored_count = author.get('article_count', 0)

    # Count actual articles
    actual_count = db.articles.count_documents({'primary_author_id': author_id})

    match = '✓' if stored_count == actual_count else '✗'
    print(f"{match} {name}")
    print(f"  Stored: {stored_count}, Actual: {actual_count}")

    if stored_count != actual_count:
        print(f"  ⚠️  MISMATCH - updating...")
        db.substack_authors.update_one(
            {'_id': author_id},
            {'$set': {'article_count': actual_count}}
        )
        mismatches += 1
    print()

if mismatches > 0:
    print(f"✓ Fixed {mismatches} mismatches")
else:
    print("✓ All author statistics are accurate!")
