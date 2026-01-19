#!/usr/bin/env python3
"""
Send ALL concepts to GPT-5 in a SINGLE request for complete reorganization
This ensures GPT-5 can see all concepts and detect duplicates
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

def prepare_all_concepts() -> List[Dict[str, Any]]:
    """
    Prepare ALL concepts for GPT-5 in a single batch
    """
    client = MongoClient('mongodb://localhost:27017/')
    db = client.smarttrendtracer
    
    # Get ALL concepts
    all_concepts = list(db.tag_concepts_v2.find())
    logger.info(f"Found {len(all_concepts)} total concepts")
    
    concepts_data = []
    
    for concept in all_concepts:
        concept_id = str(concept['_id'])
        
        # Get usage count
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
        alias_texts = [a.get('alias', a.get('alias_text', '')) for a in aliases]
        
        # Get children count
        children_count = len(concept.get('children', []))
        
        # Build concept data WITH EXPLICIT ID
        concept_data = {
            'mongodb_id': concept_id,
            'slug': concept.get('slug', ''),
            'display_name': concept.get('display_name', ''),
            'description': concept.get('description', ''),
            'current_parents': parent_slugs,
            'entity_type': concept.get('entity_type', ''),
            'usage_count': usage_count,
            'children_count': children_count,
            'aliases': alias_texts,
            'is_root': len(concept.get('parents', [])) == 0,
            'created_by': concept.get('created_by', ''),
            'needs_review': concept.get('needs_review', False)
        }
        
        concepts_data.append(concept_data)
    
    client.close()
    return concepts_data

async def send_all_to_gpt5():
    """
    Send ALL concepts to GPT-5 in a single request
    """
    print("=" * 80)
    print("🚀 SENDING ALL CONCEPTS TO GPT-5 IN SINGLE REQUEST")
    print("=" * 80)
    
    # Prepare all concepts
    print("\n📊 Preparing all concepts...")
    all_concepts = prepare_all_concepts()
    
    total_concepts = len(all_concepts)
    root_concepts = sum(1 for c in all_concepts if c['is_root'])
    orphan_concepts = sum(1 for c in all_concepts if not c['current_parents'] and c['children_count'] == 0)
    
    print(f"\n📈 Statistics:")
    print(f"  Total concepts: {total_concepts}")
    print(f"  Root concepts: {root_concepts}")
    print(f"  Orphan concepts: {orphan_concepts}")
    print(f"  Total usage: {sum(c['usage_count'] for c in all_concepts)}")
    
    # Check size
    json_size = len(json.dumps(all_concepts))
    estimated_tokens = json_size // 4
    print(f"\n📏 Size estimation:")
    print(f"  JSON size: {json_size:,} characters")
    print(f"  Estimated tokens: {estimated_tokens:,}")
    
    if estimated_tokens > 400000:
        print("\n⚠️  WARNING: Input may exceed token limits!")
        print("   Consider using a model with larger context window")
        response = input("\n   Continue anyway? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            return
    
    # Initialize reorganizer
    print("\n🤖 Initializing GPT-5 reorganizer...")
    reorganizer = GPT5TagReorganizer()
    
    # Create response directory
    response_dir = Path('data/gpt5_responses')
    response_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    def progress_callback(msg: str):
        print(f"   {msg}")
    
    try:
        print("\n🔄 Sending request to GPT-5...")
        print("   This may take several minutes due to the large input size...")
        
        # Send ALL concepts in one request
        result = await reorganizer.reorganize_tags(
            all_concepts,
            progress_callback=progress_callback
        )
        
        if result:
            # Save the complete response
            output_file = response_dir / f'gpt5_complete_all_concepts_{timestamp}.json'
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            
            print(f"\n✅ Success! Response saved to: {output_file}")
            
            # Show statistics
            if 'categories' in result:
                print(f"\n📊 Reorganization Results:")
                print(f"  Root categories: {len(result['categories'])}")
                
                # Count concepts per category
                for cat in result['categories'][:5]:  # Show first 5
                    print(f"    - {cat.get('name', 'Unknown')}: {len(cat.get('concepts', []))} concepts")
                
                if len(result['categories']) > 5:
                    print(f"    ... and {len(result['categories']) - 5} more categories")
            
            # Check for duplicates detected
            if 'duplicate_merges' in result:
                print(f"\n🔄 Duplicate merges proposed: {len(result['duplicate_merges'])}")
                for merge in result['duplicate_merges'][:5]:
                    print(f"    - Merge {merge.get('duplicates', [])} into {merge.get('target', '')}")
            
            # Check for orphan assignments
            if 'orphan_assignments' in result:
                print(f"\n📌 Orphan assignments: {len(result['orphan_assignments'])}")
            
            print("\n" + "=" * 80)
            print("✅ COMPLETE! Review the output file and apply changes if satisfactory.")
            print("=" * 80)
            
        else:
            print("\n❌ Failed to get response from GPT-5")
            
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        
        # Save error
        error_file = response_dir / f'gpt5_error_all_{timestamp}.txt'
        with open(error_file, 'w') as f:
            f.write(f"Error: {str(e)}\n")
        print(f"   Error saved to: {error_file}")

def main():
    """
    Main entry point
    """
    print("\n" + "=" * 80)
    print("GPT-5 COMPLETE CONCEPT REORGANIZATION (SINGLE REQUEST)")
    print("=" * 80)
    print("\nThis script will send ALL concepts to GPT-5 in a single request.")
    print("This ensures GPT-5 can see duplicates and properly organize everything.")
    print("\n⚠️  WARNING: This will use a large number of tokens!")
    
    response = input("\nProceed? (yes/no): ")
    if response.lower() == 'yes':
        asyncio.run(send_all_to_gpt5())
    else:
        print("Aborted.")

if __name__ == "__main__":
    main()