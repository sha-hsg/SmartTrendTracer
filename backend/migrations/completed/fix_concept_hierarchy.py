#!/usr/bin/env python3
"""
Fix the concept hierarchy by establishing proper main categories and parent-child relationships.
This script:
1. Creates the main category structure from top_level.json
2. Re-parents existing concepts under appropriate categories
3. Fixes the children arrays for all concepts
4. Reduces root concepts from 121 to ~8-10 main categories
"""

import json
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from typing import Dict, List, Set, Optional
import sys

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['smarttrendtracer']
concepts_collection = db['tag_concepts_v2']
aliases_collection = db['tag_aliases_v2']

def load_top_level_schema():
    """Load the top-level hierarchy schema."""
    with open('top_level.json', 'r') as f:
        return json.load(f)

def create_main_categories():
    """Create the main category concepts based on the hierarchy."""
    main_categories = [
        {
            'slug': 'ai-ml-fundamentals',
            'display_name': 'AI/ML Fundamentals',
            'description': 'Core concepts, theories, and foundations of artificial intelligence and machine learning',
            'color': '#3B82F6',
            'icon': '🤖',
            'entity_type': 'category'
        },
        {
            'slug': 'research-and-development',
            'display_name': 'Research & Development',
            'description': 'Research papers, methodologies, and scientific developments',
            'color': '#6366F1',
            'icon': '🔬',
            'entity_type': 'category'
        },
        {
            'slug': 'organizations-and-companies',
            'display_name': 'Organizations & Companies',
            'description': 'Companies, institutions, labs, and other organizations',
            'color': '#8B5CF6',
            'icon': '🏢',
            'entity_type': 'category'
        },
        {
            'slug': 'tools-and-technologies',
            'display_name': 'Tools & Technologies',
            'description': 'Software tools, frameworks, platforms, and technologies',
            'color': '#10B981',
            'icon': '🛠️',
            'entity_type': 'category'
        },
        {
            'slug': 'data-and-datasets',
            'display_name': 'Data & Datasets',
            'description': 'Datasets, benchmarks, and data-related concepts',
            'color': '#14B8A6',
            'icon': '📊',
            'entity_type': 'category'
        },
        {
            'slug': 'people-and-community',
            'display_name': 'People & Community',
            'description': 'Individuals, researchers, and community-related concepts',
            'color': '#EF4444',
            'icon': '👥',
            'entity_type': 'category'
        },
        {
            'slug': 'applications-and-use-cases',
            'display_name': 'Applications & Use Cases',
            'description': 'Real-world applications, use cases, and implementations',
            'color': '#F59E0B',
            'icon': '💡',
            'entity_type': 'category'
        },
        {
            'slug': 'industry-and-business',
            'display_name': 'Industry & Business',
            'description': 'Business aspects, market trends, and industry developments',
            'color': '#84CC16',
            'icon': '💼',
            'entity_type': 'category'
        }
    ]
    
    created_categories = {}
    
    for category in main_categories:
        # Check if category already exists
        existing = concepts_collection.find_one({'slug': category['slug']})
        
        if existing:
            print(f"✓ Category '{category['display_name']}' already exists")
            # Update to ensure it's a root category
            concepts_collection.update_one(
                {'_id': existing['_id']},
                {
                    '$set': {
                        'parents': [],
                        'entity_type': category['entity_type'],
                        'color': category.get('color'),
                        'icon': category.get('icon'),
                        'description': category['description'],
                        'is_main_category': True,
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            created_categories[category['slug']] = existing['_id']
        else:
            # Create new category
            new_category = {
                'slug': category['slug'],
                'name': category['display_name'],
                'display_name': category['display_name'],
                'description': category['description'],
                'parents': [],
                'children': [],
                'entity_type': category['entity_type'],
                'color': category.get('color'),
                'icon': category.get('icon'),
                'is_main_category': True,
                'created_at': datetime.utcnow(),
                'created_by': 'hierarchy_fix_script',
                'usage_count': 0
            }
            result = concepts_collection.insert_one(new_category)
            created_categories[category['slug']] = result.inserted_id
            print(f"✅ Created category '{category['display_name']}'")
    
    return created_categories

def categorize_concepts(main_categories: Dict[str, ObjectId]):
    """Categorize existing concepts under appropriate main categories."""
    
    # Define categorization rules based on keywords and patterns
    categorization_rules = {
        'ai-ml-fundamentals': [
            'neural', 'network', 'deep-learning', 'machine-learning', 'artificial-intelligence',
            'transformer', 'attention', 'embedding', 'model', 'training', 'inference',
            'gradient', 'backprop', 'optimization', 'loss', 'activation', 'layer',
            'cnn', 'rnn', 'lstm', 'bert', 'gpt', 'llm', 'nlp', 'computer-vision',
            'reinforcement-learning', 'supervised', 'unsupervised', 'fine-tuning'
        ],
        'research-and-development': [
            'research', 'paper', 'study', 'experiment', 'methodology', 'evaluation',
            'benchmark', 'metric', 'analysis', 'survey', 'review', 'conference',
            'journal', 'publication', 'arxiv', 'citation', 'peer-review'
        ],
        'organizations-and-companies': [
            'openai', 'google', 'microsoft', 'anthropic', 'meta', 'facebook',
            'deepmind', 'huggingface', 'nvidia', 'aws', 'azure', 'lab', 'institute',
            'university', 'stanford', 'mit', 'berkeley'
        ],
        'tools-and-technologies': [
            'pytorch', 'tensorflow', 'keras', 'scikit', 'pandas', 'numpy',
            'framework', 'library', 'api', 'sdk', 'platform', 'tool', 'software',
            'github', 'docker', 'kubernetes', 'cloud', 'edge', 'deployment'
        ],
        'data-and-datasets': [
            'dataset', 'data', 'corpus', 'benchmark', 'imagenet', 'coco', 'glue',
            'squad', 'mnist', 'cifar', 'preprocessing', 'augmentation', 'annotation',
            'labeling', 'synthetic', 'collection'
        ],
        'people-and-community': [
            'sam-altman', 'elon-musk', 'yann-lecun', 'geoffrey-hinton', 'andrew-ng',
            'researcher', 'scientist', 'engineer', 'developer', 'community', 'team',
            'author', 'contributor', 'maintainer'
        ],
        'applications-and-use-cases': [
            'chatbot', 'assistant', 'translation', 'summarization', 'generation',
            'classification', 'detection', 'recognition', 'segmentation', 'prediction',
            'recommendation', 'search', 'retrieval', 'automation', 'robotics'
        ],
        'industry-and-business': [
            'startup', 'enterprise', 'market', 'business', 'revenue', 'funding',
            'investment', 'acquisition', 'partnership', 'customer', 'product',
            'service', 'solution', 'platform', 'saas', 'b2b', 'b2c'
        ]
    }
    
    # Get all concepts that are currently root concepts (excluding main categories)
    root_concepts = list(concepts_collection.find({
        'parents': {'$size': 0},
        'is_main_category': {'$ne': True}
    }))
    
    print(f"\nFound {len(root_concepts)} root concepts to categorize")
    
    categorized_count = 0
    for concept in root_concepts:
        slug = concept.get('slug', '').lower()
        display_name = concept.get('display_name', '').lower()
        description = (concept.get('description', '') or '').lower()
        
        # Try to find the best category for this concept
        best_category = None
        best_score = 0
        
        for category_slug, keywords in categorization_rules.items():
            score = 0
            for keyword in keywords:
                if keyword in slug:
                    score += 3
                if keyword in display_name:
                    score += 2
                if keyword in description:
                    score += 1
            
            if score > best_score:
                best_score = score
                best_category = category_slug
        
        # If we found a category with score > 0, assign it
        if best_category and best_score > 0:
            category_id = main_categories[best_category]
            
            # Update the concept to have this category as parent
            concepts_collection.update_one(
                {'_id': concept['_id']},
                {
                    '$set': {
                        'parents': [category_id],
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            categorized_count += 1
            print(f"  → {concept['display_name']} → {best_category} (score: {best_score})")
        else:
            # Default to AI/ML Fundamentals if no clear match
            category_id = main_categories['ai-ml-fundamentals']
            concepts_collection.update_one(
                {'_id': concept['_id']},
                {
                    '$set': {
                        'parents': [category_id],
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            categorized_count += 1
            print(f"  → {concept['display_name']} → ai-ml-fundamentals (default)")
    
    print(f"\n✅ Categorized {categorized_count} concepts")
    return categorized_count

def rebuild_children_arrays():
    """Rebuild the children arrays for all concepts based on parent relationships."""
    print("\nRebuilding children arrays...")
    
    # First, clear all children arrays
    concepts_collection.update_many({}, {'$set': {'children': []}})
    
    # Get all concepts with parents
    concepts_with_parents = concepts_collection.find({'parents': {'$exists': True, '$ne': []}})
    
    parent_children_map = {}
    for concept in concepts_with_parents:
        for parent_id in concept.get('parents', []):
            if parent_id not in parent_children_map:
                parent_children_map[parent_id] = []
            parent_children_map[parent_id].append(concept['_id'])
    
    # Update each parent with its children
    for parent_id, children_ids in parent_children_map.items():
        concepts_collection.update_one(
            {'_id': parent_id},
            {'$set': {'children': children_ids}}
        )
    
    print(f"✅ Updated {len(parent_children_map)} concepts with children")
    return len(parent_children_map)

def print_hierarchy_stats():
    """Print statistics about the hierarchy after fixing."""
    print("\n" + "="*50)
    print("HIERARCHY STATISTICS AFTER FIX")
    print("="*50)
    
    total_concepts = concepts_collection.count_documents({})
    root_concepts = concepts_collection.count_documents({'parents': {'$size': 0}})
    main_categories = concepts_collection.count_documents({'is_main_category': True})
    poly_hierarchy = concepts_collection.count_documents({
        'parents': {'$exists': True, '$not': {'$size': 0}, '$not': {'$size': 1}}
    })
    
    print(f"Total concepts: {total_concepts}")
    print(f"Main categories: {main_categories}")
    print(f"Other root concepts: {root_concepts - main_categories}")
    print(f"Poly-hierarchy concepts: {poly_hierarchy}")
    
    print("\nMain Categories:")
    for cat in concepts_collection.find({'is_main_category': True}).sort('display_name'):
        child_count = len(cat.get('children', []))
        print(f"  • {cat['display_name']}: {child_count} children")
    
    # Check for orphaned concepts (no parents and not a main category)
    orphaned = concepts_collection.count_documents({
        'parents': {'$size': 0},
        'is_main_category': {'$ne': True}
    })
    if orphaned > 0:
        print(f"\n⚠️  Warning: {orphaned} concepts still without parent categories")

def main():
    print("🔧 FIXING CONCEPT HIERARCHY")
    print("="*50)
    
    # Step 1: Create main categories
    print("\n1. Creating main categories...")
    main_categories = create_main_categories()
    
    # Step 2: Categorize existing concepts
    print("\n2. Categorizing existing concepts...")
    categorize_concepts(main_categories)
    
    # Step 3: Rebuild children arrays
    print("\n3. Rebuilding parent-child relationships...")
    rebuild_children_arrays()
    
    # Step 4: Print final statistics
    print_hierarchy_stats()
    
    print("\n✅ Hierarchy fix complete!")
    print("You can now run the tag reorganization with proper hierarchy structure.")

if __name__ == "__main__":
    main()