#!/usr/bin/env python3
"""
Test sending a single batch of concepts to GPT-5
"""

import json
import logging
from datetime import datetime
from pymongo import MongoClient
from app.services.gpt5_tag_reorganizer import GPT5TagReorganizer
from pathlib import Path
from langchain.schema import HumanMessage, SystemMessage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_single_batch():
    """
    Test with just 50 concepts to see if GPT-5 responds properly
    """
    print("\n" + "="*70)
    print("TEST: SINGLE BATCH TO GPT-5")
    print("="*70)
    
    client = MongoClient('mongodb://localhost:27017/')
    db = client.smarttrendtracer
    
    # Get first 50 concepts
    concepts = list(db.tag_concepts_v2.find().limit(50))
    
    print(f"\n📊 Testing with {len(concepts)} concepts")
    
    # Prepare concept data
    batch_data = []
    for concept in concepts:
        concept_id = str(concept['_id'])
        
        # Get usage count
        usage_count = db.tag_instances.count_documents({'concept_id': concept_id})
        
        # Get parent slugs
        parent_slugs = []
        for parent_id in concept.get('parents', []):
            parent = db.tag_concepts_v2.find_one({'_id': parent_id})
            if parent:
                parent_slugs.append(parent.get('slug', ''))
        
        batch_data.append({
            'mongodb_id': concept_id,
            'slug': concept.get('slug', ''),
            'display_name': concept.get('display_name', ''),
            'entity_type': concept.get('entity_type', 'concept'),
            'current_parents': parent_slugs,
            'usage_count': usage_count
        })
    
    # Sort by usage
    batch_data.sort(key=lambda x: x['usage_count'], reverse=True)
    
    # Create prompt
    system_prompt = """You are reorganizing a tag taxonomy. Map each concept to a logical category."""
    
    user_prompt = f"""Organize these {len(batch_data)} concepts into these root categories:

ROOT CATEGORIES:
1. fundamentals - AI/ML fundamentals and theory
2. models_and_architectures - Model families and architectures
3. techniques_and_methods - Training and inference techniques
4. data_and_datasets - Data and datasets
5. evaluation_and_benchmarks - Evaluation and benchmarks
6. applications_and_tasks - Applications and downstream tasks
7. ecosystem_and_industry - Organizations, events, industry
8. tools_and_standards - Software, frameworks, standards

For each concept, return:
{{
  "mongodb_id": "the_id",
  "action": "keep",
  "new_parent_slug": "category_slug"
}}

CONCEPTS:
{json.dumps(batch_data[:10], indent=2)}  // Showing first 10 for test

Return a JSON with "concept_mappings" array containing all mappings."""
    
    print("\n🚀 Sending test batch to GPT-5...")
    
    # Initialize GPT-5
    reorganizer = GPT5TagReorganizer()
    
    try:
        # Call GPT-5
        client = reorganizer.llm_service._get_client(reorganizer.model_config)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        start_time = datetime.now()
        print("   Waiting for GPT-5 response...")
        
        response = client.invoke(messages)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\n✅ GPT-5 responded in {elapsed:.1f} seconds!")
        
        # Get response text
        result_text = response.content if hasattr(response, 'content') else str(response)
        
        # Save response
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        response_file = f"data/gpt5_responses/test_batch_{timestamp}.txt"
        Path("data/gpt5_responses").mkdir(parents=True, exist_ok=True)
        
        with open(response_file, 'w') as f:
            f.write(result_text)
        
        print(f"💾 Response saved to: {response_file}")
        
        # Try to parse
        try:
            result = json.loads(result_text)
            if 'concept_mappings' in result:
                print(f"\n📊 Successfully parsed {len(result['concept_mappings'])} mappings")
            else:
                print("\n⚠️ Response doesn't contain concept_mappings")
        except:
            print("\n⚠️ Could not parse as JSON, checking response format...")
            print(f"Response preview: {result_text[:500]}...")
        
        return result_text
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_single_batch()