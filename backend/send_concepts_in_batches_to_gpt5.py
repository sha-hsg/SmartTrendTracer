#!/usr/bin/env python3
"""
Send concepts to GPT-5 in batches for complete reorganization
GPT-5 indicated it needs batches of 180-220 concepts for reliable processing
"""

import json
import asyncio
import logging
from datetime import datetime
from pymongo import MongoClient
from app.services.gpt5_tag_reorganizer import GPT5TagReorganizer
from pathlib import Path
from bson import ObjectId
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def prepare_concepts_batch(concepts: List[Dict], batch_num: int, total_batches: int) -> Dict[str, Any]:
    """
    Prepare a batch of concepts with IDs for GPT-5
    """
    batch_data = []
    
    for concept in concepts:
        concept_id = str(concept['_id'])
        
        # Get usage count
        client = MongoClient('mongodb://localhost:27017/')
        db = client.smarttrendtracer
        usage_count = db.tag_instances.count_documents({
            'concept_id': concept_id
        })
        
        # Get parent slugs
        parent_slugs = []
        for parent_id in concept.get('parents', []):
            parent = db.tag_concepts_v2.find_one({'_id': parent_id})
            if parent:
                parent_slugs.append(parent.get('slug', str(parent_id)))
        
        # Get aliases
        aliases = list(db.tag_aliases_v2.find({'concept_id': concept['_id']}))
        alias_texts = [a['alias_text'] for a in aliases]
        
        # Build concept data WITH EXPLICIT ID
        concept_data = {
            'mongodb_id': concept_id,
            'slug': concept.get('slug', ''),
            'display_name': concept.get('display_name', concept.get('slug', '')),
            'description': concept.get('description', ''),
            'entity_type': concept.get('entity_type', 'concept'),
            'current_parent_slugs': parent_slugs,
            'aliases': alias_texts,
            'usage_count': usage_count
        }
        
        batch_data.append(concept_data)
    
    return {
        'batch_number': batch_num,
        'total_batches': total_batches,
        'concepts': batch_data,
        'concept_count': len(batch_data)
    }

def create_batch_prompt(batch_data: Dict[str, Any], root_categories: List[Dict]) -> str:
    """
    Create prompt for a batch of concepts
    """
    batch_num = batch_data['batch_number']
    total_batches = batch_data['total_batches']
    count = batch_data['concept_count']
    
    prompt = f"""You are processing BATCH {batch_num} of {total_batches} for tag reorganization.
This batch contains {count} concepts that MUST be organized.

ROOT CATEGORIES TO USE:
{json.dumps(root_categories, indent=2)}

YOUR TASK FOR THIS BATCH:
1. Process ALL {count} concepts in this batch
2. For each concept, decide:
   - Keep as-is with new parent assignment
   - Merge into another concept (provide merge_into_id)
   - Rename but preserve the mongodb_id
3. Return a mapping for EVERY mongodb_id in this batch

REQUIRED OUTPUT FORMAT:
{{
  "batch_number": {batch_num},
  "concepts_processed": {count},
  "concept_mappings": [
    {{
      "mongodb_id": "ORIGINAL_MONGODB_ID",  // MUST match input
      "action": "keep|merge|reorganize",
      "new_slug": "new-or-same-slug",
      "new_display_name": "Display Name",
      "new_parent_slug": "parent-category-slug from root categories",
      "merge_into_id": "target_mongodb_id if merging, null otherwise",
      "reason": "Brief explanation"
    }}
    // MUST have EXACTLY {count} entries
  ],
  "verification": {{
    "batch_total": {count},
    "mapped_count": 0  // Must equal {count}
  }}
}}

VALIDATION:
- concept_mappings MUST have EXACTLY {count} entries
- Every mongodb_id from input MUST appear in concept_mappings
- verification.mapped_count MUST equal {count}

BATCH CONCEPTS:
{json.dumps(batch_data['concepts'], indent=2)}"""
    
    return prompt

