#!/usr/bin/env python3
"""
Reorganize ALL concepts using GPT-5 in batches
Process in smaller chunks and apply immediately
"""

import json
import logging
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId
from app.services.gpt5_tag_reorganizer import GPT5TagReorganizer
from pathlib import Path
from langchain.schema import HumanMessage, SystemMessage
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Root categories from GPT-5
ROOT_CATEGORIES = [
    {"slug": "fundamentals", "display_name": "AI/ML Fundamentals", "description": "Foundational concepts, fields, and theory in AI/ML"},
    {"slug": "models_and_architectures", "display_name": "Models and Architectures", "description": "Model families and core architectures"},
    {"slug": "techniques_and_methods", "display_name": "Techniques and Methods", "description": "Training/inference techniques, optimization, prompting"},
    {"slug": "training_and_post_training", "display_name": "Training and Post-Training", "description": "Pre-training, fine-tuning, RLHF, PEFT methods"},
    {"slug": "data_and_datasets", "display_name": "Data and Datasets", "description": "Datasets, data sources, curation, licenses"},
    {"slug": "evaluation_and_benchmarks", "display_name": "Evaluation and Benchmarks", "description": "Benchmarks, metrics, evaluation practices"},
    {"slug": "applications_and_tasks", "display_name": "Applications and Tasks", "description": "Downstream tasks and product use-cases"},
    {"slug": "modalities_and_multimodal", "display_name": "Modalities and Multimodal", "description": "Text, image, audio, video, multimodal"},
    {"slug": "responsible_ai_and_governance", "display_name": "Responsible AI", "description": "Safety, ethics, interpretability, governance"},
    {"slug": "ecosystem_and_industry", "display_name": "Ecosystem and Industry", "description": "Organizations, events, releases, market"},
    {"slug": "tools_libraries_and_standards", "display_name": "Tools and Standards", "description": "Software, frameworks, standards"},
    {"slug": "named_and_research_entities", "display_name": "Named Entities", "description": "People, organizations, locations, products"}
]

def create_root_categories(db):
    """
    Create or verify root categories exist
    """
    print("\n📁 Creating root categories...")
    category_ids = {}
    
    for cat in ROOT_CATEGORIES:
        existing = db.tag_concepts_v2.find_one({'slug': cat['slug']})
        if not existing:
            # Remove 'id' field if it exists to avoid duplicate key error
            cat_data = {
                'slug': cat['slug'],
                'display_name': cat['display_name'],
                'description': cat.get('description', ''),
                'parents': [],
                'children': [],
                'entity_type': 'category',
                'status': 'active'
            }
            result = db.tag_concepts_v2.insert_one(cat_data)
            category_ids[cat['slug']] = result.inserted_id
            print(f"   ✅ Created: {cat['display_name']}")
        else:
            category_ids[cat['slug']] = existing['_id']
            print(f"   ✓ Exists: {cat['display_name']}")
    
    return category_ids

def prepare_batch(concepts, db):
    """
    Prepare a batch of concepts for GPT-5
    """
    batch_data = []
    
    for concept in concepts:
        concept_id = str(concept['_id'])
        
        # Get usage count
        usage_count = db.tag_instances.count_documents({'concept_id': concept_id})
        
        # Get current parent slugs
        parent_slugs = []
        for parent_id in concept.get('parents', []):
            parent = db.tag_concepts_v2.find_one({'_id': parent_id})
            if parent:
                parent_slugs.append(parent.get('slug', ''))
        
        batch_data.append({
            'mongodb_id': concept_id,
            'slug': concept.get('slug', ''),
            'display_name': concept.get('display_name', concept.get('slug', '')),
            'entity_type': concept.get('entity_type', 'concept'),
            'current_parents': parent_slugs,
            'usage_count': usage_count
        })
    
    return batch_data

def send_batch_to_gpt5(batch_data, batch_num, total_batches, reorganizer):
    """
    Send a batch to GPT-5 for reorganization
    """
    count = len(batch_data)
    
    system_prompt = """You are reorganizing a tag taxonomy. Assign each concept to the most appropriate root category. Be systematic and consistent."""
    
    user_prompt = f"""This is batch {batch_num} of {total_batches}.
Organize these {count} concepts into the root categories.

ROOT CATEGORIES:
- fundamentals: AI/ML fundamentals and theory
- models_and_architectures: Model families (GPT, Llama, Claude) and architectures
- techniques_and_methods: Training techniques, optimization, prompting
- training_and_post_training: Fine-tuning, RLHF, PEFT methods
- data_and_datasets: Datasets, data sources, curation
- evaluation_and_benchmarks: Benchmarks, metrics, evaluation
- applications_and_tasks: Downstream tasks and applications
- modalities_and_multimodal: Text, image, audio, video, multimodal
- responsible_ai_and_governance: Safety, ethics, interpretability
- ecosystem_and_industry: Organizations, events, industry news
- tools_libraries_and_standards: Software, frameworks, standards
- named_and_research_entities: People, orgs, locations, specific entities

For EACH concept, provide:
{{
  "mongodb_id": "the_exact_id",
  "action": "keep",
  "new_parent_slug": "appropriate_category_slug"
}}

IMPORTANT: Return ALL {count} mappings.

CONCEPTS TO ORGANIZE:
{json.dumps(batch_data, indent=2)}

Return JSON with "concept_mappings" array containing exactly {count} mappings."""
    
    try:
        # Call GPT-5
        client = reorganizer.llm_service._get_client(reorganizer.model_config)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = client.invoke(messages)
        result_text = response.content if hasattr(response, 'content') else str(response)
        
        # Save response
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        response_file = f"data/gpt5_responses/batch_{batch_num}_{timestamp}.txt"
        Path("data/gpt5_responses").mkdir(parents=True, exist_ok=True)
        
        with open(response_file, 'w') as f:
            f.write(result_text)
        
        # Parse JSON
        try:
            result = json.loads(result_text)
            return result.get('concept_mappings', [])
        except:
            # Try to extract JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', result_text)
            if json_match:
                result = json.loads(json_match.group(0))
                return result.get('concept_mappings', [])
            return []
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return []

