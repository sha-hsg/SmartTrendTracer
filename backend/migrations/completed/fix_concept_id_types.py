#!/usr/bin/env python3
"""
Fix concept_id data type inconsistency in tag_instances collection.
Some concept_ids are stored as strings, others as ObjectIds, causing duplicates.
"""

from pymongo import MongoClient
from bson import ObjectId

client = MongoClient('mongodb://localhost:27017/')
db = client.smarttrendtracer

print('🔍 Checking for concept_id type inconsistencies')
print('=' * 60)

# Find all instances with string concept_ids
string_concept_ids = db.tag_instances.find({'concept_id': {'$type': 'string'}})
string_count = db.tag_instances.count_documents({'concept_id': {'$type': 'string'}})

print(f'\nFound {string_count} instances with string concept_ids')

if string_count > 0:
    print('\nConverting string concept_ids to ObjectIds...')
    
    converted = 0
    duplicates_removed = 0
    
    for instance in db.tag_instances.find({'concept_id': {'$type': 'string'}}):
        try:
            # Convert string to ObjectId
            new_concept_id = ObjectId(instance['concept_id'])
            
            # Check if this would create a duplicate
            existing = db.tag_instances.find_one({
                'content_type': instance['content_type'],
                'content_id': instance['content_id'],
                'concept_id': new_concept_id
            })
            
            if existing:
                # Duplicate would be created, remove this instance
                db.tag_instances.delete_one({'_id': instance['_id']})
                duplicates_removed += 1
                print(f'  ❌ Removed duplicate: {instance["content_type"]} {instance["content_id"]} -> concept {instance["concept_id"]}')
            else:
                # Update to ObjectId
                db.tag_instances.update_one(
                    {'_id': instance['_id']},
                    {'$set': {'concept_id': new_concept_id}}
                )
                converted += 1
                
        except Exception as e:
            print(f'  ⚠️  Could not convert {instance["concept_id"]}: {e}')
    
    print(f'\n✅ Converted {converted} concept_ids from string to ObjectId')
    print(f'✅ Removed {duplicates_removed} duplicates')

# Verify unique index is in place
print('\n🛡️ Verifying unique index...')
indexes = db.tag_instances.list_indexes()
has_unique = False
for idx in indexes:
    if 'unique' in idx and idx['unique']:
        if 'content_type' in idx['key'] and 'content_id' in idx['key'] and 'concept_id' in idx['key']:
            has_unique = True
            print(f'✅ Unique index found: {idx["name"]}')
            break

if not has_unique:
    print('Creating unique index...')
    try:
        db.tag_instances.create_index(
            [
                ('content_type', 1),
                ('content_id', 1),
                ('concept_id', 1)
            ],
            unique=True,
            name='unique_content_concept'
        )
        print('✅ Created unique index')
    except Exception as e:
        print(f'⚠️  Could not create index: {e}')

# Final verification
print('\n📊 Final Statistics:')
total_instances = db.tag_instances.count_documents({})
string_remaining = db.tag_instances.count_documents({'concept_id': {'$type': 'string'}})
objectid_count = db.tag_instances.count_documents({'concept_id': {'$type': 'objectId'}})

print(f'Total instances: {total_instances}')
print(f'ObjectId concept_ids: {objectid_count}')
print(f'String concept_ids remaining: {string_remaining}')

# Check specific tweet
print('\n🔍 Checking the Innovator\'s Dilemma tweet:')
instances = list(db.tag_instances.find({
    'content_type': 'tweet',
    'content_id': '1948585378991976525'
}))

print(f'Concepts attached: {len(instances)}')
for inst in instances:
    concept = db.tag_concepts_v2.find_one({'_id': inst['concept_id']})
    if concept:
        print(f'  - {concept["display_name"]} (type: {type(inst["concept_id"]).__name__})')

print('\n✅ Fix complete!')