async def send_batch_to_gpt5(batch_data: Dict[str, Any], root_categories: List[Dict], reorganizer: GPT5TagReorganizer) -> Dict[str, Any]:
    """
    Send a single batch to GPT-5
    """
    batch_num = batch_data['batch_number']
    count = batch_data['concept_count']
    
    print(f"\n📦 Batch {batch_num}: Sending {count} concepts to GPT-5...")
    
    system_prompt = """You are processing a batch of concepts for tag reorganization. You MUST map EVERY single concept provided in this batch. Missing even one is a failure."""
    
    user_prompt = create_batch_prompt(batch_data, root_categories)
    
    try:
        from langchain.schema import HumanMessage, SystemMessage
        
        client = reorganizer.llm_service._get_client(reorganizer.model_config)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        start_time = datetime.now()
        response = client.invoke(messages)
        elapsed = (datetime.now() - start_time).total_seconds()
        
        print(f"   ✅ Batch {batch_num} completed in {elapsed:.1f} seconds")
        
        # Parse response
        result_text = response.content if hasattr(response, 'content') else str(response)
        
        # Save batch response
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        response_file = f"data/gpt5_responses/batch_{batch_num}_{timestamp}.txt"
        Path("data/gpt5_responses").mkdir(parents=True, exist_ok=True)
        
        with open(response_file, 'w') as f:
            f.write(f"Batch: {batch_num}/{batch_data['total_batches']}\n")
            f.write(f"Concepts: {count}\n")
            f.write("-" * 80 + "\n")
            f.write(result_text)
        
        # Parse JSON
        try:
            result = json.loads(result_text)
        except:
            import re
            json_match = re.search(r'\{[\s\S]*\}', result_text)
            if json_match:
                result = json.loads(json_match.group(0))
            else:
                print(f"   ❌ Could not parse batch {batch_num} response")
                return None
        
        # Verify batch
        if 'concept_mappings' in result:
            mapped = len(result['concept_mappings'])
            print(f"   📊 Batch {batch_num}: Mapped {mapped}/{count} concepts")
            if mapped != count:
                print(f"   ⚠️ WARNING: Batch {batch_num} incomplete!")
        
        return result
        
    except Exception as e:
        print(f"   ❌ Batch {batch_num} failed: {e}")
        return None

async def process_all_batches():
    """
    Process all concepts in batches
    """
    print("\n" + "="*70)
    print("BATCHED CONCEPT REORGANIZATION WITH GPT-5")
    print("="*70)
    
    client = MongoClient('mongodb://localhost:27017/')
    db = client.smarttrendtracer
    
    # Get ALL concepts
    all_concepts = list(db.tag_concepts_v2.find())
    total_concepts = len(all_concepts)
    
    print(f"\n📊 Total concepts to process: {total_concepts}")
    
    # Define root categories (from GPT-5's response)
    root_categories = [
        {"slug": "fundamentals", "display_name": "AI/ML Fundamentals"},
        {"slug": "models_and_architectures", "display_name": "Models and Architectures"},
        {"slug": "techniques_and_methods", "display_name": "Techniques and Methods"},
        {"slug": "training_and_post_training", "display_name": "Training and Post-Training"},
        {"slug": "data_and_datasets", "display_name": "Data and Datasets"},
        {"slug": "evaluation_and_benchmarks", "display_name": "Evaluation and Benchmarks"},
        {"slug": "applications_and_tasks", "display_name": "Applications and Tasks"},
        {"slug": "modalities_and_multimodal", "display_name": "Modalities and Multimodal"},
        {"slug": "responsible_ai_and_governance", "display_name": "Responsible AI and Governance"},
        {"slug": "ecosystem_and_industry", "display_name": "Ecosystem and Industry"},
        {"slug": "tools_libraries_and_standards", "display_name": "Tools, Libraries, and Standards"},
        {"slug": "named_and_research_entities", "display_name": "Named & Research Entities"}
    ]
    
    # Create batches (200 concepts per batch)
    batch_size = 200
    batches = []
    
    for i in range(0, total_concepts, batch_size):
        batch_concepts = all_concepts[i:i+batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total_concepts + batch_size - 1) // batch_size
        
        batch_data = prepare_concepts_batch(batch_concepts, batch_num, total_batches)
        batches.append(batch_data)
    
    print(f"📦 Created {len(batches)} batches of ~{batch_size} concepts each")
    
    # Initialize reorganizer
    reorganizer = GPT5TagReorganizer()
    
    # Process each batch
    all_mappings = []
    
    for batch_data in batches:
        result = await send_batch_to_gpt5(batch_data, root_categories, reorganizer)
        if result and 'concept_mappings' in result:
            all_mappings.extend(result['concept_mappings'])
            
            # Save intermediate results
            with open('data/gpt5_responses/all_mappings_progress.json', 'w') as f:
                json.dump(all_mappings, f, indent=2)
        
        # Small delay between batches
        if batch_data['batch_number'] < len(batches):
            print("   ⏳ Waiting 2 seconds before next batch...")
            await asyncio.sleep(2)
    
    # Save final consolidated mappings
    final_result = {
        'total_concepts': total_concepts,
        'root_categories': root_categories,
        'concept_mappings': all_mappings,
        'mapped_count': len(all_mappings),
        'timestamp': datetime.now().isoformat()
    }
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    final_file = f"data/gpt5_responses/final_batched_mapping_{timestamp}.json"
    
    with open(final_file, 'w') as f:
        json.dump(final_result, f, indent=2)
    
    print("\n" + "="*70)
    print("BATCHED PROCESSING COMPLETE!")
    print(f"📊 Total mappings collected: {len(all_mappings)}/{total_concepts}")
    print(f"💾 Final mapping saved to: {final_file}")
    print("="*70)
    
    return final_result

