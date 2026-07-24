#!/usr/bin/env python3
"""
Check for duplicate concepts in the database
"""

from pymongo import MongoClient
from bson import ObjectId

client = MongoClient('mongodb://localhost:27017/')
db = client.smarttrendtracer

print('🔍 Investigating duplicate concepts issue')
print('=' * 60)

# Search for Innovator's Dilemma concepts
print("\n1. Searching for 'Innovator' related concepts:")
concepts = list(db.tag_concepts_v2.find({
    'display_name': {'$regex': 'Innovator', '$options': 'i'}
}))

print(f"Found {len(concepts)} concepts with 'Innovator' in the name")

for concept in concepts:
    print(f"\n  Concept #{concepts.index(concept) + 1}:")
    print(f"    ID: {concept['_id']}")
    print(f"    Display: {concept.get('display_name')}")
    print(f"    Slug: {concept.get('slug')}")
    parents = concept.get('parents', [])
    if parents:
        print(f"    Parents: {parents[:2]}...")  # Show first 2 parents
    else:
        print(f"    Parents: None (root concept)")

# Check for exact duplicates
print("\n2. Checking for ALL duplicate display names:")
pipeline = [
    {'$group': {
        '_id': '$display_name',
        'count': {'$sum': 1},
        'ids': {'$push': '$_id'}
    }},
    {'$match': {'count': {'$gt': 1}}},
    {'$sort': {'count': -1}},
    {'$limit': 20}
]

try:
    duplicates = list(db.tag_concepts_v2.aggregate(pipeline))
    print(f"\nFound {len(duplicates)} concepts with duplicate display names:")
    
    for dup in duplicates[:10]:  # Show top 10
        print(f"\n  '{dup['_id']}': {dup['count']} duplicates")
        for i, concept_id in enumerate(dup['ids'][:3], 1):
            # Get more info about each duplicate
            concept = db.tag_concepts_v2.find_one({'_id': concept_id})
            if concept:
                print(f"    {i}. ID: {concept_id}")
                print(f"       Slug: {concept.get('slug')}")
                parents = concept.get('parents', [])
                if parents:
                    # Get parent names
                    parent_names = []
                    for pid in parents[:2]:  # Just first 2 parents
                        parent = db.tag_concepts_v2.find_one({'_id': pid})
                        if parent:
                            parent_names.append(parent.get('display_name', 'Unknown'))
                    print(f"       Parents: {', '.join(parent_names)}")
                else:
                    print(f"       Parents: None (root)")
                    
except Exception as e:
    print(f"Error in aggregation: {e}")

# Specific check for Innovator's Dilemma
print("\n3. Specific check for \"Innovator's Dilemma\" duplicates:")
exact_matches = list(db.tag_concepts_v2.find({
    'display_name': "Innovator's Dilemma"
}))

if len(exact_matches) > 1:
    print(f"⚠️  Found {len(exact_matches)} exact matches for \"Innovator's Dilemma\":")
    for match in exact_matches:
        print(f"\n  ID: {match['_id']}")
        print(f"  Slug: {match.get('slug')}")
        # Check usage
        usage_count = db.tag_instances.count_documents({'concept_id': match['_id']})
        print(f"  Usage count: {usage_count}")
        # Get parent info
        parents = match.get('parents', [])
        if parents:
            parent = db.tag_concepts_v2.find_one({'_id': parents[0]})
            if parent:
                print(f"  Parent: {parent.get('display_name')}")
elif exact_matches:
    print(f"✅ Only one \"Innovator's Dilemma\" concept found")
else:
    print(f"❌ No \"Innovator's Dilemma\" concept found")

print("\n" + "=" * 60)
print("RECOMMENDATION:")
if len(duplicates) > 0:
    print("🔧 Duplicates found! Need to:")
    print("   1. Merge duplicate concepts")
    print("   2. Update tag_instances to point to the merged concept")
    print("   3. Remove duplicate entries")
else:
    print("✅ No duplicates found in concept names")