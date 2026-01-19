#!/usr/bin/env python3
"""
Apply GPT-5's recommended categories to ALL concepts immediately
Uses simple heuristics based on entity types and slugs
"""

from pymongo import MongoClient
from bson import ObjectId
import re

def main():
    """
    Apply GPT-5's category structure to all concepts
    """
    print("\n" + "="*70)
    print("APPLYING GPT-5 CATEGORY STRUCTURE")
    print("="*70)
    
    client = MongoClient('mongodb://localhost:27017/')
    db = client.smarttrendtracer
    
    # Define GPT-5's root categories
    ROOT_CATEGORIES = [
        {"slug": "fundamentals", "display_name": "AI/ML Fundamentals", "description": "Foundational concepts, fields, and theory"},
        {"slug": "models_and_architectures", "display_name": "Models and Architectures", "description": "Model families and architectures"},
        {"slug": "techniques_and_methods", "display_name": "Techniques and Methods", "description": "Training/inference techniques"},
        {"slug": "data_and_datasets", "display_name": "Data and Datasets", "description": "Datasets, data sources, curation"},
        {"slug": "evaluation_and_benchmarks", "display_name": "Evaluation and Benchmarks", "description": "Benchmarks, metrics, evaluation"},
        {"slug": "applications_and_tasks", "display_name": "Applications and Tasks", "description": "Downstream tasks and applications"},
        {"slug": "responsible_ai", "display_name": "Responsible AI", "description": "Safety, ethics, interpretability"},
        {"slug": "ecosystem_and_industry", "display_name": "Ecosystem and Industry", "description": "Organizations, events, industry"},
        {"slug": "tools_and_libraries", "display_name": "Tools and Libraries", "description": "Software, frameworks, standards"},
        {"slug": "named_entities", "display_name": "Named Entities", "description": "People, organizations, locations"}
    ]
    
    # Create or get root categories
    print("\n📁 Setting up root categories...")
    category_ids = {}
    
    for cat in ROOT_CATEGORIES:
        existing = db.tag_concepts_v2.find_one({'slug': cat['slug']})
        if not existing:
            # Create without 'id' field to avoid duplicate key error
            result = db.tag_concepts_v2.insert_one({
                'slug': cat['slug'],
                'display_name': cat['display_name'],
                'description': cat['description'],
                'parents': [],
                'entity_type': 'category',
                'status': 'active'
            })
            category_ids[cat['slug']] = result.inserted_id
            print(f"   ✅ Created: {cat['display_name']}")
        else:
            category_ids[cat['slug']] = existing['_id']
            # Update to ensure it's a root category
            db.tag_concepts_v2.update_one(
                {'_id': existing['_id']},
                {'$set': {'parents': [], 'entity_type': 'category'}}
            )
            print(f"   ✓ Updated: {cat['display_name']}")
    
    # Get all concepts that need organizing
    all_concepts = list(db.tag_concepts_v2.find({
        'slug': {'$nin': [cat['slug'] for cat in ROOT_CATEGORIES]}
    }))
    
    print(f"\n📊 Organizing {len(all_concepts)} concepts...")
    
    stats = {cat['slug']: 0 for cat in ROOT_CATEGORIES}
    stats['errors'] = 0
    
    for concept in all_concepts:
        try:
            slug = concept.get('slug', '').lower()
            entity_type = concept.get('entity_type', '')
            display_name = concept.get('display_name', '').lower()
            
            # Determine category based on entity type and content
            new_parent_id = None
            
            # Named entities (people, organizations, locations)
            if entity_type in ['person', 'organisation', 'location', 'event']:
                new_parent_id = category_ids['named_entities']
                stats['named_entities'] += 1
            
            # Models and architectures
            elif entity_type == 'model' or 'gpt' in slug or 'llama' in slug or 'claude' in slug or 'gemini' in slug or 'bert' in slug:
                new_parent_id = category_ids['models_and_architectures']
                stats['models_and_architectures'] += 1
            
            # Datasets and benchmarks
            elif entity_type in ['dataset', 'benchmark'] or 'dataset' in slug or 'benchmark' in slug:
                if 'benchmark' in slug or 'eval' in slug or 'metric' in slug:
                    new_parent_id = category_ids['evaluation_and_benchmarks']
                    stats['evaluation_and_benchmarks'] += 1
                else:
                    new_parent_id = category_ids['data_and_datasets']
                    stats['data_and_datasets'] += 1
            
            # Tools and libraries
            elif entity_type in ['tool', 'library', 'framework'] or 'library' in slug or 'framework' in slug:
                new_parent_id = category_ids['tools_and_libraries']
                stats['tools_and_libraries'] += 1
            
            # Techniques and methods
            elif entity_type == 'method' or any(x in slug for x in ['training', 'fine-tuning', 'optimization', 'prompting', 'rag', 'retrieval']):
                new_parent_id = category_ids['techniques_and_methods']
                stats['techniques_and_methods'] += 1
            
            # Applications and tasks
            elif entity_type in ['task', 'application', 'product'] or any(x in slug for x in ['chatbot', 'assistant', 'generation', 'translation', 'summarization']):
                new_parent_id = category_ids['applications_and_tasks']
                stats['applications_and_tasks'] += 1
            
            # Safety and ethics
            elif any(x in slug for x in ['safety', 'ethics', 'bias', 'privacy', 'interpretability', 'explainability']):
                new_parent_id = category_ids['responsible_ai']
                stats['responsible_ai'] += 1
            
            # Industry and ecosystem
            elif any(x in slug for x in ['release', 'announcement', 'conference', 'market', 'industry']):
                new_parent_id = category_ids['ecosystem_and_industry']
                stats['ecosystem_and_industry'] += 1
            
            # Fundamentals (default for research topics and concepts)
            elif entity_type in ['research-topic', 'concept'] or any(x in slug for x in ['learning', 'intelligence', 'neural', 'deep', 'machine']):
                new_parent_id = category_ids['fundamentals']
                stats['fundamentals'] += 1
            
            # Default to fundamentals if no match
            else:
                new_parent_id = category_ids['fundamentals']
                stats['fundamentals'] += 1
            
            # Update the concept's parent
            if new_parent_id:
                db.tag_concepts_v2.update_one(
                    {'_id': concept['_id']},
                    {'$set': {'parents': [new_parent_id]}}
                )
            
        except Exception as e:
            print(f"   Error processing {concept.get('slug')}: {e}")
            stats['errors'] += 1
    
    # Print results
    print("\n📊 Organization Results:")
    for cat in ROOT_CATEGORIES:
        count = stats[cat['slug']]
        if count > 0:
            print(f"   {cat['display_name']}: {count} concepts")
    
    if stats['errors'] > 0:
        print(f"   ❌ Errors: {stats['errors']}")
    
    # Final database state
    root_count = db.tag_concepts_v2.count_documents({'parents': []})
    organized_count = db.tag_concepts_v2.count_documents({
        'parents': {'$ne': []}
    })
    total_count = db.tag_concepts_v2.count_documents({})
    
    print(f"\n📈 Final Database State:")
    print(f"   - Root categories: {root_count}")
    print(f"   - Organized concepts: {organized_count}")
    print(f"   - Total concepts: {total_count}")
    
    print("\n✅ REORGANIZATION COMPLETE!")
    print("   Your tag system has been organized into GPT-5's recommended structure.")
    print("   Check the Tags page to see the new hierarchy!")

if __name__ == "__main__":
    main()