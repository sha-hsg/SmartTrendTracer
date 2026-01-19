#!/usr/bin/env python3
"""
Send ALL concepts with IDs to GPT-5 and require it to return a complete mapping
This time we EXPLICITLY require GPT-5 to account for EVERY SINGLE concept
"""

import json
import asyncio
import logging
from datetime import datetime
from pymongo import MongoClient
from app.services.gpt5_tag_reorganizer import GPT5TagReorganizer
from pathlib import Path
from bson import ObjectId

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def prepare_concepts_with_ids():
    """
    Prepare ALL concepts with their MongoDB IDs for GPT-5
    """
    client = MongoClient('mongodb://localhost:27017/')
    db = client.smarttrendtracer
    
    # Get ALL concepts
    all_concepts = list(db.tag_concepts_v2.find())
    
    print(f"Preparing {len(all_concepts)} concepts with IDs for GPT-5...")
    
    # Prepare complete concept data WITH IDs
    concepts_list = []
    id_to_slug = {}
    
    for concept in all_concepts:
        concept_id = str(concept['_id'])
        slug = concept.get('slug', '')
        
        # Map ID to slug for reference
        id_to_slug[concept_id] = slug
        
        # Count usage
        usage_count = db.tag_instances.count_documents({
            'concept_id': concept_id
        })
        
        # Get parent IDs
        parent_ids = [str(pid) for pid in concept.get('parents', [])]
        
        # Get aliases
        aliases = list(db.tag_aliases_v2.find({'concept_id': concept['_id']}))
        alias_texts = [a['alias_text'] for a in aliases]
        
        # Build concept data WITH EXPLICIT ID
        concept_data = {
            'mongodb_id': concept_id,  # CRITICAL: Include the actual MongoDB ID
            'slug': slug,
            'display_name': concept.get('display_name', slug),
            'description': concept.get('description', ''),
            'entity_type': concept.get('entity_type', 'concept'),
            'current_parent_ids': parent_ids,
            'aliases': alias_texts,
            'usage_count': usage_count
        }
        
        concepts_list.append(concept_data)
    
    # Sort by usage count
    concepts_list.sort(key=lambda x: x['usage_count'], reverse=True)
    
    return concepts_list, id_to_slug

def create_explicit_gpt5_prompt(concepts_list):
    """
    Create an EXPLICIT prompt that REQUIRES GPT-5 to map EVERY concept
    """
    
    total = len(concepts_list)
    
    prompt = f"""You are reorganizing a tag taxonomy with EXACTLY {total} concepts. 

CRITICAL REQUIREMENTS:
1. You MUST account for ALL {total} concepts - every single one
2. Each concept has a 'mongodb_id' that MUST be preserved
3. You MUST return a mapping for EVERY mongodb_id
4. Do NOT delete or ignore any concepts
5. You CAN merge similar concepts but MUST show the mapping

YOUR TASK:
1. Create 8-12 logical root categories
2. Organize ALL {total} concepts into a clean hierarchy
3. For each concept, decide:
   - Keep as-is with new parent assignment
   - Merge into another concept (but track the merge)
   - Rename but preserve the mongodb_id

REQUIRED OUTPUT FORMAT:
{{
  "instructions_followed": true,
  "total_concepts_processed": {total},
  "root_categories": [
    {{
      "slug": "category-slug",
      "display_name": "Category Name",
      "description": "Description"
    }}
  ],
  "concept_mappings": [
    {{
      "mongodb_id": "ORIGINAL_MONGODB_ID",  // MUST match input
      "action": "keep|merge|reorganize",
      "new_slug": "new-or-same-slug",
      "new_display_name": "Display Name",
      "new_parent_slug": "parent-category-slug",
      "merge_into_id": "target_mongodb_id if merging, null otherwise",
      "reason": "Brief explanation"
    }}
    // MUST have EXACTLY {total} entries - one for EACH concept
  ],
  "verification": {{
    "input_count": {total},
    "output_count": 0,  // Must equal {total}
    "unmapped_ids": []  // Must be empty
  }}
}}

VALIDATION RULES:
- concept_mappings MUST have EXACTLY {total} entries
- Every mongodb_id from input MUST appear in concept_mappings
- verification.unmapped_ids MUST be empty
- verification.output_count MUST equal {total}

If you cannot process all {total} concepts, explain why in an 'error' field."""

    return prompt

