#!/usr/bin/env python3
"""
Fix author name fields that are missing or undefined
"""

from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client.smarttrendtracer

print("=== Fixing Author Name Fields ===\n")

# Find authors with missing or undefined name field
authors = list(db.substack_authors.find({}))

fixed = 0
for author in authors:
    author_id = author['_id']
    name = author.get('name')
    canonical_name = author.get('canonical_name')

    # If name is missing but canonical_name exists, copy it
    if (not name or name == 'undefined') and canonical_name:
        print(f"Fixing: {name} → {canonical_name}")
        db.substack_authors.update_one(
            {'_id': author_id},
            {'$set': {'name': canonical_name}}
        )
        fixed += 1

    # If canonical_name is missing but name exists, copy it
    elif name and not canonical_name:
        print(f"Adding canonical_name: {name}")
        db.substack_authors.update_one(
            {'_id': author_id},
            {'$set': {'canonical_name': name}}
        )
        fixed += 1

print(f"\n✓ Fixed {fixed} author records")

# Show final state
print("\n=== Final Author List ===")
authors = list(db.substack_authors.find({}, {
    'name': 1,
    'canonical_name': 1,
    'article_count': 1
}).sort('article_count', -1))

for author in authors:
    name = author.get('name', 'NO NAME')
    count = author.get('article_count', 0)
    print(f"  {name}: {count} articles")
