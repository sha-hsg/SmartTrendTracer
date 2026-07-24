#!/usr/bin/env python3
"""
Fix Person entity and properly classify all people concepts
"""

from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

client = MongoClient('mongodb://localhost:27017/')
db = client.smarttrendtracer

print("=" * 60)
print("FIXING PERSON ENTITY AND PEOPLE CONCEPTS")
print("=" * 60)

# Step 1: Find or create Person entity
print("\n1. CHECKING PERSON ENTITY...")
print("-" * 40)

person_entity = db.tag_concepts_v2.find_one({
    "$or": [
        {"display_name": "Person", "entity_type": "person"},
        {"slug": "person", "entity_type": "person"},
        {"display_name": "Person"},
        {"slug": "person"}
    ]
})

if not person_entity:
    print("❌ Person entity not found, creating it...")
    
    # Find Named Entities parent
    named_entities = db.tag_concepts_v2.find_one({
        "display_name": "Named Entities",
        "parents": []
    })
    
    if not named_entities:
        print("Creating Named Entities root...")
        named_entities_doc = {
            "_id": ObjectId("68af78566b4944766c2e6f0a"),
            "slug": "named_entities",
            "display_name": "Named Entities",
            "entity_type": None,
            "parents": [],
            "children": [],
            "status": "active",
            "usage_count": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        result = db.tag_concepts_v2.insert_one(named_entities_doc)
        named_entities = named_entities_doc
        print(f"✅ Created Named Entities: {named_entities['_id']}")
    
    # Create Person entity
    person_doc = {
        "_id": ObjectId("68af78566b4944766c2e6f0b"),
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
    result = db.tag_concepts_v2.insert_one(person_doc)
    person_entity = person_doc
    print(f"✅ Created Person entity: {person_entity['_id']}")
else:
    print(f"✅ Person entity found: {person_entity['_id']}")
    # Ensure it has correct entity_type
    if person_entity.get('entity_type') != 'person':
        db.tag_concepts_v2.update_one(
            {"_id": person_entity['_id']},
            {"$set": {"entity_type": "person"}}
        )
        print("  Fixed entity_type to 'person'")

# Step 2: Find all people concepts
print("\n2. FINDING ALL PEOPLE CONCEPTS...")
print("-" * 40)

# List of people to properly classify
people_to_fix = {
    # People with annotations (usage > 0)
    "Christopher Manning": {"variants": ["Chris Manning", "Christopher D. Manning"]},
    "Chris Potts": {"variants": []},
    "Ethan Mollick": {"variants": ["emollick"]},
    "François Chollet": {"variants": ["Francois Chollet"]},
    "Jack Clark": {"variants": []},
    
    # Other known AI researchers
    "Sam Altman": {"variants": ["sama"]},
    "Dario Amodei": {"variants": []},
    "Sebastian Raschka": {"variants": []},
    "Andrej Karpathy": {"variants": []},
    "Gary Marcus": {"variants": []},
    "Nathan Lambert": {"variants": []},
    "Yann LeCun": {"variants": ["Yann Le Cun"]},
    "Geoffrey Hinton": {"variants": ["Geoff Hinton"]},
    "Yoshua Bengio": {"variants": []},
    "Andrew Ng": {"variants": []},
    "Ian Goodfellow": {"variants": []},
    "Demis Hassabis": {"variants": []},
    "Greg Brockman": {"variants": []},
    "Ilya Sutskever": {"variants": []},
}

fixed_count = 0
already_correct = 0

for person_name, info in people_to_fix.items():
    # Search for the person and variants
    search_names = [person_name] + info.get('variants', [])
    
    person_concept = None
    for search_name in search_names:
        person_concept = db.tag_concepts_v2.find_one({
            "display_name": {"$regex": f"^{search_name}$", "$options": "i"}
        })
        if person_concept:
            break
    
    if person_concept:
        # Check if already correctly placed
        if (person_concept.get('entity_type') == 'person' and 
            person_entity['_id'] in person_concept.get('parents', [])):
            already_correct += 1
            print(f"  ✅ '{person_concept['display_name']}' already correct")
        else:
            # Fix the person concept
            result = db.tag_concepts_v2.update_one(
                {"_id": person_concept['_id']},
                {"$set": {
                    "entity_type": "person",
                    "parents": [person_entity['_id']],
                    "updated_at": datetime.utcnow()
                }}
            )
            if result.modified_count > 0:
                fixed_count += 1
                usage = person_concept.get('usage_count', 0)
                print(f"  ✅ Fixed '{person_concept['display_name']}' (usage: {usage})")
            else:
                print(f"  ⚠️ Failed to fix '{person_concept['display_name']}'")
    else:
        # Person doesn't exist, could create if needed
        print(f"  ℹ️ '{person_name}' not found in database")

# Step 3: Update Person entity's children list
print("\n3. UPDATING PERSON ENTITY'S CHILDREN...")
print("-" * 40)

all_person_children = list(db.tag_concepts_v2.find({
    "parents": person_entity['_id']
}).distinct('_id'))

db.tag_concepts_v2.update_one(
    {"_id": person_entity['_id']},
    {"$set": {"children": all_person_children}}
)

print(f"✅ Updated Person entity with {len(all_person_children)} children")

# Step 4: Update Named Entities if it exists
named_entities = db.tag_concepts_v2.find_one({
    "display_name": "Named Entities",
    "parents": []
})

if named_entities and person_entity['_id'] not in named_entities.get('children', []):
    db.tag_concepts_v2.update_one(
        {"_id": named_entities['_id']},
        {"$addToSet": {"children": person_entity['_id']}}
    )
    print(f"✅ Added Person entity to Named Entities children")

# Step 5: List all people now under Person
print("\n4. ALL PEOPLE UNDER PERSON ENTITY...")
print("-" * 40)

people_under_person = list(db.tag_concepts_v2.find(
    {"parents": person_entity['_id']},
    {"display_name": 1, "usage_count": 1}
).sort("display_name", 1))

for person in people_under_person:
    usage = person.get('usage_count', 0)
    if usage > 0:
        print(f"  ✅ {person['display_name']} (used {usage} times)")
    else:
        print(f"  ✅ {person['display_name']}")

print("\n" + "=" * 60)
print("RESULTS:")
print(f"  Fixed: {fixed_count} people")
print(f"  Already correct: {already_correct}")
print(f"  Total people under Person: {len(all_person_children)}")
print("=" * 60)