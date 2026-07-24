#!/usr/bin/env python3
"""Find duplicate concept IDs in hierarchy"""

import requests
import json

# Get hierarchy facets
response = requests.get("http://localhost:8000/api/tweets/hierarchy-facets")
data = response.json()

# Track all concept IDs and their paths
concept_paths = {}

def traverse_hierarchy(concepts, parent_path=""):
    """Recursively traverse hierarchy and track concept IDs"""
    for concept in concepts:
        concept_id = concept.get('concept_id')
        display_name = concept.get('display_name', 'Unknown')
        current_path = f"{parent_path}/{display_name}" if parent_path else display_name
        
        if concept_id:
            if concept_id not in concept_paths:
                concept_paths[concept_id] = []
            concept_paths[concept_id].append(current_path)
        
        # Traverse children
        if 'children' in concept and concept['children']:
            traverse_hierarchy(concept['children'], current_path)

# Start traversal
if 'concepts' in data:
    traverse_hierarchy(data['concepts'])

# Find duplicates
print("=" * 60)
print("DUPLICATE CONCEPT IDS IN HIERARCHY")
print("=" * 60)

duplicates_found = False
for concept_id, paths in concept_paths.items():
    if len(paths) > 1:
        duplicates_found = True
        print(f"\n❌ Concept ID: {concept_id}")
        print(f"   Appears {len(paths)} times:")
        for path in paths:
            print(f"   - {path}")

if not duplicates_found:
    print("\n✅ No duplicate concept IDs found in hierarchy")

print("\n" + "=" * 60)
print(f"Total unique concepts: {len(concept_paths)}")
print(f"Total concept appearances: {sum(len(paths) for paths in concept_paths.values())}")
print("=" * 60)