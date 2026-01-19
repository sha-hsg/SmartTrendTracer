#!/usr/bin/env python3
"""Test article concepts fetching"""

from pymongo import MongoClient
from app.services.concept_only_tag_service import ConceptOnlyTagService

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client.smarttrendtracer

# Initialize concept service
concept_service = ConceptOnlyTagService()

# Get article with old_sqlite_id = 1
article = db.articles.find_one({'old_sqlite_id': 1})
print(f"Article: {article['title'][:50]}...")
print(f"Article ID: {article['_id']}")
print(f"Old SQLite ID: {article.get('old_sqlite_id')}")

# Get concepts from tag_instances
article_id = str(article['_id'])
sqlite_id = str(article.get('old_sqlite_id', ''))

tag_instances = list(db.tag_instances.find({
    'content_type': 'article',
    '$or': [
        {'content_id': article_id},
        {'content_id': sqlite_id}
    ]
}))

print(f"\nFound {len(tag_instances)} tag instances")

# Get concept details
concepts = []
for ti in tag_instances[:5]:
    cid = ti['concept_id']
    print(f"\nProcessing concept_id: {cid} (type: {type(cid)})")
    
    try:
        concept = concept_service.get_concept_by_id(cid)
        if concept:
            print(f"  Found: {concept.get('display_name')}")
            concepts.append({
                'concept_id': cid,
                'display_name': concept.get('display_name'),
                'slug': concept.get('slug')
            })
        else:
            print(f"  Not found")
    except Exception as e:
        print(f"  Error: {e}")

print(f"\n\nTotal concepts found: {len(concepts)}")
for c in concepts:
    print(f"  - {c['display_name']}")