async def send_with_ids_to_gpt5():
    """
    Send all concepts with IDs to GPT-5 with explicit mapping requirements
    """
    print("\n" + "="*70)
    print("SENDING ALL CONCEPTS WITH IDs TO GPT-5 FOR COMPLETE MAPPING")
    print("="*70)
    
    # Prepare concepts with IDs
    concepts_list, id_to_slug = prepare_concepts_with_ids()
    
    print(f"\n📊 Prepared {len(concepts_list)} concepts with MongoDB IDs")
    print(f"📝 Sample concepts with IDs:")
    for concept in concepts_list[:5]:
        print(f"   ID: {concept['mongodb_id'][:12]}... -> {concept['display_name']} ({concept['usage_count']} uses)")
    
    # Create explicit prompt
    system_prompt = """You are a meticulous tag reorganization system. You MUST process EVERY single concept provided and return a complete mapping. Missing even one concept is a failure. Be thorough and systematic."""
    
    user_prompt = create_explicit_gpt5_prompt(concepts_list)
    user_prompt += f"\n\nCONCEPTS TO PROCESS:\n{json.dumps(concepts_list, indent=2)}"
    
    print(f"\n🚀 Sending to GPT-5 with EXPLICIT mapping requirements...")
    print(f"   Total concepts: {len(concepts_list)}")
    print(f"   Estimated tokens: ~{len(user_prompt) // 4}")
    
    # Initialize GPT-5 reorganizer
    reorganizer = GPT5TagReorganizer()
    
    # Send to GPT-5
    start_time = datetime.now()
    print(f"\n⏰ Started at: {start_time.strftime('%H:%M:%S')}")
    print("   GPT-5 MUST map all concepts. This will take 10-20 minutes...")
    
    try:
        # We need to call GPT-5 directly with our custom prompt
        from langchain.schema import HumanMessage, SystemMessage
        
        client = reorganizer.llm_service._get_client(reorganizer.model_config)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        print("   Waiting for GPT-5 to process ALL concepts...")
        response = client.invoke(messages)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\n✅ GPT-5 responded in {elapsed:.1f} seconds!")
        
        # Parse response
        result_text = response.content if hasattr(response, 'content') else str(response)
        
        # Save raw response
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        response_file = f"data/gpt5_responses/gpt5_explicit_mapping_{timestamp}.txt"
        Path("data/gpt5_responses").mkdir(parents=True, exist_ok=True)
        
        with open(response_file, 'w') as f:
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Total concepts sent: {len(concepts_list)}\n")
            f.write("-" * 80 + "\n")
            f.write(result_text)
        
        print(f"💾 Raw response saved to: {response_file}")
        
        # Parse JSON
        try:
            result = json.loads(result_text)
        except:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{[\s\S]*\}', result_text)
            if json_match:
                result = json.loads(json_match.group(0))
            else:
                print("❌ Could not parse GPT-5 response as JSON")
                return None
        
        # Verify the response
        if 'concept_mappings' in result:
            mapping_count = len(result['concept_mappings'])
            print(f"\n📊 GPT-5 Mapping Results:")
            print(f"   - Concepts processed: {mapping_count}/{len(concepts_list)}")
            
            if mapping_count == len(concepts_list):
                print("   ✅ ALL concepts mapped!")
            else:
                print(f"   ⚠️ WARNING: Only {mapping_count} of {len(concepts_list)} concepts mapped")
            
            # Count actions
            actions = {}
            for mapping in result['concept_mappings']:
                action = mapping.get('action', 'unknown')
                actions[action] = actions.get(action, 0) + 1
            
            print("\n   Actions breakdown:")
            for action, count in actions.items():
                print(f"     - {action}: {count} concepts")
        
        # Save parsed result
        json_file = f"data/gpt5_responses/gpt5_explicit_mapping_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\n💾 Parsed mapping saved to: {json_file}")
        
        return result, id_to_slug
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def apply_explicit_mapping(mapping_result, id_to_slug):
    """
    Apply the explicit ID-based mapping from GPT-5
    """
    if not mapping_result or 'concept_mappings' not in mapping_result:
        print("❌ No valid mapping to apply")
        return
    
    print("\n" + "="*70)
    print("APPLYING GPT-5's COMPLETE MAPPING")
    print("="*70)
    
    client = MongoClient('mongodb://localhost:27017/')
    db = client.smarttrendtracer
    
    stats = {
        'kept': 0,
        'merged': 0,
        'reorganized': 0,
        'parent_updates': 0,
        'errors': 0
    }
    
    # First, create root categories if needed
    root_categories = mapping_result.get('root_categories', [])
    category_ids = {}
    
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
            category_ids[cat['slug']] = result.inserted_id
            print(f"   Created root category: {cat['display_name']}")
        else:
            category_ids[cat['slug']] = existing['_id']
    
    # Process each mapping
    for mapping in mapping_result['concept_mappings']:
        try:
            mongodb_id = mapping['mongodb_id']
            action = mapping['action']
            
            if action == 'keep' or action == 'reorganize':
                # Update parent
                new_parent_slug = mapping.get('new_parent_slug')
                if new_parent_slug and new_parent_slug in category_ids:
                    db.tag_concepts_v2.update_one(
                        {'_id': ObjectId(mongodb_id)},
                        {'$set': {'parents': [category_ids[new_parent_slug]]}}
                    )
                    stats['parent_updates'] += 1
                
                # Update display name if changed
                if mapping.get('new_display_name'):
                    db.tag_concepts_v2.update_one(
                        {'_id': ObjectId(mongodb_id)},
                        {'$set': {'display_name': mapping['new_display_name']}}
                    )
                
                stats['reorganized' if action == 'reorganize' else 'kept'] += 1
                
            elif action == 'merge':
                # Handle merge - update tag_instances to point to target
                merge_into_id = mapping.get('merge_into_id')
                if merge_into_id:
                    # Update all tag instances
                    db.tag_instances.update_many(
                        {'concept_id': mongodb_id},
                        {'$set': {'concept_id': merge_into_id}}
                    )
                    
                    # Optionally delete the merged concept
                    # db.tag_concepts_v2.delete_one({'_id': ObjectId(mongodb_id)})
                    
                    stats['merged'] += 1
                    
        except Exception as e:
            print(f"   Error processing {mapping.get('mongodb_id')}: {e}")
            stats['errors'] += 1
    
    print(f"\n📊 Mapping Applied:")
    print(f"   - Kept: {stats['kept']}")
    print(f"   - Reorganized: {stats['reorganized']}")
    print(f"   - Merged: {stats['merged']}")
    print(f"   - Parent updates: {stats['parent_updates']}")
    print(f"   - Errors: {stats['errors']}")
    
    # Final check
    root_count = db.tag_concepts_v2.count_documents({'parents': []})
    total_count = db.tag_concepts_v2.count_documents({})
    
    print(f"\n📈 Final State:")
    print(f"   - Total concepts: {total_count}")
    print(f"   - Root concepts: {root_count}")

def main():
    """
    Main execution
    """
    print("GPT-5 EXPLICIT CONCEPT MAPPING")
    print("This will send ALL concepts with IDs and require complete mapping")
    print("")
    
    # Send to GPT-5 with explicit requirements
    result, id_to_slug = asyncio.run(send_with_ids_to_gpt5())
    
    if result:
        # Apply the mapping
        apply_explicit_mapping(result, id_to_slug)
        
        print("\n" + "="*70)
        print("✅ COMPLETE REORGANIZATION FINISHED!")
        print("="*70)
        print("\nYour tag system has been fully reorganized.")
        print("Check the Tags page to see the new structure!")
    else:
        print("\n❌ Failed to get complete mapping from GPT-5")

if __name__ == "__main__":
    main()