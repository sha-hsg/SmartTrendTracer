#!/usr/bin/env python3
"""
Integrate top_level.json entity types into MongoDB concept hierarchy
and fix misplaced concepts
"""
import json
from pymongo import MongoClient
from datetime import datetime

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client.smarttrendtracer
concepts_col = db.tag_concepts_v2

def load_top_level_schema():
    """Load the entity type schema from top_level.json"""
    with open("top_level.json", "r") as f:
        return json.load(f)

def create_entity_type_concepts():
    """Create root concepts for entity types if they don't exist"""
    schema = load_top_level_schema()
    
    # Create main entity type categories as root concepts
    entity_type_roots = []
    
    for category_key, category in schema["entity_types"].items():
        # Check if this category concept exists
        existing = concepts_col.find_one({"slug": category_key})
        
        if not existing:
            # Create the category concept
            concept = {
                "id": f"c_et_{category_key}",
                "_id": f"c_et_{category_key}",
                "slug": category_key,
                "display_name": category["display_name"],
                "description": category["description"],
                "entity_type": "category",
                "parents": [],  # Root level
                "children": [],
                "level": 0,
                "icon": category.get("icon", "📂"),
                "color": category.get("color", "#6B7280"),
                "usage_count": 0,
                "status": "active",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            concepts_col.insert_one(concept)
            print(f"✅ Created entity type category: {category['display_name']}")
            entity_type_roots.append(concept["id"])
        else:
            print(f"ℹ️  Entity type category exists: {category['display_name']}")
            entity_type_roots.append(existing["id"])
        
        # Create subcategory concepts
        if "children" in category:
            for subcat_key, subcat in category["children"].items():
                existing_sub = concepts_col.find_one({"slug": subcat_key})
                
                if not existing_sub:
                    sub_concept = {
                        "id": f"c_et_{subcat_key}",
                        "_id": f"c_et_{subcat_key}",
                        "slug": subcat_key,
                        "display_name": subcat["display_name"],
                        "description": subcat["description"],
                        "entity_type": subcat_key,  # This IS the entity type
                        "parents": [f"c_et_{category_key}"],
                        "children": [],
                        "level": 1,
                        "icon": subcat.get("icon", "🏷️"),
                        "color": subcat.get("color", "#6B7280"),
                        "usage_count": 0,
                        "status": "active",
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                    concepts_col.insert_one(sub_concept)
                    print(f"  ✅ Created entity type: {subcat['display_name']}")
                    
                    # Update parent's children
                    concepts_col.update_one(
                        {"id": f"c_et_{category_key}"},
                        {"$addToSet": {"children": sub_concept["id"]}}
                    )
                else:
                    print(f"  ℹ️  Entity type exists: {subcat['display_name']}")
    
    return entity_type_roots

def fix_misplaced_concepts():
    """Fix concepts that are in wrong places"""
    fixes = []
    
    # 1. Fix location concepts (India, Silicon Valley)
    location_concepts = [
        {"slug": "c_location_india", "name": "India"},
        {"slug": "c_location_silicon_valley", "name": "Silicon Valley"}
    ]
    
    for loc in location_concepts:
        concept = concepts_col.find_one({"id": loc["slug"]})
        if concept:
            # Move under Location entity type
            concepts_col.update_one(
                {"id": loc["slug"]},
                {
                    "$set": {
                        "parents": ["c_et_location"],
                        "entity_type": "location",
                        "icon": "📍",
                        "color": "#EF4444",
                        "level": 2
                    }
                }
            )
            
            # Add to Location's children
            concepts_col.update_one(
                {"id": "c_et_location"},
                {"$addToSet": {"children": loc["slug"]}}
            )
            
            fixes.append(f"Moved {loc['name']} under Location entity type")
    
    # 2. Fix person entities (Sam Altman, Dario Amodei, etc.)
    people = [
        "Sam Altman", "Dario Amodei", "Andrej Karpathy", "Yann LeCun",
        "Geoffrey Hinton", "Ian Goodfellow", "Ethan Mollick", "Gary Marcus",
        "Ilya Sutskever", "Greg Brockman", "Demis Hassabis", "Mustafa Suleyman"
    ]
    
    for person_name in people:
        # Find by display_name
        concept = concepts_col.find_one({"display_name": person_name})
        if concept:
            # Update entity_type and visual properties
            concepts_col.update_one(
                {"id": concept["id"]},
                {
                    "$set": {
                        "entity_type": "person",
                        "icon": "👤",
                        "color": "#10B981"
                    },
                    "$addToSet": {"parents": "c_et_person"}  # Add Person entity type as parent
                }
            )
            
            # Add to Person entity type's children
            concepts_col.update_one(
                {"id": "c_et_person"},
                {"$addToSet": {"children": concept["id"]}}
            )
            
            fixes.append(f"Set {person_name} as entity_type: person")
    
    # 3. Fix Knowledge Graphs to have multiple parents
    kg_concept = concepts_col.find_one({"slug": "c_kg"})
    if kg_concept:
        # Should be under both AI/ML Fundamentals AND Data and Datasets
        concepts_col.update_one(
            {"id": "c_kg"},
            {
                "$set": {
                    "parents": ["c_fundamentals", "c_data"],
                    "display_name": "Knowledge Graphs"
                }
            }
        )
        
        # Ensure it's in both parents' children
        concepts_col.update_one(
            {"id": "c_fundamentals"},
            {"$addToSet": {"children": "c_kg"}}
        )
        concepts_col.update_one(
            {"id": "c_data"},
            {"$addToSet": {"children": "c_kg"}}
        )
        
        fixes.append("Knowledge Graphs now has multiple parents: AI/ML Fundamentals AND Data and Datasets")
    
    # 4. Fix Semantic Web to have multiple parents
    sw_concept = concepts_col.find_one({"slug": "c_semantic_web"})
    if sw_concept:
        concepts_col.update_one(
            {"id": "c_semantic_web"},
            {
                "$set": {
                    "parents": ["c_fundamentals", "c_data"]
                }
            }
        )
        
        # Ensure it's in both parents' children
        concepts_col.update_one(
            {"id": "c_fundamentals"},
            {"$addToSet": {"children": "c_semantic_web"}}
        )
        concepts_col.update_one(
            {"id": "c_data"},
            {"$addToSet": {"children": "c_semantic_web"}}
        )
        
        fixes.append("Semantic Web now has multiple parents: AI/ML Fundamentals AND Data and Datasets")
    
    # 5. Set entity types for organizations
    orgs = [
        {"name": "OpenAI", "id": "c_org_openai"},
        {"name": "Anthropic", "id": "c_org_anthropic"},
        {"name": "Google", "id": "c_org_google"},
        {"name": "Meta", "id": "c_org_meta"},
        {"name": "Microsoft", "id": "c_org_microsoft"},
        {"name": "Nvidia", "id": "c_org_nvidia"},
        {"name": "Hugging Face", "id": "c_org_huggingface"}
    ]
    
    for org in orgs:
        concept = concepts_col.find_one({"id": org["id"]})
        if concept:
            concepts_col.update_one(
                {"id": org["id"]},
                {
                    "$set": {
                        "entity_type": "organisation",
                        "icon": "🏢",
                        "color": "#8B5CF6"
                    },
                    "$addToSet": {"parents": "c_et_organisation"}
                }
            )
            
            # Add to Organisation entity type's children
            concepts_col.update_one(
                {"id": "c_et_organisation"},
                {"$addToSet": {"children": org["id"]}}
            )
            
            fixes.append(f"Set {org['name']} as entity_type: organisation")
    
    return fixes

def verify_hierarchy():
    """Verify the updated hierarchy"""
    print("\n" + "="*60)
    print("VERIFICATION")
    print("="*60)
    
    # Check root concepts
    roots = list(concepts_col.find({"parents": []}))
    print(f"\nRoot concepts ({len(roots)}):")
    for root in roots:
        children_count = len(root.get("children", []))
        print(f"  - {root['display_name']} ({root['id']}) - {children_count} children")
    
    # Check multi-parent concepts
    multi_parent = list(concepts_col.find({"parents": {"$exists": True, "$not": {"$size": 0}, "$not": {"$size": 1}}}))
    print(f"\nConcepts with multiple parents ({len(multi_parent)}):")
    for concept in multi_parent[:10]:
        parent_names = []
        for pid in concept["parents"]:
            parent = concepts_col.find_one({"id": pid})
            if parent:
                parent_names.append(parent["display_name"])
        print(f"  - {concept['display_name']}: {parent_names}")
    
    # Check entity types
    entity_types = {}
    for concept in concepts_col.find({"entity_type": {"$exists": True, "$ne": None}}):
        et = concept.get("entity_type")
        if et not in entity_types:
            entity_types[et] = 0
        entity_types[et] += 1
    
    print(f"\nEntity type distribution:")
    for et, count in sorted(entity_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {et}: {count} concepts")

def main():
    print("="*60)
    print("INTEGRATING ENTITY TYPES AND FIXING HIERARCHY")
    print("="*60)
    
    # Step 1: Create entity type concepts
    print("\nStep 1: Creating entity type hierarchy...")
    entity_roots = create_entity_type_concepts()
    
    # Step 2: Fix misplaced concepts
    print("\nStep 2: Fixing misplaced concepts...")
    fixes = fix_misplaced_concepts()
    for fix in fixes:
        print(f"  ✅ {fix}")
    
    # Step 3: Verify
    verify_hierarchy()
    
    print("\n" + "="*60)
    print("✅ INTEGRATION COMPLETE!")
    print("="*60)

if __name__ == "__main__":
    main()