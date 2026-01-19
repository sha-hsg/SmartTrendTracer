#!/usr/bin/env python3
"""
Send ALL concepts to GPT-5 for complete reorganization
This time we send EVERYTHING - all 1,686 concepts with full details!
"""

import json
import asyncio
import logging
from datetime import datetime
from pymongo import MongoClient
from app.services.gpt5_tag_reorganizer import GPT5TagReorganizer
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def prepare_all_concepts_for_gpt5():
    """
    Prepare ALL concepts with complete information for GPT-5
    """
    client = MongoClient('mongodb://localhost:27017/')
    db = client.smarttrendtracer
    
    # Get ALL concepts - no filtering!
    all_concepts = list(db.tag_concepts_v2.find())
    
    print(f"Preparing {len(all_concepts)} concepts for GPT-5...")
    
    # Prepare complete concept data
    concepts_data = []
    
    for concept in all_concepts:
        # Count usage
        usage_count = db.tag_instances.count_documents({
            'concept_id': str(concept['_id'])
        })
        
        # Get parent names
        parent_names = []
        for parent_id in concept.get('parents', []):
            parent = db.tag_concepts_v2.find_one({'_id': parent_id})
            if parent:
                parent_names.append(parent.get('slug', str(parent_id)))
        
        # Get child names
        child_names = []
        for child_id in concept.get('children', []):
            child = db.tag_concepts_v2.find_one({'_id': child_id})
            if child:
                child_names.append(child.get('slug', str(child_id)))
        
        # Get aliases
        aliases = list(db.tag_aliases_v2.find({'concept_id': concept['_id']}))
        alias_texts = [a['alias_text'] for a in aliases]
        
        # Build comprehensive concept data
        concept_data = {
            'id': concept.get('id', str(concept['_id'])),
            'slug': concept.get('slug', ''),
            'display_name': concept.get('display_name', concept.get('slug', '')),
            'description': concept.get('description', ''),
            'entity_type': concept.get('entity_type', 'concept'),
            'current_parents': parent_names,
            'current_children': child_names,
            'aliases': alias_texts,
            'usage_count': usage_count,
            'status': concept.get('status', 'active')
        }
        
        concepts_data.append(concept_data)
    
    # Sort by usage count to help GPT-5 prioritize
    concepts_data.sort(key=lambda x: x['usage_count'], reverse=True)
    
    return concepts_data

def create_gpt5_prompt(concepts_data):
    """
    Create a comprehensive prompt for GPT-5 to reorganize ALL concepts
    """
    
    # Statistics
    total_concepts = len(concepts_data)
    root_concepts = len([c for c in concepts_data if not c['current_parents']])
    total_usage = sum(c['usage_count'] for c in concepts_data)
    
    prompt = f"""You are organizing a complete tag taxonomy system. You have been given ALL {total_concepts} concepts that exist in the system.

CURRENT STATE:
- Total concepts: {total_concepts}
- Root-level concepts (no parents): {root_concepts}
- Total usage across all concepts: {total_usage}

YOUR TASK:
1. Review ALL {total_concepts} concepts provided
2. Create a clean, logical hierarchy with 8-12 main root categories
3. Organize EVERY SINGLE concept under appropriate parents
4. Identify and merge duplicate/similar concepts
5. Ensure NO concept is left unmapped or orphaned

REQUIREMENTS:
- Every concept MUST be placed in the hierarchy (all {total_concepts} of them)
- Create clear parent-child relationships
- Merge similar concepts (e.g., "GPT-4", "gpt4", "GPT 4" should become one)
- Use the most common/clear name as the canonical form
- Preserve important distinctions (e.g., different model versions)

OUTPUT FORMAT:
Return a JSON object with:
{{
  "root_categories": ["list of root category slugs"],
  "concepts": [
    {{
      "id": "unique_id",
      "slug": "concept-slug",
      "display_name": "Display Name",
      "description": "Description",
      "parents": ["parent_ids"],
      "entity_type": "type",
      "merge_from": ["list of concept slugs that should merge into this one"]
    }}
  ],
  "merge_map": {{
    "old_slug": "new_slug"  // Maps old concepts to their new merged forms
  }},
  "statistics": {{
    "original_count": {total_concepts},
    "final_count": 0,
    "merged_count": 0,
    "root_categories": 0
  }}
}}

IMPORTANT: 
- You MUST process all {total_concepts} concepts
- The merge_map MUST account for every concept that gets merged
- No concept should be deleted, only merged or reorganized
"""
    
    return prompt

