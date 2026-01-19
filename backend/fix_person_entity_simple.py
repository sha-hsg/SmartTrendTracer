#!/usr/bin/env python3
"""
Simple Fix for Person Entity Misclassification

This script addresses the issue where 96 concepts were incorrectly marked with entity_type: 'person'
when only 3 are actual people. It will:

1. Identify actual people (Christopher Manning, Chris Potts, Ethan Mollick)
2. Reset entity_type for non-person concepts to more appropriate types
3. Use existing parent categories where possible

Author: System Architecture Auditor
Date: 2025-08-28
"""

from pymongo import MongoClient

def connect_to_mongodb():
    """Connect to MongoDB"""
    client = MongoClient('mongodb://localhost:27017/')
    db = client['smarttrendtracer']
    return db

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
            if person_name.lower() in name.lower():
                is_person = True
                break
        
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
        elif any(keyword in name_lower for keyword in ['accuracy', 'precision', 'recall', 'score', 'rate', 'metric', 'error']):
            categories['metric'].append(concept)
        elif any(keyword in name_lower for keyword in ['dataset', 'corpus', 'data']):
            categories['dataset'].append(concept)
        elif any(keyword in name_lower for keyword in ['framework', 'library', 'tool', 'software', 'api']):
            categories['tool'].append(concept)
        elif any(keyword in name_lower for keyword in ['openai', 'google', 'microsoft', 'anthropic', 'company', 'lab', 'consulting']):
            categories['organisation'].append(concept)
        elif any(keyword in name_lower for keyword in ['gpu', 'cpu', 'chip', 'hardware', 'accelerator']):
            categories['hardware'].append(concept)
        elif any(keyword in name_lower for keyword in ['transformer', 'cnn', 'rnn', 'architecture', 'layer']):
            categories['architecture'].append(concept)
        elif any(keyword in name_lower for keyword in ['zero-shot', 'few-shot', 'prompting', 'setup']):
            categories['experimental-setup'].append(concept)
        elif any(keyword in name_lower for keyword in ['text', 'image', 'audio', 'video', 'multimodal', 'speech']):
            categories['modality'].append(concept)
        elif any(keyword in name_lower for keyword in ['benchmark', 'leaderboard', 'evaluation']):
            categories['benchmark'].append(concept)
        elif any(keyword in name_lower for keyword in ['mit', 'apache', 'license', 'cc-by']):
            categories['license'].append(concept)
        elif any(keyword in name_lower for keyword in ['tech', 'technology', 'innovation', 'startup']):
            categories['technology'].append(concept)
        else:
            # Default to concept for general ideas and abstract concepts
            categories['concept'].append(concept)
    
    return categories

def fix_person_entity_types(db):
    """Fix the incorrectly classified person entity types"""
    print("=== Fixing Person Entity Type Misclassification ===")
    
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
    
    # Update entity types
    updates_made = 0
    for entity_type, concepts in categorized.items():
        if not concepts:
            continue
            
        print(f"\nProcessing {len(concepts)} concepts for entity_type: '{entity_type}'")
        
        for concept in concepts:
            concept_id = concept['_id']
            name = concept.get('name', str(concept_id))
            
            # Update entity type
            result = db.tag_concepts_v2.update_one(
                {'_id': concept_id},
                {'$set': {'entity_type': entity_type}}
            )
            
            if result.modified_count > 0:
                updates_made += 1
                print(f"  ✓ Updated: {name[:50]}{'...' if len(name) > 50 else ''}")
    
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

def main():
    """Main function to fix person entity misclassification"""
    print("=== Simple Person Entity Misclassification Fix ===")
    print("This script will fix concepts incorrectly marked as entity_type: 'person'")
    print()
    
    # Connect to database
    db = connect_to_mongodb()
    
    # Fix the person entity types
    updates_made = fix_person_entity_types(db)
    
    # Verify results
    verify_results(db)
    
    print(f"\n=== Fix Complete ===")
    print(f"Total concept updates made: {updates_made}")
    print("The Person entity type now contains only actual people.")
    print("Other concepts have been properly categorized by their content type.")

if __name__ == "__main__":
    main()