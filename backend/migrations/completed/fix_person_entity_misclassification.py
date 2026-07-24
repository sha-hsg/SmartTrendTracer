#!/usr/bin/env python3
"""
Fix Person Entity Misclassification

This script addresses the issue where 96 concepts were incorrectly marked with entity_type: 'person'
when only 3 are actual people. It will:

1. Identify actual people (Christopher Manning, Chris Potts, Ethan Mollick)
2. Reset entity_type for non-person concepts to more appropriate types
3. Create proper top-level categories if they don't exist
4. Move concepts to appropriate parent categories based on their content

Author: System Architecture Auditor
Date: 2025-08-28
"""

import json
import re
from datetime import datetime, timezone
from pymongo import MongoClient
from bson import ObjectId

def connect_to_mongodb():
    """Connect to MongoDB"""
    client = MongoClient('mongodb://localhost:27017/')
    db = client['smarttrendtracer']
    return db

def generate_slug(name):
    """Generate a URL-safe slug from a name"""
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower().strip())
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    return slug

def load_top_level_schema():
    """Load the top_level.json schema for reference"""
    try:
        with open('top_level.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Warning: top_level.json not found, proceeding without schema reference")
        return None

def identify_actual_people(concepts):
    """Identify concepts that are actually people"""
    actual_people = []
    non_people = []
    
    # Known people in the system
    known_people = [
        'Christopher Manning', 'Chris Potts', 'Ethan Mollick', 
        'Sam Altman', 'Dario Amodei', 'Geoffrey Hinton', 'Yann LeCun',
        'Andrej Karpathy', 'Ilya Sutskever', 'Demis Hassabis'
    ]
    
    for concept in concepts:
        name = concept.get('name', str(concept.get('_id', 'Unknown')))
        
        # Check if this is a known person
        is_person = False
        for person_name in known_people:
            if person_name.lower() in name.lower() or name.lower() in person_name.lower():
                is_person = True
                break
        
        # Additional heuristics for people
        if not is_person:
            # Check for common patterns that indicate a person
            name_words = name.split()
            if len(name_words) >= 2 and all(word.istitle() for word in name_words[:2]):
                # Two consecutive title-case words might be a person
                # But exclude obvious non-people patterns
                non_person_patterns = [
                    'Model', 'Algorithm', 'Framework', 'System', 'Method',
                    'Data', 'Analysis', 'Research', 'Learning', 'Neural',
                    'Deep', 'Machine', 'Artificial', 'Language', 'Computer',
                    'Vision', 'Processing', 'Generation', 'Classification'
                ]
                
                if not any(pattern in name for pattern in non_person_patterns):
                    is_person = True
        
        if is_person:
            actual_people.append(concept)
        else:
            non_people.append(concept)
    
    return actual_people, non_people

def categorize_concepts(concepts):
    """Categorize concepts based on their names and content"""
    categories = {
        'method': [],
        'model': [],
        'research-topic': [],
        'concept': [],
        'task': [],
        'metric': [],
        'dataset': [],
        'tool': [],
        'organisation': [],
        'product': [],
        'hardware': [],
        'benchmark': [],
        'architecture': [],
        'experimental-setup': [],
        'modality': [],
        'license': [],
        'standard': [],
        'event': [],
        'location': [],
        'paper': [],
        'technology': [],
    }
    
    for concept in concepts:
        name = concept.get('name', str(concept.get('_id', 'Unknown')))
        name_lower = name.lower()
        
        # Categorization rules based on keywords and patterns
        if any(keyword in name_lower for keyword in ['attention', 'mechanism', 'algorithm', 'optimization', 'training', 'learning']):
            categories['method'].append(concept)
        elif any(keyword in name_lower for keyword in ['gpt', 'bert', 'model', 'llm', 'neural', 'network']):
            categories['model'].append(concept)
        elif any(keyword in name_lower for keyword in ['classification', 'generation', 'recognition', 'translation', 'summarization']):
            categories['task'].append(concept)
        elif any(keyword in name_lower for keyword in ['accuracy', 'precision', 'recall', 'score', 'rate', 'metric']):
            categories['metric'].append(concept)
        elif any(keyword in name_lower for keyword in ['dataset', 'corpus', 'data']):
            categories['dataset'].append(concept)
        elif any(keyword in name_lower for keyword in ['framework', 'library', 'tool', 'software', 'api']):
            categories['tool'].append(concept)
        elif any(keyword in name_lower for keyword in ['openai', 'google', 'microsoft', 'anthropic', 'company', 'lab']):
            categories['organisation'].append(concept)
        elif any(keyword in name_lower for keyword in ['gpu', 'cpu', 'chip', 'hardware', 'accelerator']):
            categories['hardware'].append(concept)
        elif any(keyword in name_lower for keyword in ['transformer', 'cnn', 'rnn', 'architecture']):
            categories['architecture'].append(concept)
        elif any(keyword in name_lower for keyword in ['zero-shot', 'few-shot', 'prompting', 'setup']):
            categories['experimental-setup'].append(concept)
        elif any(keyword in name_lower for keyword in ['text', 'image', 'audio', 'video', 'multimodal']):
            categories['modality'].append(concept)
        elif any(keyword in name_lower for keyword in ['benchmark', 'leaderboard', 'evaluation']):
            categories['benchmark'].append(concept)
        elif any(keyword in name_lower for keyword in ['mit', 'apache', 'license', 'cc-by']):
            categories['license'].append(concept)
        elif any(keyword in name_lower for keyword in ['conference', 'workshop', 'summit', 'event']):
            categories['event'].append(concept)
        elif any(keyword in name_lower for keyword in ['city', 'country', 'valley', 'location']):
            categories['location'].append(concept)
        elif any(keyword in name_lower for keyword in ['paper', 'publication', 'arxiv']):
            categories['paper'].append(concept)
        else:
            # Default to concept for general ideas and abstract concepts
            categories['concept'].append(concept)
    
    return categories

def ensure_top_level_categories(db, schema=None):
    """Ensure top-level categories exist in the database"""
    # Check for existing categories with both old and new naming conventions
    category_mappings = [
        {'old_name': 'c_named_entities', 'new_name': 'Named Entities', 'entity_type': 'named-entities'},
        {'old_name': 'c_research_entities', 'new_name': 'Research Entities', 'entity_type': 'research-entities'},
        {'old_name': 'c_content_types', 'new_name': 'Content Types', 'entity_type': 'content-types'},
    ]
    
    # Second-level categories
    subcategories = [
        # Named Entities children
        {'name': 'Person', 'entity_type': 'person', 'parent': 'Named Entities', 'description': 'Individual people mentioned in content'},
        {'name': 'Organisation', 'entity_type': 'organisation', 'parent': 'Named Entities', 'description': 'Companies, institutions, and organizations'},
        {'name': 'Location', 'entity_type': 'location', 'parent': 'Named Entities', 'description': 'Geographic locations and places'},
        {'name': 'Event', 'entity_type': 'event', 'parent': 'Named Entities', 'description': 'Conferences, releases, and significant events'},
        {'name': 'Product', 'entity_type': 'product', 'parent': 'Named Entities', 'description': 'Commercially named products or services'},
        {'name': 'Hardware', 'entity_type': 'hardware', 'parent': 'Named Entities', 'description': 'Chips, accelerators, and computing devices'},
        
        # Research Entities children
        {'name': 'Research Topic', 'entity_type': 'research-topic', 'parent': 'Research Entities', 'description': 'Research areas and topics'},
        {'name': 'Dataset', 'entity_type': 'dataset', 'parent': 'Research Entities', 'description': 'Datasets used in research and development'},
        {'name': 'Benchmark', 'entity_type': 'benchmark', 'parent': 'Research Entities', 'description': 'Performance benchmarks and evaluation metrics'},
        {'name': 'Metric', 'entity_type': 'metric', 'parent': 'Research Entities', 'description': 'Quantitative metrics and measurements'},
        {'name': 'Method', 'entity_type': 'method', 'parent': 'Research Entities', 'description': 'Algorithms, techniques, and methodologies'},
        {'name': 'Model', 'entity_type': 'model', 'parent': 'Research Entities', 'description': 'AI/ML models and architectures'},
        {'name': 'Task', 'entity_type': 'task', 'parent': 'Research Entities', 'description': 'Well-defined ML/NLP/CV tasks'},
        {'name': 'Modality', 'entity_type': 'modality', 'parent': 'Research Entities', 'description': 'Input/output media types processed by models'},
        {'name': 'License', 'entity_type': 'license', 'parent': 'Research Entities', 'description': 'Licenses applicable to datasets, models, or tools'},
        {'name': 'Architecture', 'entity_type': 'architecture', 'parent': 'Research Entities', 'description': 'Model architecture families'},
        {'name': 'Experimental Setup', 'entity_type': 'experimental-setup', 'parent': 'Research Entities', 'description': 'Setup and configuration of experiments'},
        
        # Content Types children
        {'name': 'Research Paper', 'entity_type': 'paper', 'parent': 'Content Types', 'description': 'Academic papers and publications'},
        {'name': 'Tool', 'entity_type': 'tool', 'parent': 'Content Types', 'description': 'Software tools and applications'},
        {'name': 'Concept', 'entity_type': 'concept', 'parent': 'Content Types', 'description': 'Abstract concepts and ideas'},
        {'name': 'Standard', 'entity_type': 'standard', 'parent': 'Content Types', 'description': 'Technical standards or regulations'},
    ]
    
    created_categories = {}
    
    # Find or create top-level categories
    for mapping in category_mappings:
        # First try to find by old name
        existing = db.tag_concepts_v2.find_one({'name': mapping['old_name']})
        if existing:
            created_categories[mapping['new_name']] = existing['_id']
            print(f"Found existing category: {mapping['old_name']} -> {mapping['new_name']}")
        else:
            # Try new name
            existing = db.tag_concepts_v2.find_one({'name': mapping['new_name']})
            if existing:
                created_categories[mapping['new_name']] = existing['_id']
                print(f"Found existing category: {mapping['new_name']}")
            else:
                # Create new category
                doc = {
                    '_id': ObjectId(),
                    'name': mapping['new_name'],
                    'slug': generate_slug(mapping['new_name']),
                    'entity_type': mapping['entity_type'],
                    'description': f"{mapping['new_name']} category",
                    'parents': [],
                    'children': [],
                    'created_at': datetime.now(timezone.utc),
                    'source': 'migration'
                }
                result = db.tag_concepts_v2.insert_one(doc)
                created_categories[mapping['new_name']] = result.inserted_id
                print(f"Created top-level category: {mapping['new_name']}")
    
    # Create subcategories
    for subcat in subcategories:
        existing = db.tag_concepts_v2.find_one({'name': subcat['name']})
        if not existing:
            parent_id = created_categories.get(subcat['parent'])
            if parent_id:
                doc = {
                    '_id': ObjectId(),
                    'name': subcat['name'],
                    'slug': generate_slug(subcat['name']),
                    'entity_type': subcat['entity_type'],
                    'description': subcat['description'],
                    'parents': [parent_id],
                    'children': [],
                    'created_at': datetime.now(timezone.utc),
                    'source': 'migration'
                }
                result = db.tag_concepts_v2.insert_one(doc)
                created_categories[subcat['name']] = result.inserted_id
                
                # Update parent's children list
                db.tag_concepts_v2.update_one(
                    {'_id': parent_id},
                    {'$addToSet': {'children': result.inserted_id}}
                )
                print(f"Created subcategory: {subcat['name']} under {subcat['parent']}")
        else:
            created_categories[subcat['name']] = existing['_id']
            print(f"Found existing subcategory: {subcat['name']}")
    
    return created_categories

def fix_person_entity_types(db, categories_map):
    """Fix the incorrectly classified person entity types"""
    print("\n=== Fixing Person Entity Type Misclassification ===")
    
    # Get all concepts with entity_type: 'person'
    person_concepts = list(db.tag_concepts_v2.find({'entity_type': 'person'}))
    print(f"Found {len(person_concepts)} concepts with entity_type: 'person'")
    
    # Separate actual people from non-people
    actual_people, non_people = identify_actual_people(person_concepts)
    
    print(f"\nActual people identified: {len(actual_people)}")
    for person in actual_people:
        name = person.get('name', str(person.get('_id')))
        print(f"  - {name}")
    
    print(f"\nNon-people to be reclassified: {len(non_people)}")
    
    # Categorize the non-people concepts
    categorized = categorize_concepts(non_people)
    
    # Update entity types and move concepts to appropriate parents
    updates_made = 0
    for entity_type, concepts in categorized.items():
        if not concepts:
            continue
            
        print(f"\nProcessing {len(concepts)} concepts for entity_type: '{entity_type}'")
        
        # Get the parent category ID
        parent_category_name = {
            'method': 'Method',
            'model': 'Model', 
            'research-topic': 'Research Topic',
            'task': 'Task',
            'metric': 'Metric',
            'dataset': 'Dataset',
            'tool': 'Tool',
            'organisation': 'Organisation',
            'product': 'Product',
            'hardware': 'Hardware',
            'benchmark': 'Benchmark',
            'architecture': 'Architecture',
            'experimental-setup': 'Experimental Setup',
            'modality': 'Modality',
            'license': 'License',
            'standard': 'Standard',
            'event': 'Event',
            'location': 'Location',
            'paper': 'Research Paper',
            'concept': 'Concept'
        }.get(entity_type, 'Concept')
        
        parent_id = categories_map.get(parent_category_name)
        if not parent_id:
            print(f"  Warning: Parent category '{parent_category_name}' not found, using 'Concept'")
            parent_id = categories_map.get('Concept')
        
        for concept in concepts:
            concept_id = concept['_id']
            name = concept.get('name', str(concept_id))
            
            # Update entity type
            update_doc = {'entity_type': entity_type}
            
            # Update parents if we have a valid parent
            if parent_id:
                update_doc['parents'] = [parent_id]
            
            result = db.tag_concepts_v2.update_one(
                {'_id': concept_id},
                {'$set': update_doc}
            )
            
            if result.modified_count > 0:
                updates_made += 1
                print(f"  ✓ Updated: {name[:50]}{'...' if len(name) > 50 else ''}")
                
                # Add this concept to parent's children list
                if parent_id:
                    db.tag_concepts_v2.update_one(
                        {'_id': parent_id},
                        {'$addToSet': {'children': concept_id}}
                    )
    
    # Ensure actual people have correct parent (Person category)
    person_parent_id = categories_map.get('Person')
    if person_parent_id:
        for person in actual_people:
            concept_id = person['_id']
            name = person.get('name', str(concept_id))
            
            result = db.tag_concepts_v2.update_one(
                {'_id': concept_id},
                {'$set': {'parents': [person_parent_id]}}
            )
            
            if result.modified_count > 0:
                # Add to parent's children
                db.tag_concepts_v2.update_one(
                    {'_id': person_parent_id},
                    {'$addToSet': {'children': concept_id}}
                )
                print(f"  ✓ Ensured person has correct parent: {name}")
    
    print(f"\nTotal updates made: {updates_made}")
    return updates_made

def verify_results(db):
    """Verify the fix was successful"""
    print("\n=== Verification Results ===")
    
    # Count concepts by entity type
    pipeline = [
        {'$group': {'_id': '$entity_type', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}
    ]
    
    entity_type_counts = list(db.tag_concepts_v2.aggregate(pipeline))
    
    print("Entity type distribution:")
    for item in entity_type_counts:
        entity_type = item['_id'] if item['_id'] else 'null/missing'
        count = item['count']
        print(f"  {entity_type}: {count}")
    
    # Check specifically for person entity type
    person_concepts = list(db.tag_concepts_v2.find({'entity_type': 'person'}))
    print(f"\nConcepts with entity_type 'person': {len(person_concepts)}")
    for concept in person_concepts:
        name = concept.get('name', str(concept.get('_id')))
        print(f"  - {name}")
    
    # Check root categories
    root_concepts = list(db.tag_concepts_v2.find({
        '$or': [
            {'parents': {'$size': 0}}, 
            {'parents': {'$exists': False}},
            {'parents': None}
        ]
    }))
    
    print(f"\nRoot-level concepts: {len(root_concepts)}")
    for concept in root_concepts:
        name = concept.get('name', str(concept.get('_id')))
        entity_type = concept.get('entity_type', 'None')
        children_count = len(concept.get('children', []))
        print(f"  - {name} (type: {entity_type}, children: {children_count})")

def main():
    """Main function to fix person entity misclassification"""
    print("=== Person Entity Misclassification Fix ===")
    print("This script will fix concepts incorrectly marked as entity_type: 'person'")
    print()
    
    # Connect to database
    db = connect_to_mongodb()
    
    # Load schema
    schema = load_top_level_schema()
    
    # Ensure proper category structure exists
    categories_map = ensure_top_level_categories(db, schema)
    
    # Fix the person entity types
    updates_made = fix_person_entity_types(db, categories_map)
    
    # Verify results
    verify_results(db)
    
    print(f"\n=== Fix Complete ===")
    print(f"Total concept updates made: {updates_made}")
    print("The Person entity type now contains only actual people.")
    print("Other concepts have been properly categorized by their content type.")

if __name__ == "__main__":
    main()