async def send_to_gpt5_async():
    """
    Send all concepts to GPT-5 and save the response
    """
    print("\n" + "="*60)
    print("SENDING ALL CONCEPTS TO GPT-5 FOR COMPLETE REORGANIZATION")
    print("="*60)
    
    # Prepare all concepts
    concepts_data = prepare_all_concepts_for_gpt5()
    
    print(f"\n📊 Prepared {len(concepts_data)} concepts")
    print(f"📝 Top 10 concepts by usage:")
    for concept in concepts_data[:10]:
        print(f"   - {concept['display_name']}: {concept['usage_count']} uses")
    
    # Create tags data for GPT-5
    tags_data = []
    for concept in concepts_data:
        tags_data.append({
            'tag': concept['slug'],
            'count': concept['usage_count'],
            'display_name': concept['display_name'],
            'current_parents': concept['current_parents'],
            'aliases': concept['aliases']
        })
    
    print(f"\n🚀 Sending to GPT-5...")
    print(f"   Estimated tokens: ~{len(json.dumps(tags_data)) // 4}")
    
    # Initialize GPT-5 reorganizer
    reorganizer = GPT5TagReorganizer()
    
    # Track progress
    def progress_callback(msg):
        print(f"   📍 {msg}")
    
    # Send to GPT-5
    start_time = datetime.now()
    print(f"\n⏰ Started at: {start_time.strftime('%H:%M:%S')}")
    print("   This will take 10-20 minutes. Please wait...")
    
    try:
        result = reorganizer.reorganize_tags(tags_data, progress_callback=progress_callback)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\n✅ GPT-5 responded in {elapsed:.1f} seconds!")
        
        # Save the response
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        response_file = f"data/gpt5_responses/gpt5_complete_reorg_{timestamp}.json"
        
        Path("data/gpt5_responses").mkdir(parents=True, exist_ok=True)
        
        with open(response_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\n💾 Response saved to: {response_file}")
        
        # Show summary
        if result and 'concepts' in result:
            print(f"\n📊 GPT-5 Reorganization Summary:")
            print(f"   - Concepts organized: {len(result.get('concepts', []))}")
            print(f"   - Root categories: {len(result.get('root_categories', []))}")
            print(f"   - Merge proposals: {len(result.get('merge_proposals', []))}")
            print(f"   - Aliases created: {len(result.get('aliases', []))}")
            
            print(f"\n🎯 Root Categories Created:")
            for cat in result.get('root_categories', [])[:15]:
                print(f"   - {cat}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """
    Main execution
    """
    print("GPT-5 COMPLETE CONCEPT REORGANIZATION")
    print("This will send ALL 1,686 concepts to GPT-5")
    print("")
    
    # Run async function
    result = asyncio.run(send_to_gpt5_async())
    
    if result:
        print("\n" + "="*60)
        print("✅ SUCCESS! GPT-5 has reorganized ALL concepts!")
        print("="*60)
        print("\nNext steps:")
        print("1. Review the reorganization in the saved file")
        print("2. Apply the reorganization using the comprehensive apply function")
        print("3. Your tag system will be completely reorganized!")
    else:
        print("\n❌ Failed to get reorganization from GPT-5")

if __name__ == "__main__":
    main()