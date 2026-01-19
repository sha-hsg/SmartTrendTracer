#!/usr/bin/env python3
"""
Fix all concept base inconsistencies:
1. Merge duplicate root concepts
2. Move François Chollet under Person entity
3. Ensure entity exclusivity
4. Clean up orphaned concepts
5. Fix parent-child bidirectional relationships
"""

from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

client = MongoClient('mongodb://localhost:27017/')
db = client.smarttrendtracer

print("=" * 60)
print("FIXING ALL CONCEPT BASE INCONSISTENCIES")
print("=" * 60)

# Step 1: Merge duplicate root concepts
print("\n1. MERGING DUPLICATE ROOT CONCEPTS...")

duplicate_roots = list(db.tag_concepts_v2.aggregate([
    {"$match": {"parents": {"$size": 0}}},
    {"$group": {
        "_id": "$display_name",
        "ids": {"$push": "$_id"},
        "count": {"$sum": 1}
    }},
    {"$match": {"count": {"$gt": 1}}}
]))

for dup in duplicate_roots:
    print(f"\nMerging '{dup['_id']}' ({dup['count']} copies)")
    
    # Keep the first one, update children of others
    primary_id = dup['ids'][0]
    duplicate_ids = dup['ids'][1:]
    
    # Find all children of duplicates
    children_to_update = db.tag_concepts_v2.find({
        "parents": {"$in": duplicate_ids}
    })
    
    updated_children = 0
    for child in children_to_update:
        new_parents = []
        for parent in child['parents']:
            if parent in duplicate_ids:
                new_parents.append(primary_id)
            else:
                new_parents.append(parent)
        
        # Remove duplicates from new_parents
        new_parents = list(set(new_parents))
        
        db.tag_concepts_v2.update_one(
            {"_id": child['_id']},
            {"$set": {"parents": new_parents}}
        )
        updated_children += 1
    
    # Delete the duplicates
    result = db.tag_concepts_v2.delete_many({"_id": {"$in": duplicate_ids}})
    print(f"  ✅ Merged into {primary_id}, updated {updated_children} children, deleted {result.deleted_count} duplicates")

# Step 2: Fix François Chollet and other misplaced person entities
print("\n2. FIXING MISPLACED PERSON ENTITIES...")

# First, ensure we have a Person entity type root
person_root = db.tag_concepts_v2.find_one({
    "slug": "person",
    "entity_type": "person"
})

