#!/usr/bin/env python3
"""
Fix duplicate concept attachments and prevent future duplicates
"""

from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

client = MongoClient('mongodb://localhost:27017/')
db = client.smarttrendtracer

print('🔍 Checking for duplicate concept attachments')
print('=' * 60)

# Find Innovator's Dilemma concept
concept = db.tag_concepts_v2.find_one({'display_name': "Innovator's Dilemma"})
if concept:
    concept_id = concept['_id']
    print(f'\nInnovator\'s Dilemma concept ID: {concept_id}')
    
    # Find all instances
    instances = list(db.tag_instances.find({
        'concept_id': concept_id,
        'content_type': 'tweet'
    }))
    
    print(f'Found {len(instances)} tag instances for this concept')
    
    # Group by content_id to find duplicates
    by_tweet = {}
    for inst in instances:
        tweet_id = inst['content_id']
        if tweet_id not in by_tweet:
            by_tweet[tweet_id] = []
        by_tweet[tweet_id].append(inst)
    
    # Check for duplicates
    duplicates_to_remove = []
    for tweet_id, instances in by_tweet.items():
        if len(instances) > 1:
            print(f'\n⚠️  Tweet {tweet_id} has {len(instances)} duplicate attachments!')
            # Keep the first one, mark others for removal
            for i, inst in enumerate(instances, 1):
                print(f'  {i}. Instance ID: {inst["_id"]}')
                print(f'     Created: {inst.get("created_at", "Unknown")}')
                if i > 1:
                    duplicates_to_remove.append(inst["_id"])
                    print(f'     ❌ Will be removed')
                else:
                    print(f'     ✅ Will be kept')

# Check for all duplicate attachments in the system
print('\n\n📊 Checking ALL duplicate concept attachments:')
pipeline = [
    {'$group': {
        '_id': {
            'content_type': '$content_type',
            'content_id': '$content_id', 
            'concept_id': '$concept_id'
        },
        'count': {'$sum': 1},
        'instance_ids': {'$push': '$_id'}
    }},
    {'$match': {'count': {'$gt': 1}}},
    {'$sort': {'count': -1}},
    {'$limit': 20}
]

all_duplicates = list(db.tag_instances.aggregate(pipeline))
print(f'Found {len(all_duplicates)} cases of duplicate attachments')

total_duplicates_to_remove = []
for dup in all_duplicates:
    # Keep first, remove rest
    instances_to_remove = dup['instance_ids'][1:]  # Skip first one
    total_duplicates_to_remove.extend(instances_to_remove)
    
    if len(all_duplicates) <= 10:  # Show details for first 10
        concept = db.tag_concepts_v2.find_one({'_id': dup["_id"]["concept_id"]})
        concept_name = concept.get('display_name', 'Unknown') if concept else 'Unknown'
        print(f'\n  Content: {dup["_id"]["content_type"]} {dup["_id"]["content_id"]}')
        print(f'  Concept: {concept_name}')
        print(f'  Duplicates: {dup["count"]} instances (will remove {len(instances_to_remove)})')

# Fix the duplicates
print('\n\n🔧 FIXING DUPLICATE ATTACHMENTS')
print('=' * 60)

if total_duplicates_to_remove:
    print(f'Will remove {len(total_duplicates_to_remove)} duplicate tag instances')
    
    response = input('\nProceed with removal? (yes/no): ')
    if response.lower() == 'yes':
        result = db.tag_instances.delete_many({
            '_id': {'$in': total_duplicates_to_remove}
        })
        print(f'✅ Removed {result.deleted_count} duplicate attachments')
    else:
        print('❌ Removal cancelled')
else:
    print('✅ No duplicate attachments found!')

print('\n\n🛡️ IMPLEMENTING DUPLICATE PREVENTION')
print('=' * 60)

# Create unique index to prevent future duplicates
print('Creating unique compound index on tag_instances...')
try:
    # Drop existing non-unique indexes if they exist
    existing_indexes = db.tag_instances.list_indexes()
    for idx in existing_indexes:
        if 'content_type' in idx['key'] and 'content_id' in idx['key'] and 'concept_id' in idx['key']:
            if not idx.get('unique'):
                print(f'  Dropping non-unique index: {idx["name"]}')
                db.tag_instances.drop_index(idx['name'])
    
    # Create unique compound index
    db.tag_instances.create_index(
        [
            ('content_type', 1),
            ('content_id', 1),
            ('concept_id', 1)
        ],
        unique=True,
        name='unique_content_concept'
    )
    print('✅ Created unique compound index to prevent duplicate attachments')
    print('   Future attempts to attach the same concept twice will be rejected')
except Exception as e:
    if 'duplicate key error' in str(e).lower():
        print('❌ Cannot create unique index - duplicates still exist!')
        print('   Please run the removal process first')
    else:
        print(f'⚠️  Index creation issue: {e}')

print('\n✅ Fix complete!')