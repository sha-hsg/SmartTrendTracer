#!/usr/bin/env python3
"""
Find all people concepts in the database, regardless of their current classification
"""

from pymongo import MongoClient
from bson import ObjectId

client = MongoClient('mongodb://localhost:27017/')
db = client.smarttrendtracer

print("=" * 60)
print("SEARCHING FOR ALL PEOPLE CONCEPTS")
print("=" * 60)

# Known people names to search for
known_people = [
    "Sam Altman", "Dario Amodei", "Sebastian Raschka", "Andrej Karpathy",
    "Gary Marcus", "Nathan Lambert", "Yann LeCun", "Geoffrey Hinton",
    "Yoshua Bengio", "Andrew Ng", "Ian Goodfellow", "Demis Hassabis",
    "Greg Brockman", "Ilya Sutskever", "Elon Musk", "Bill Gates",
    "Mark Zuckerberg", "Satya Nadella", "Sundar Pichai", "Tim Cook",
    "Jeff Bezos", "Jensen Huang", "Christopher Manning", "Chris Potts",
    "Ethan Mollick", "François Chollet", "Fei-Fei Li", "Chris Manning",
    "Christopher D. Manning", "Michael Jordan", "Peter Norvig",
    "Stuart Russell", "Judea Pearl", "Max Tegmark", "Nick Bostrom",
    "Eliezer Yudkowsky", "Connor Leahy", "Leopold Aschenbrenner",
    "Emmett Shear", "Mira Murati", "Adam D'Angelo", "Wojciech Zaremba",
    "Alec Radford", "Rewon Child", "Lilian Weng", "John Schulman",
    "Dario Amodei", "Daniela Amodei", "Tom Brown", "Jared Kaplan",
    "Sam McCandlish", "Chris Olah", "Catherine Olsson", "Jack Clark",
    "Miles Brundage", "Jade Leung", "Allan Dafoe", "Rohin Shah",
    "Jan Leike", "Paul Christiano", "Buck Shlegeris", "Nate Soares",
    "Eliezer Yudkowsky", "Rob Miles", "Robert Miles", "Connor Leahy",
    "Leopold Aschenbrenner", "Dan Hendrycks", "Jacob Steinhardt"
]

# Search patterns for people (common name patterns)
people_patterns = [
    # Full names with common patterns
    {"display_name": {"$regex": "^[A-Z][a-z]+ [A-Z][a-z]+$"}},  # John Doe
    {"display_name": {"$regex": "^[A-Z][a-z]+ [A-Z]\\. [A-Z][a-z]+$"}},  # John D. Doe
    {"display_name": {"$regex": "^[A-Z][a-z]+ [A-Z][a-z]+ [A-Z][a-z]+$"}},  # John David Doe
]

print("\n1. SEARCHING FOR KNOWN PEOPLE NAMES...")
print("-" * 40)

found_people = {}
person_entity = db.tag_concepts_v2.find_one({"display_name": "Person", "entity_type": "person"})

for name in known_people:
    # Search case-insensitive
    concept = db.tag_concepts_v2.find_one({
        "display_name": {"$regex": f"^{name}$", "$options": "i"}
    })
    
    if concept:
        entity_type = concept.get('entity_type', 'none')
        parent_names = []
        for parent_id in concept.get('parents', []):
            parent = db.tag_concepts_v2.find_one({"_id": parent_id})
            if parent:
                parent_names.append(parent['display_name'])
        
        usage = concept.get('usage_count', 0)
        found_people[name] = {
            'id': concept['_id'],
            'slug': concept.get('slug'),
            'entity_type': entity_type,
            'parents': parent_names,
            'usage_count': usage,
            'correct': entity_type == 'person' and person_entity and person_entity['_id'] in concept.get('parents', [])
        }

# Sort by usage count
sorted_people = sorted(found_people.items(), key=lambda x: x[1]['usage_count'], reverse=True)

print(f"\nFound {len(found_people)} known people in database:")
for name, info in sorted_people:
    status = "✅" if info['correct'] else "❌"
    print(f"{status} {name}")
    print(f"   Entity type: {info['entity_type']}")
    print(f"   Parents: {', '.join(info['parents']) if info['parents'] else 'None'}")
    print(f"   Usage: {info['usage_count']} times")
    print()

print("\n2. SEARCHING BY NAME PATTERNS...")
print("-" * 40)

pattern_matches = []
for pattern in people_patterns:
    matches = db.tag_concepts_v2.find(pattern).limit(50)
    for match in matches:
        name = match['display_name']
        # Filter out obvious non-people
        if not any(word in name.lower() for word in [
            'model', 'system', 'method', 'algorithm', 'architecture', 
            'benchmark', 'dataset', 'framework', 'api', 'tool', 
            'platform', 'service', 'paper', 'report', 'study',
            'technique', 'approach', 'analysis', 'evaluation',
            'processing', 'generation', 'learning', 'network'
        ]):
            if name not in found_people:
                entity_type = match.get('entity_type', 'none')
                usage = match.get('usage_count', 0)
                if usage > 0:  # Only show if actually used
                    pattern_matches.append({
                        'name': name,
                        'entity_type': entity_type,
                        'usage_count': usage
                    })

pattern_matches.sort(key=lambda x: x['usage_count'], reverse=True)
if pattern_matches:
    print(f"\nFound {len(pattern_matches)} potential people by name pattern (with usage):")
    for match in pattern_matches[:20]:  # Show top 20
        print(f"  • {match['name']} (type: {match['entity_type']}, usage: {match['usage_count']})")

print("\n3. CURRENT PERSON ENTITY STATUS...")
print("-" * 40)

if person_entity:
    # Get all concepts currently under Person
    people_under_person = list(db.tag_concepts_v2.find({
        "parents": person_entity['_id']
    }))
    
    print(f"Person entity has {len(people_under_person)} children:")
    for person in people_under_person:
        usage = person.get('usage_count', 0)
        print(f"  ✅ {person['display_name']} (usage: {usage})")
else:
    print("❌ Person entity not found!")

print("\n4. INCORRECTLY CLASSIFIED PEOPLE...")
print("-" * 40)

# Find people who should be under Person but aren't
needs_fixing = []
for name, info in found_people.items():
    if not info['correct'] and info['usage_count'] > 0:
        needs_fixing.append((name, info))

if needs_fixing:
    print(f"Found {len(needs_fixing)} people that need to be moved to Person entity:")
    for name, info in needs_fixing:
        print(f"  ❌ {name}")
        print(f"     Current entity_type: {info['entity_type']}")
        print(f"     Current parents: {', '.join(info['parents'])}")
        print(f"     Usage: {info['usage_count']} times")
else:
    print("All found people are correctly classified!")

print("\n" + "=" * 60)
print("SUMMARY:")
print(f"  Known people found: {len(found_people)}")
print(f"  Correctly classified: {sum(1 for _, info in found_people.items() if info['correct'])}")
print(f"  Need fixing: {len(needs_fixing)}")
print(f"  Currently under Person entity: {len(people_under_person) if person_entity else 0}")
print("=" * 60)