if not person_root:
    # Create Person root under Named Entities
    named_entities = db.tag_concepts_v2.find_one({
        "display_name": "Named Entities",
        "parents": {"$size": 0}
    })
    
    if named_entities:
        person_root = {
            "slug": "person",
            "display_name": "Person",
            "entity_type": "person",
            "parents": [named_entities['_id']],
            "children": [],
            "status": "active",
            "usage_count": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        result = db.tag_concepts_v2.insert_one(person_root)
        person_root['_id'] = result.inserted_id
        print(f"  ✅ Created Person entity type")

# Move François Chollet and any other person at root
persons_at_root = db.tag_concepts_v2.find({
    "parents": {"$size": 0},
    "$or": [
        {"display_name": {"$regex": "François|Chollet", "$options": "i"}},
        {"entity_type": "person"}
    ]
})

for person in persons_at_root:
    if person['_id'] != person_root['_id']:  # Don't move the Person root itself
        db.tag_concepts_v2.update_one(
            {"_id": person['_id']},
            {"$set": {
                "parents": [person_root['_id']],
                "entity_type": "person"
            }}
        )
        print(f"  ✅ Moved '{person['display_name']}' under Person entity")

# Step 3: Ensure entity exclusivity for organizations, locations, events
print("\n3. ENSURING ENTITY EXCLUSIVITY...")

entity_types = {
    "organisation": "Organization",
    "location": "Location", 
    "event": "Event"
}

for entity_type, display_name in entity_types.items():
    # Find or create the entity root
    entity_root = db.tag_concepts_v2.find_one({
        "slug": entity_type,
        "entity_type": entity_type
    })
    
    if not entity_root:
        named_entities = db.tag_concepts_v2.find_one({
            "display_name": "Named Entities",
            "parents": {"$size": 0}
        })
        
        if named_entities:
            entity_root = {
                "slug": entity_type,
                "display_name": display_name,
                "entity_type": entity_type,
                "parents": [named_entities['_id']],
                "children": [],
                "status": "active",
                "usage_count": 0,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            result = db.tag_concepts_v2.insert_one(entity_root)
            entity_root['_id'] = result.inserted_id
            print(f"  ✅ Created {display_name} entity type")
    
    # Find all concepts with this entity type
    entities = db.tag_concepts_v2.find({
        "entity_type": entity_type,
        "_id": {"$ne": entity_root['_id']}
    })
    
    fixed_count = 0
    for entity in entities:
        # Check if it has multiple parents or wrong parent
        if len(entity.get('parents', [])) != 1 or entity_root['_id'] not in entity.get('parents', []):
            db.tag_concepts_v2.update_one(
                {"_id": entity['_id']},
                {"$set": {"parents": [entity_root['_id']]}}
            )
            fixed_count += 1
    
    if fixed_count > 0:
        print(f"  ✅ Fixed {fixed_count} {entity_type} entities to be exclusive")

# Step 4: Fix parent-child bidirectional relationships
print("\n4. FIXING PARENT-CHILD RELATIONSHIPS...")

# Clear all children arrays first
db.tag_concepts_v2.update_many({}, {"$set": {"children": []}})

# Rebuild children arrays from parent relationships
all_concepts = db.tag_concepts_v2.find()
parent_to_children = {}

for concept in all_concepts:
    for parent_id in concept.get('parents', []):
        if parent_id not in parent_to_children:
            parent_to_children[parent_id] = []
        parent_to_children[parent_id].append(concept['_id'])

# Update all parent concepts with their children
for parent_id, children_ids in parent_to_children.items():
    db.tag_concepts_v2.update_one(
        {"_id": parent_id},
        {"$set": {"children": children_ids}}
    )

print(f"  ✅ Rebuilt parent-child relationships for {len(parent_to_children)} parents")

# Step 5: Remove truly orphaned concepts (no parents, no children, no usage)
print("\n5. CLEANING ORPHANED CONCEPTS...")

orphans = db.tag_concepts_v2.find({
    "parents": {"$size": 0},
    "children": {"$in": [[], None]},
    "usage_count": {"$in": [0, None]}
})

orphan_list = list(orphans)
# Keep only valid root categories
valid_roots = [
    "Named Entities", "Research Entities", "Content Types",
    "AI/ML Fundamentals", "Models & Architectures", "Techniques & Methods",
    "Applications & Domains", "Data & Datasets", "Tools & Infrastructure",
    "Research & Development", "Industry & Business", "Ethics & Society",
    "Evaluation & Metrics", "Large Language Models (LLMs)"
]

removed = 0
for orphan in orphan_list:
    if orphan['display_name'] not in valid_roots:
        result = db.tag_concepts_v2.delete_one({"_id": orphan['_id']})
        if result.deleted_count > 0:
            removed += 1
            print(f"  ✅ Removed orphan: '{orphan['display_name']}'")

print(f"  ✅ Total orphans removed: {removed}")

# Step 6: Final verification
print("\n6. FINAL VERIFICATION...")

total = db.tag_concepts_v2.count_documents({})
roots = db.tag_concepts_v2.count_documents({"parents": {"$size": 0}})
organized = db.tag_concepts_v2.count_documents({"parents": {"$ne": []}})
with_children = db.tag_concepts_v2.count_documents({"children": {"$ne": []}})
with_usage = db.tag_concepts_v2.count_documents({"usage_count": {"$gt": 0}})

# Check for any remaining duplicates
remaining_dups = list(db.tag_concepts_v2.aggregate([
    {"$match": {"parents": {"$size": 0}}},
    {"$group": {
        "_id": "$display_name",
        "count": {"$sum": 1}
    }},
    {"$match": {"count": {"$gt": 1}}}
]))

print(f"""
Final Statistics:
  Total concepts: {total}
  Root concepts: {roots}
  Organized concepts: {organized}
  Concepts with children: {with_children}
  Concepts with usage: {with_usage}
  Remaining duplicate roots: {len(remaining_dups)}
""")

if remaining_dups:
    print("⚠️ Still have duplicate roots:")
    for dup in remaining_dups:
        print(f"  - {dup['_id']} ({dup['count']} copies)")
else:
    print("✅ No duplicate roots remaining!")

# List final root concepts
final_roots = db.tag_concepts_v2.find(
    {"parents": {"$size": 0}},
    {"display_name": 1}
).sort("display_name", 1)

print("\nFinal Root Concepts:")
for root in final_roots:
    print(f"  - {root['display_name']}")

print("\n" + "=" * 60)
print("CONCEPT BASE CLEANUP COMPLETE!")
print("=" * 60)
