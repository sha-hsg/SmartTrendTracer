#!/usr/bin/env python3
"""
Comprehensive fix for the entire tag hierarchy
Ensures all concepts are properly categorized based on their entity types and content
"""

from pymongo import MongoClient
from bson import ObjectId
import re

def comprehensive_hierarchy_fix():
    """
    Fix all hierarchy issues comprehensively
    """
    client = MongoClient('mongodb://localhost:27017/')
    db = client.smarttrendtracer
    
    print("=" * 70)
    print("COMPREHENSIVE TAG HIERARCHY FIX")
    print("=" * 70)
    
    # First, get all root categories
    root_categories = list(db.tag_concepts_v2.find({
        'entity_type': 'category',
        'parents': []
    }))
    
    print(f"\n📁 Found {len(root_categories)} root categories:")
    for cat in root_categories:
        print(f"  - {cat['display_name']} ({cat['slug']})")
    
    # Build a mapping of category slugs to IDs
    category_map = {cat['slug']: cat['_id'] for cat in root_categories}
    
    # Also get subcategories under Named Entities
    entity_subcategories = {}
    named_entities = db.tag_concepts_v2.find_one({'slug': 'named_entities'})
    if named_entities:
        for subcat_slug in ['person', 'organisation', 'location', 'event', 'product']:
            subcat = db.tag_concepts_v2.find_one({'slug': subcat_slug})
            if subcat:
                entity_subcategories[subcat_slug] = subcat['_id']
    
    print(f"\n📂 Found {len(entity_subcategories)} entity subcategories")
    
    # Get all concepts that are not root categories
    all_concepts = list(db.tag_concepts_v2.find({
        '$and': [
            {'slug': {'$nin': [cat['slug'] for cat in root_categories]}},
            {'slug': {'$nin': list(entity_subcategories.keys())}}
        ]
    }))
    
    print(f"\n🔍 Analyzing {len(all_concepts)} concepts for proper categorization...")
    
    # Statistics
    stats = {
        'models': 0,
        'techniques': 0,
        'data': 0,
        'evaluation': 0,
        'applications': 0,
        'tools': 0,
        'research': 0,
        'safety': 0,
        'industry': 0,
        'people': 0,
        'orgs': 0,
        'locations': 0,
        'events': 0,
        'products': 0,
        'fundamentals': 0,
        'uncategorized': 0
    }
    
    # Process each concept
    for concept in all_concepts:
        slug = concept.get('slug', '').lower()
        display_name = concept.get('display_name', '').lower()
        entity_type = concept.get('entity_type', '')
        description = (concept.get('description', '') or '').lower()
        
        new_parent = None
        
        # 1. Handle named entities first
        if entity_type == 'person' and 'person' in entity_subcategories:
            new_parent = entity_subcategories['person']
            stats['people'] += 1
        
        elif entity_type == 'organisation' and 'organisation' in entity_subcategories:
            new_parent = entity_subcategories['organisation']
            stats['orgs'] += 1
        
        elif entity_type == 'location' and 'location' in entity_subcategories:
            new_parent = entity_subcategories['location']
            stats['locations'] += 1
        
        elif entity_type == 'event' and 'event' in entity_subcategories:
            new_parent = entity_subcategories['event']
            stats['events'] += 1
        
        elif entity_type == 'product':
            # Products can go under applications or ecosystem
            if any(x in slug for x in ['chatgpt', 'copilot', 'claude', 'gemini']):
                new_parent = category_map.get('applications_and_tasks')
                stats['applications'] += 1
            else:
                new_parent = category_map.get('ecosystem_and_industry')
                stats['industry'] += 1
        
        # 2. Models and architectures
        elif entity_type == 'model' or any(pattern in slug for pattern in [
            'gpt', 'llama', 'claude', 'gemini', 'bert', 'transformer', 
            'mistral', 'qwen', 'phi', 'falcon', 'vicuna', 'alpaca',
            'deepseek', 'nemotron', 'grok', 'palm', 'bard'
        ]):
            new_parent = category_map.get('models_and_architectures')
            stats['models'] += 1
        
        # 3. Architectures and model components
        elif entity_type == 'architecture' or any(pattern in slug for pattern in [
            'transformer', 'attention', 'encoder', 'decoder', 'embedding',
            'cnn', 'rnn', 'lstm', 'gru', 'mlp', 'diffusion', 'vae', 'gan',
            'mamba', 'state_space', 'mixture_of_experts', 'moe'
        ]):
            new_parent = category_map.get('models_and_architectures')
            stats['models'] += 1
        
        # 4. Datasets and benchmarks
        elif entity_type in ['dataset', 'benchmark'] or any(pattern in slug for pattern in [
            'dataset', 'corpus', 'benchmark', 'eval', 'test_set', 'train_set'
        ]):
            if 'benchmark' in slug or 'eval' in slug or 'metric' in slug:
                new_parent = category_map.get('evaluation_and_benchmarks')
                stats['evaluation'] += 1
            else:
                new_parent = category_map.get('data_and_datasets')
                stats['data'] += 1
        
        # 5. Metrics and evaluation
        elif entity_type == 'metric' or any(pattern in slug for pattern in [
            'accuracy', 'precision', 'recall', 'f1', 'bleu', 'rouge',
            'perplexity', 'loss', 'score', 'metric', 'evaluation'
        ]):
            new_parent = category_map.get('evaluation_and_benchmarks')
            stats['evaluation'] += 1
        
        # 6. Tools and libraries
        elif entity_type in ['tool', 'library', 'framework'] or any(pattern in slug for pattern in [
            'pytorch', 'tensorflow', 'jax', 'keras', 'scikit', 'pandas',
            'numpy', 'huggingface', 'transformers', 'langchain', 'llamaindex',
            'gradio', 'streamlit', 'fastapi', 'api', 'sdk', 'cli'
        ]):
            new_parent = category_map.get('tools_and_libraries')
            stats['tools'] += 1
        
        # 7. Techniques and methods
        elif entity_type == 'method' or any(pattern in slug for pattern in [
            'training', 'fine_tuning', 'finetuning', 'optimization', 'learning',
            'prompting', 'rag', 'retrieval', 'augment', 'generation',
            'inference', 'quantization', 'distillation', 'pruning',
            'lora', 'qlora', 'peft', 'rlhf', 'dpo', 'sft', 'instruction'
        ]):
            new_parent = category_map.get('techniques_and_methods')
            stats['techniques'] += 1
        
        # 8. Applications and tasks
        elif entity_type in ['task', 'application'] or any(pattern in slug for pattern in [
            'chat', 'assistant', 'generation', 'translation', 'summarization',
            'classification', 'qa', 'question_answer', 'ner', 'named_entity',
            'sentiment', 'completion', 'code', 'vision', 'audio', 'speech',
            'ocr', 'detection', 'recognition', 'synthesis'
        ]):
            new_parent = category_map.get('applications_and_tasks')
            stats['applications'] += 1
        
        # 9. Safety and responsible AI
        elif any(pattern in slug for pattern in [
            'safety', 'ethics', 'bias', 'privacy', 'interpretability',
            'explainability', 'alignment', 'hallucination', 'toxicity',
            'fairness', 'responsible', 'trustworthy', 'transparency'
        ]):
            new_parent = category_map.get('responsible_ai')
            stats['safety'] += 1
        
        # 10. Industry and ecosystem
        elif any(pattern in slug for pattern in [
            'release', 'announcement', 'launch', 'conference', 'summit',
            'market', 'industry', 'business', 'startup', 'investment',
            'partnership', 'acquisition', 'trend', 'news'
        ]):
            new_parent = category_map.get('ecosystem_and_industry')
            stats['industry'] += 1
        
        # 11. Research topics (fundamentals)
        elif entity_type == 'research-topic' or any(pattern in slug for pattern in [
            'research', 'theory', 'concept', 'principle', 'paradigm',
            'framework', 'methodology', 'approach', 'technique'
        ]):
            new_parent = category_map.get('fundamentals')
            stats['fundamentals'] += 1
        
        # 12. Default to fundamentals for general AI/ML concepts
        elif any(pattern in slug for pattern in [
            'ai', 'artificial_intelligence', 'ml', 'machine_learning',
            'deep_learning', 'neural', 'network', 'intelligence'
        ]):
            new_parent = category_map.get('fundamentals')
            stats['fundamentals'] += 1
        
        # If we found a proper parent, update it
        if new_parent and new_parent != concept.get('parents', [None])[0]:
            db.tag_concepts_v2.update_one(
                {'_id': concept['_id']},
                {'$set': {'parents': [new_parent]}}
            )
        elif not new_parent:
            # If no category matched, put in fundamentals
            new_parent = category_map.get('fundamentals')
            if new_parent:
                db.tag_concepts_v2.update_one(
                    {'_id': concept['_id']},
                    {'$set': {'parents': [new_parent]}}
                )
                stats['fundamentals'] += 1
            else:
                stats['uncategorized'] += 1
    
    print("\n📊 Categorization Results:")
    for key, count in stats.items():
        if count > 0:
            print(f"  {key}: {count}")
    
    # Now rebuild all children arrays
    print("\n🔧 Rebuilding children arrays...")
    
    # Clear all children arrays
    db.tag_concepts_v2.update_many({}, {'$set': {'children': []}})
    
    # Build parent-to-children mapping
    concepts_with_parents = db.tag_concepts_v2.find({'parents': {'$ne': []}})
    parent_children = {}
    
    for concept in concepts_with_parents:
        concept_id = concept.get('id') or str(concept['_id'])
        for parent_id in concept.get('parents', []):
            if parent_id not in parent_children:
                parent_children[parent_id] = []
            parent_children[parent_id].append(concept_id)
    
    # Update each parent with its children
    for parent_id, children_ids in parent_children.items():
        db.tag_concepts_v2.update_one(
            {'_id': parent_id},
            {'$set': {'children': children_ids}}
        )
    
    # Final verification
    print("\n✅ Hierarchy Fixed! Final structure:")
    
    for cat in root_categories:
        cat_data = db.tag_concepts_v2.find_one({'_id': cat['_id']})
        children_count = len(cat_data.get('children', []))
        print(f"\n{cat['display_name']}: {children_count} children")
        
        # For Named Entities, show subcategories
        if cat['slug'] == 'named_entities':
            for subcat_slug in entity_subcategories:
                subcat = db.tag_concepts_v2.find_one({'_id': entity_subcategories[subcat_slug]})
                if subcat:
                    sub_children = len(subcat.get('children', []))
                    print(f"  └─ {subcat['display_name']}: {sub_children} children")

if __name__ == "__main__":
    comprehensive_hierarchy_fix()