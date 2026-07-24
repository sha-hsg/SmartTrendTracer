#!/usr/bin/env python3
"""
Final fix: Move non-person concepts out of Person entity, keep only actual people
"""

from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

client = MongoClient('mongodb://localhost:27017/')
db = client.smarttrendtracer

print("=" * 60)
print("FINAL FIX: CLEAN UP PERSON ENTITY")
print("=" * 60)

# Get Person entity
person_entity = db.tag_concepts_v2.find_one({"slug": "person", "entity_type": "person"})
if not person_entity:
    print("❌ Person entity not found!")
    exit(1)

print(f"Person entity: {person_entity['_id']}")

# Define actual people (be conservative, only clear people)
actual_people = {
    "Christopher Manning", "Chris Potts", "Ethan Mollick", 
    "François Chollet", "Jack Clark", "Sam Altman",
    "Dario Amodei", "Sebastian Raschka", "Andrej Karpathy",
    "Gary Marcus"
}

# Get all concepts currently under Person
all_under_person = list(db.tag_concepts_v2.find({"parents": person_entity['_id']}))

print(f"\nCurrently {len(all_under_person)} concepts under Person entity")

# Find proper parent categories
ai_fundamentals = db.tag_concepts_v2.find_one({"display_name": "AI/ML Fundamentals"})
techniques = db.tag_concepts_v2.find_one({"display_name": "Techniques & Methods"})
applications = db.tag_concepts_v2.find_one({"display_name": "Applications & Domains"})
data_datasets = db.tag_concepts_v2.find_one({"display_name": "Data & Datasets"})
research_dev = db.tag_concepts_v2.find_one({"display_name": "Research & Development"})
tools_infra = db.tag_concepts_v2.find_one({"display_name": "Tools & Infrastructure"})
ethics_society = db.tag_concepts_v2.find_one({"display_name": "Ethics & Society"})

# Map non-person concepts to correct parents
concept_mapping = {
    # Methods and techniques
    "Attention Mechanisms": techniques['_id'] if techniques else None,
    "Self Attention": techniques['_id'] if techniques else None,
    "Linear Attention": techniques['_id'] if techniques else None,
    "Causal Attention": techniques['_id'] if techniques else None,
    "Transformer Attribution": techniques['_id'] if techniques else None,
    "Description Logic": techniques['_id'] if techniques else None,
    "Probing Classifiers": techniques['_id'] if techniques else None,
    "Classification Finetuning": techniques['_id'] if techniques else None,
    
    # Data concepts
    "Data Filtering": data_datasets['_id'] if data_datasets else None,
    "Data Sharing": data_datasets['_id'] if data_datasets else None,
    "Data Heterogeneity": data_datasets['_id'] if data_datasets else None,
    "Knowledge Graph": data_datasets['_id'] if data_datasets else None,
    "Commonsense Knowledge": data_datasets['_id'] if data_datasets else None,
    
    # Applications
    "Image Processing": applications['_id'] if applications else None,
    "Image Matching": applications['_id'] if applications else None,
    "Image Upscaling": applications['_id'] if applications else None,
    "Entity Resolution": applications['_id'] if applications else None,
    "Content Classifier": applications['_id'] if applications else None,
    "Multilingual Speech": applications['_id'] if applications else None,
    "Earth Observation": applications['_id'] if applications else None,
    "Gaming Scenarios": applications['_id'] if applications else None,
    "Spatial Reasoning": applications['_id'] if applications else None,
    
    # Research concepts
    "Research Entities": None,  # This is a root category itself
    "Named Entities": None,  # This is a root category itself
    "Content Types": None,  # This is a root category itself
    "Autonomous Agents": ai_fundamentals['_id'] if ai_fundamentals else None,
    "Autonomous Research": research_dev['_id'] if research_dev else None,
    "Empirical Evaluation": research_dev['_id'] if research_dev else None,
    "Literature Reviews": research_dev['_id'] if research_dev else None,
    "Research Engineer": research_dev['_id'] if research_dev else None,
    
    # Privacy and ethics
    "Privacy Concerns": ethics_society['_id'] if ethics_society else None,
    "Privacy Settings": ethics_society['_id'] if ethics_society else None,
    "Cbrn Filtering": ethics_society['_id'] if ethics_society else None,
    "Hallucination Mitigation": techniques['_id'] if techniques else None,
    
    # Other
    "Google Gemini": ai_fundamentals['_id'] if ai_fundamentals else None,  # Should be under models
    "Feature Requests": tools_infra['_id'] if tools_infra else None,
    "Performance Metrics": research_dev['_id'] if research_dev else None,
    "Performance Optimization": techniques['_id'] if techniques else None,
    "Diminishing Returns": research_dev['_id'] if research_dev else None,
    "Long Context": techniques['_id'] if techniques else None,
    "Power Users": applications['_id'] if applications else None,
    "Seed Oss": tools_infra['_id'] if tools_infra else None,
    "Semantic Representation": ai_fundamentals['_id'] if ai_fundamentals else None,
}

# Process each concept under Person
people_kept = []
concepts_moved = []
concepts_to_remove = []

for concept in all_under_person:
    name = concept['display_name']
    
    if name in actual_people:
        # Keep under Person, ensure entity_type is person
        db.tag_concepts_v2.update_one(
            {"_id": concept['_id']},
            {"$set": {"entity_type": "person"}}
        )
        people_kept.append(name)
    elif name in concept_mapping:
        # Move to correct parent
        new_parent = concept_mapping[name]
        if new_parent:
            db.tag_concepts_v2.update_one(
                {"_id": concept['_id']},
                {"$set": {
                    "parents": [new_parent],
                    "entity_type": "concept"
                }}
            )
            concepts_moved.append(name)
        else:
            # Make it a root concept or find appropriate parent
            db.tag_concepts_v2.update_one(
                {"_id": concept['_id']},
                {"$set": {
                    "parents": [],
                    "entity_type": "concept"
                }}
            )
            concepts_to_remove.append(name)
    else:
        # Unknown concept - analyze and place appropriately
        # For now, move to AI/ML Fundamentals if unclear
        if ai_fundamentals:
            db.tag_concepts_v2.update_one(
                {"_id": concept['_id']},
                {"$set": {
                    "parents": [ai_fundamentals['_id']],
                    "entity_type": "concept"
                }}
            )
            concepts_moved.append(f"{name} (default)")

# Update Person entity's children
final_people = list(db.tag_concepts_v2.find({
    "parents": person_entity['_id']
}).distinct('_id'))

db.tag_concepts_v2.update_one(
    {"_id": person_entity['_id']},
    {"$set": {"children": final_people}}
)

print("\n" + "=" * 60)
print("RESULTS:")
print(f"  People kept under Person: {len(people_kept)}")
for p in sorted(people_kept):
    print(f"    ✅ {p}")
print(f"\n  Concepts moved to proper categories: {len(concepts_moved)}")
print(f"  Concepts made root: {len(concepts_to_remove)}")
print(f"\n  Final people count under Person: {len(final_people)}")
print("=" * 60)