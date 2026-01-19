#!/usr/bin/env python3
"""
Prioritize Named Entities in the hierarchy - make it first among roots
"""

from pymongo import MongoClient
from datetime import datetime

client = MongoClient('mongodb://localhost:27017/')
db = client.smarttrendtracer

print("=" * 60)
print("PRIORITIZING NAMED ENTITIES IN HIERARCHY")
print("=" * 60)

# Get current root concepts
print("\n1. CURRENT ROOT ORDER...")
print("-" * 40)

roots = list(db.tag_concepts_v2.find({
    "$or": [
        {"parents": []},
        {"parents": {"$exists": False}},
        {"parents": None}
    ]
}).sort("display_name", 1))

print("Current root concepts order:")
for i, root in enumerate(roots):
    print(f"  {i+1}. {root['display_name']}")

# Check if Named Entities exists and is a root
named_entities = db.tag_concepts_v2.find_one({"display_name": "Named Entities"})

if not named_entities:
    print("\n⚠️ Named Entities not found! Creating it...")
    named_entities = {
        "_id": "c_named_entities",
        "slug": "named_entities",
        "display_name": "Named Entities",
        "description": "People, organizations, locations, events, and other named entities",
        "entity_type": None,
        "parents": [],
        "children": [],
        "usage_count": 0,
        "status": "active",
        "priority": 1,  # Highest priority
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    db.tag_concepts_v2.insert_one(named_entities)
    print("✅ Created Named Entities root")

# Add priority field to all roots to control display order
print("\n2. SETTING DISPLAY PRIORITIES...")
print("-" * 40)

# Define preferred order
priority_order = [
    "Named Entities",           # 1st - Most important
    "AI/ML Fundamentals",       # 2nd
    "Models & Architectures",   # 3rd  
    "Techniques & Methods",     # 4th
    "Applications & Domains",   # 5th
    "Data & Datasets",         # 6th
    "Tools & Infrastructure",  # 7th
    "Research & Development",  # 8th
    "Industry & Business",     # 9th
    "Ethics & Society",        # 10th
    "Evaluation & Metrics",    # 11th
    "Content Types",           # 12th
    "Research Entities",       # 13th
]

# Set priorities
for priority, name in enumerate(priority_order, 1):
    result = db.tag_concepts_v2.update_one(
        {"display_name": name, "parents": []},
        {"$set": {"priority": priority}}
    )
    if result.modified_count > 0:
        print(f"  ✅ Set priority {priority} for {name}")

# Set low priority for any other roots
db.tag_concepts_v2.update_many(
    {"parents": [], "priority": {"$exists": False}},
    {"$set": {"priority": 999}}
)

# Ensure entity types under Named Entities are properly organized
print("\n3. ORGANIZING ENTITY TYPES...")
print("-" * 40)

entity_types = [
    {"name": "Person", "type": "person", "description": "Individual people and researchers", "icon": "👤"},
    {"name": "Organisation", "type": "organisation", "description": "Companies, institutions, and organizations", "icon": "🏢"},
    {"name": "Location", "type": "location", "description": "Places, regions, and geographical entities", "icon": "📍"},
    {"name": "Event", "type": "event", "description": "Conferences, launches, and notable events", "icon": "📅"},
    {"name": "Product/Service", "type": "product", "description": "Products, services, and platforms", "icon": "📦"},
    {"name": "Hardware", "type": "hardware", "description": "Physical computing devices and hardware", "icon": "💻"}
]

for entity_def in entity_types:
    entity = db.tag_concepts_v2.find_one({
        "display_name": entity_def["name"],
        "entity_type": entity_def["type"]
    })
    
    if entity:
        # Ensure it's under Named Entities
        if named_entities['_id'] not in entity.get('parents', []):
            db.tag_concepts_v2.update_one(
                {"_id": entity['_id']},
                {"$set": {
                    "parents": [named_entities['_id']],
                    "description": entity_def["description"],
                    "icon": entity_def["icon"]
                }}
            )
            print(f"  ✅ Updated {entity_def['name']} under Named Entities")
        else:
            # Just update icon and description
            db.tag_concepts_v2.update_one(
                {"_id": entity['_id']},
                {"$set": {
                    "description": entity_def["description"],
                    "icon": entity_def["icon"]
                }}
            )
            print(f"  ✅ Updated {entity_def['name']} metadata")
    else:
        # Create it
        new_entity = {
            "slug": entity_def["type"],
            "display_name": entity_def["name"],
            "description": entity_def["description"],
            "entity_type": entity_def["type"],
            "parents": [named_entities['_id']],
            "children": [],
            "icon": entity_def["icon"],
            "usage_count": 0,
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        result = db.tag_concepts_v2.insert_one(new_entity)
        print(f"  ✅ Created {entity_def['name']} entity type")

# Update Named Entities children
children_ids = list(db.tag_concepts_v2.find(
    {"parents": named_entities['_id']}
).distinct('_id'))

db.tag_concepts_v2.update_one(
    {"_id": named_entities['_id']},
    {"$set": {"children": children_ids}}
)

print(f"\n✅ Named Entities now has {len(children_ids)} entity types")

# Verify final order
print("\n4. FINAL ROOT ORDER...")
print("-" * 40)

final_roots = list(db.tag_concepts_v2.find({
    "$or": [
        {"parents": []},
        {"parents": {"$exists": False}}, 
        {"parents": None}
    ]
}).sort("priority", 1))

print("New root concepts order (by priority):")
for i, root in enumerate(final_roots):
    priority = root.get('priority', 999)
    print(f"  {i+1}. {root['display_name']} (priority: {priority})")

print("\n" + "=" * 60)
print("PRIORITIZATION COMPLETE")
print("=" * 60)