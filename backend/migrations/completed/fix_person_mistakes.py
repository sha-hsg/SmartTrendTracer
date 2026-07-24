#!/usr/bin/env python3
"""
Fix the mistakes - move non-people OUT of Person entity
"""

from pymongo import MongoClient
from bson import ObjectId

client = MongoClient('mongodb://localhost:27017/')
db = client.smarttrendtracer

print("FIXING PERSON ENTITY MISTAKES...")

# These are ACTUAL people that should stay
actual_people = [
    "Christopher Manning",
    "Chris Potts",
    "Ethan Mollick", 
    "Sam Altman",
    "Dario Amodei",
    "Sebastian Raschka",
    "Andrej Karpathy",
    "Gary Marcus",
    "François Chollet"
]

# Get Person entity
person_entity = db.tag_concepts_v2.find_one({"display_name": "Person", "entity_type": "person"})

# Find appropriate parents for misplaced concepts
ai_fundamentals = db.tag_concepts_v2.find_one({"display_name": "AI/ML Fundamentals"})
models_arch = db.tag_concepts_v2.find_one({"display_name": "Models & Architectures"})
techniques = db.tag_concepts_v2.find_one({"display_name": "Techniques & Methods"})
applications = db.tag_concepts_v2.find_one({"display_name": "Applications & Domains"})
research_entities = db.tag_concepts_v2.find_one({"display_name": "Research Entities", "parents": {"$size": 0}})

# Get all concepts currently under Person
under_person = db.tag_concepts_v2.find({"parents": person_entity['_id']})

fixed_count = 0
for concept in under_person:
    name = concept['display_name']
    
    # Skip actual people
    if name in actual_people:
        print(f"  ✓ Keeping '{name}' under Person")
        continue
    
    # Determine correct parent
    new_parent = None
    entity_type = "concept"
    
    if name in ["Named Entities", "Research Entities", "Content Types"]:
        # These should be roots
        new_parent = []
        entity_type = "category"
    elif "attention" in name.lower() or name == "Self Attention" or name == "Linear Attention" or name == "Causal Attention":
        new_parent = [models_arch['_id']]
        entity_type = "architecture"
    elif name == "Knowledge Graph":
        new_parent = [ai_fundamentals['_id']]
    elif any(x in name.lower() for x in ["chat", "gpt", "gemini", "speech", "image", "audio", "virtual"]):
        new_parent = [applications['_id']]
    elif any(x in name.lower() for x in ["data", "privacy", "performance", "error", "metric"]):
        new_parent = [techniques['_id']]
    else:
        new_parent = [research_entities['_id']]
    
    # Fix the concept
    result = db.tag_concepts_v2.update_one(
        {"_id": concept['_id']},
        {"$set": {
            "parents": new_parent,
            "entity_type": entity_type
        }}
    )
    
    if result.modified_count > 0:
        fixed_count += 1
        parent_name = "ROOT" if new_parent == [] else db.tag_concepts_v2.find_one({"_id": new_parent[0]})['display_name']
        print(f"  ✅ Moved '{name}' to {parent_name}")

# Update Person's children to only include actual people
actual_person_ids = []
for name in actual_people:
    person = db.tag_concepts_v2.find_one({"display_name": name})
    if person:
        actual_person_ids.append(person['_id'])

db.tag_concepts_v2.update_one(
    {"_id": person_entity['_id']},
    {"$set": {"children": actual_person_ids}}
)

print(f"\n✅ Fixed {fixed_count} misplaced concepts")
print(f"✅ Person entity now has {len(actual_person_ids)} actual people")