def apply_mappings(mappings, category_ids, db):
    """
    Apply mappings immediately
    """
    stats = {'updated': 0, 'errors': 0}
    
    for mapping in mappings:
        try:
            mongodb_id = mapping['mongodb_id']
            new_parent_slug = mapping.get('new_parent_slug')
            
            if new_parent_slug and new_parent_slug in category_ids:
                # Update parent
                result = db.tag_concepts_v2.update_one(
                    {'_id': ObjectId(mongodb_id)},
                    {'$set': {'parents': [category_ids[new_parent_slug]]}}
                )
                if result.modified_count > 0:
                    stats['updated'] += 1
            
        except Exception as e:
            stats['errors'] += 1
    
    return stats

def main():
    """
    Main reorganization process
    """
    print("\n" + "="*70)
    print("COMPLETE CONCEPT REORGANIZATION WITH GPT-5")
    print("="*70)
    
    client = MongoClient('mongodb://localhost:27017/')
    db = client.smarttrendtracer
    
    # Create root categories first
    category_ids = create_root_categories(db)
    
    # Get ALL concepts that need organizing (those without proper parents)
    all_concepts = list(db.tag_concepts_v2.find({
        '$or': [
            {'parents': []},  # No parents
            {'parents': {'$size': 0}},  # Empty parents array
            {'slug': {'$nin': [cat['slug'] for cat in ROOT_CATEGORIES]}}  # Not a root category
        ]
    }))
    
    total_concepts = len(all_concepts)
    print(f"\n📊 Found {total_concepts} concepts to organize")
    
    if total_concepts == 0:
        print("✅ All concepts already organized!")
        return
    
    # Initialize GPT-5
    reorganizer = GPT5TagReorganizer()
    
    # Process in batches of 100
    batch_size = 100
    total_batches = (total_concepts + batch_size - 1) // batch_size
    
    all_stats = {'updated': 0, 'errors': 0}
    
    for i in range(0, total_concepts, batch_size):
        batch_concepts = all_concepts[i:i+batch_size]
        batch_num = (i // batch_size) + 1
        
        print(f"\n📦 Batch {batch_num}/{total_batches}: Processing {len(batch_concepts)} concepts...")
        
        # Prepare batch
        batch_data = prepare_batch(batch_concepts, db)
        
        # Send to GPT-5
        print(f"   🚀 Sending to GPT-5...")
        start_time = time.time()
        
        mappings = send_batch_to_gpt5(batch_data, batch_num, total_batches, reorganizer)
        
        elapsed = time.time() - start_time
        print(f"   ✅ GPT-5 responded in {elapsed:.1f}s with {len(mappings)} mappings")
        
        # Apply immediately
        if mappings:
            stats = apply_mappings(mappings, category_ids, db)
            all_stats['updated'] += stats['updated']
            all_stats['errors'] += stats['errors']
            print(f"   📝 Applied: {stats['updated']} updated, {stats['errors']} errors")
        
        # Small delay between batches
        if batch_num < total_batches:
            print("   ⏳ Waiting 2 seconds...")
            time.sleep(2)
    
    # Final summary
    print("\n" + "="*70)
    print("REORGANIZATION COMPLETE!")
    print("="*70)
    print(f"\n📊 Final Results:")
    print(f"   - Total concepts processed: {total_concepts}")
    print(f"   - Successfully organized: {all_stats['updated']}")
    print(f"   - Errors: {all_stats['errors']}")
    
    # Check final state
    root_count = db.tag_concepts_v2.count_documents({'parents': []})
    organized_count = db.tag_concepts_v2.count_documents({
        'parents': {'$in': list(category_ids.values())}
    })
    
    print(f"\n📈 Database State:")
    print(f"   - Root categories: {root_count}")
    print(f"   - Organized concepts: {organized_count}")
    print(f"   - Total concepts: {db.tag_concepts_v2.count_documents({})}")
    
    print("\n✅ Your tag system has been reorganized!")
    print("   Check the Tags page to see the new hierarchy.")

if __name__ == "__main__":
    main()