def apply_batched_mappings(mappings_file: str):
    """
    Apply the batched mappings from GPT-5
    """
    print("\n" + "="*70)
    print("APPLYING BATCHED MAPPINGS")
    print("="*70)
    
    with open(mappings_file, 'r') as f:
        data = json.load(f)
    
    mappings = data.get('concept_mappings', [])
    root_categories = data.get('root_categories', [])
    
    if not mappings:
        print("❌ No mappings to apply")
        return
    
    client = MongoClient('mongodb://localhost:27017/')
    db = client.smarttrendtracer
    
    stats = {
        'kept': 0,
        'merged': 0,
        'reorganized': 0,
        'root_created': 0,
        'errors': 0
    }
    
    # First, create root categories
    for cat in root_categories:
        existing = db.tag_concepts_v2.find_one({'slug': cat['slug']})
        if not existing:
            result = db.tag_concepts_v2.insert_one({
                'slug': cat['slug'],
                'display_name': cat['display_name'],
                'description': cat.get('description', ''),
                'parents': [],
                'children': [],
                'entity_type': 'category',
                'status': 'active'
            })
            stats['root_created'] += 1
            print(f"✅ Created root category: {cat['display_name']}")
    
    # Build slug to ID map for parents
    slug_to_id = {}
    for concept in db.tag_concepts_v2.find():
        slug_to_id[concept.get('slug', '')] = concept['_id']
    
    # Apply each mapping
    print(f"\n📝 Applying {len(mappings)} concept mappings...")
    
    for mapping in mappings:
        try:
            mongodb_id = mapping['mongodb_id']
            action = mapping['action']
            
            if action == 'keep' or action == 'reorganize':
                # Update parent
                new_parent_slug = mapping.get('new_parent_slug')
                if new_parent_slug and new_parent_slug in slug_to_id:
                    db.tag_concepts_v2.update_one(
                        {'_id': ObjectId(mongodb_id)},
                        {'$set': {'parents': [slug_to_id[new_parent_slug]]}}
                    )
                
                # Update display name if changed
                if mapping.get('new_display_name'):
                    db.tag_concepts_v2.update_one(
                        {'_id': ObjectId(mongodb_id)},
                        {'$set': {'display_name': mapping['new_display_name']}}
                    )
                
                stats['reorganized' if action == 'reorganize' else 'kept'] += 1
                
            elif action == 'merge':
                # Handle merge
                merge_into_id = mapping.get('merge_into_id')
                if merge_into_id:
                    # Update all tag instances
                    result = db.tag_instances.update_many(
                        {'concept_id': mongodb_id},
                        {'$set': {'concept_id': merge_into_id}}
                    )
                    
                    if result.modified_count > 0:
                        print(f"   Merged {result.modified_count} instances from {mongodb_id[:8]}...")
                    
                    # Mark original concept as merged
                    db.tag_concepts_v2.update_one(
                        {'_id': ObjectId(mongodb_id)},
                        {'$set': {'status': 'merged', 'merged_into': merge_into_id}}
                    )
                    
                    stats['merged'] += 1
                    
        except Exception as e:
            print(f"   Error processing {mapping.get('mongodb_id')}: {e}")
            stats['errors'] += 1
    
    print(f"\n📊 Mapping Applied:")
    print(f"   - Root categories created: {stats['root_created']}")
    print(f"   - Kept: {stats['kept']}")
    print(f"   - Reorganized: {stats['reorganized']}")
    print(f"   - Merged: {stats['merged']}")
    print(f"   - Errors: {stats['errors']}")
    
    # Final check
    root_count = db.tag_concepts_v2.count_documents({'parents': []})
    total_count = db.tag_concepts_v2.count_documents({'status': {'$ne': 'merged'}})
    
    print(f"\n📈 Final State:")
    print(f"   - Active concepts: {total_count}")
    print(f"   - Root concepts: {root_count}")

def main():
    """
    Main execution
    """
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--apply':
        # Apply existing mappings
        if len(sys.argv) > 2:
            mappings_file = sys.argv[2]
        else:
            # Find most recent final mapping
            from pathlib import Path
            files = sorted(Path('data/gpt5_responses').glob('final_batched_mapping_*.json'))
            if files:
                mappings_file = str(files[-1])
                print(f"Using most recent mapping: {mappings_file}")
            else:
                print("No mapping file found. Run without --apply first.")
                return
        
        apply_batched_mappings(mappings_file)
    else:
        # Process all batches
        print("GPT-5 BATCHED CONCEPT REORGANIZATION")
        print("This will process all concepts in batches of 200")
        print("")
        
        result = asyncio.run(process_all_batches())
        
        if result and result.get('mapped_count', 0) > 0:
            print("\n✅ Batched processing complete!")
            print(f"To apply the mappings, run:")
            print(f"python send_concepts_in_batches_to_gpt5.py --apply")

if __name__ == "__main__":
    main()