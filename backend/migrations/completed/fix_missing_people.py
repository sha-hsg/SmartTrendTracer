#!/usr/bin/env python3
"""
Fix missing people by moving them under Person entity
"""

from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

client = MongoClient('mongodb://localhost:27017/')
db = client.smarttrendtracer

print("=" * 60)
print("FIXING MISSING PEOPLE IN TAXONOMY")
print("=" * 60)

# Get the Person entity root
person_entity = db.tag_concepts_v2.find_one({"display_name": "Person", "entity_type": "person"})
if not person_entity:
    print("ERROR: Person entity not found!")
    exit(1)

print(f"\nPerson entity found: {person_entity['_id']}")

# List of people to move under Person entity
people_to_fix = [
    "Christopher Manning",
    "Chris Potts", 
    "Ethan Mollick",
    "Sam Altman",
    "Dario Amodei",
    "Sebastian Raschka",
    "Andrej Karpathy",
    "Gary Marcus",
    "Nathan Lambert",
    "Yann LeCun",
    "Geoffrey Hinton",
    "Yoshua Bengio",
    "Andrew Ng",
    "Ian Goodfellow",
    "Demis Hassabis",
    "Greg Brockman",
    "Ilya Sutskever"
]

# Find more people by pattern
additional_people = db.tag_concepts_v2.find({
    "$and": [
        {"entity_type": {"$ne": "person"}},
        {"$or": [
            # Organization leaders
            {"display_name": {"$regex": "^(Elon Musk|Bill Gates|Mark Zuckerberg|Satya Nadella|Sundar Pichai|Tim Cook|Jeff Bezos|Jensen Huang)"}},
            # Researchers with full names
            {"display_name": {"$regex": "^[A-Z][a-z]+ [A-Z][a-z]+$"}},
        ]},
        # Make sure it has low usage to avoid false positives
        {"usage_count": {"$lte": 10}}
    ]
}).limit(100)

for person in additional_people:
    name = person['display_name']
    # Filter out obvious non-people
    if not any(word in name.lower() for word in ['model', 'system', 'method', 'algorithm', 'architecture', 'benchmark', 'dataset', 'framework', 'api', 'tool', 'platform', 'service']):
        # Check if it looks like a real person name
        parts = name.split()
        if len(parts) == 2 and parts[0][0].isupper() and parts[1][0].isupper():
            # Likely a person
            if name not in people_to_fix:
                people_to_fix.append(name)

print(f"\nPeople to move under Person entity: {len(people_to_fix)}")
print("-" * 40)

moved_count = 0
already_correct = 0

for person_name in sorted(people_to_fix):
    # Find the concept
    person_concept = db.tag_concepts_v2.find_one({"display_name": person_name})
    
    if person_concept:
        # Check if already under Person
        if person_concept.get('entity_type') == 'person' and person_entity['_id'] in person_concept.get('parents', []):
            already_correct += 1
            print(f"  ✓ '{person_name}' already correctly placed")
        else:
            # Move under Person entity
            result = db.tag_concepts_v2.update_one(
                {"_id": person_concept['_id']},
                {"$set": {
                    "entity_type": "person",
                    "parents": [person_entity['_id']],
                    "updated_at": datetime.utcnow()
                }}
            )
            if result.modified_count > 0:
                moved_count += 1
                usage = person_concept.get('usage_count', 0)
                print(f"  ✅ Moved '{person_name}' to Person entity (usage: {usage})")
            else:
                print(f"  ⚠️ Failed to move '{person_name}'")
    else:
        # Person doesn't exist yet - could create if needed
        print(f"  ℹ️ '{person_name}' not found in database")

# Update Person entity's children list
print("\nUpdating Person entity's children list...")
all_person_children = db.tag_concepts_v2.find({
    "parents": person_entity['_id']
}).distinct('_id')

db.tag_concepts_v2.update_one(
    {"_id": person_entity['_id']},
    {"$set": {"children": all_person_children}}
)

print(f"\n" + "=" * 60)
print("RESULTS:")
print(f"  Moved to Person entity: {moved_count}")
print(f"  Already correct: {already_correct}")
print(f"  Total people under Person: {len(all_person_children)}")

# List all people now under Person
print("\nAll people now under Person entity:")
print("-" * 40)
people_under_person = db.tag_concepts_v2.find(
    {"parents": person_entity['_id']},
    {"display_name": 1, "usage_count": 1}
).sort("display_name", 1)

for person in people_under_person:
    usage = person.get('usage_count', 0)
    if usage > 0:
        print(f"  • {person['display_name']} (used {usage} times)")
    else:
        print(f"  • {person['display_name']}")

print("=" * 60)
