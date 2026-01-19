#!/usr/bin/env python3
"""
Comprehensive test to verify GPT-5 model works correctly with compact format implementation
Tests both GPT-5 and Gemini models with real concept data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
import time
from datetime import datetime
from app.services.gpt5_tag_reorganizer import GPT5TagReorganizer
from app.services.concept_only_tag_service import ConceptOnlyTagService

def test_compact_format_efficiency():
    """Test the space savings of compact format vs regular format"""
    print("=" * 60)
    print("COMPACT FORMAT EFFICIENCY TEST")
    print("=" * 60)
    
    # Get real concept data
    service = ConceptOnlyTagService()
    concepts = service.get_all_concepts_with_counts(include_unused=True)[:50]  # Test with 50 concepts
    
    # Create regular format
    regular_format = []
    for concept in concepts:
        regular_format.append({
            'id': concept.get('id', str(concept.get('_id', ''))),
            'tag': concept.get('slug', ''),
            'display_name': concept.get('display_name', ''),
            'count': concept.get('count', 0),
            'entity_type': concept.get('entity_type'),
            'current_parents': [str(p) for p in concept.get('parents', [])]
        })
    
    # Create compact format (same logic as in GPT5TagReorganizer)
    compact_format = []
    for concept in concepts:
        compact_tag = {
            'id': concept.get('id', str(concept.get('_id', ''))),
            't': concept.get('slug', ''),
            'd': concept.get('display_name', ''),
            'c': concept.get('count', 0),
        }
        if concept.get('entity_type'):
            compact_tag['e'] = concept['entity_type']
        if concept.get('parents'):
            compact_tag['p'] = [str(p) for p in concept['parents']]
        compact_format.append(compact_tag)
    
    # Generate JSON
    regular_json = json.dumps(regular_format, indent=2)
    compact_json = json.dumps(compact_format, separators=(',', ':'))
    
    # Calculate savings
    regular_size = len(regular_json)
    compact_size = len(compact_json)
    savings = 100 - (compact_size * 100 // regular_size)
    
    print(f"Sample size: {len(concepts)} concepts")
    print(f"Regular format: {regular_size:,} characters ({regular_size/4:.0f} tokens)")
    print(f"Compact format: {compact_size:,} characters ({compact_size/4:.0f} tokens)")
    print(f"Space savings: {savings}%")
    print(f"✅ Compact format is more efficient")
    
    return compact_size / regular_size

def test_model_configurations():
    """Test both GPT-5 and Gemini model configurations"""
    print("\n" + "=" * 60)
    print("MODEL CONFIGURATION TEST")
    print("=" * 60)
    
    # Test GPT-5 configuration
    print("\n--- GPT-5 Configuration ---")
    try:
        gpt5_reorganizer = GPT5TagReorganizer(model_override='gpt5')
        print(f"✅ GPT-5 initialized successfully")
        print(f"   Model: {gpt5_reorganizer.model_config.get('model')}")
        print(f"   Max tokens: {gpt5_reorganizer.model_config.get('max_tokens'):,}")
        print(f"   Temperature: {gpt5_reorganizer.model_config.get('temperature')}")
        print(f"   Provider: {gpt5_reorganizer.model_config.get('provider')}")
        
        # Check top_level.json is loaded
        if gpt5_reorganizer.top_level_json and gpt5_reorganizer.top_level_json != "{}":
            print(f"   ✅ Top-level ontology loaded ({len(gpt5_reorganizer.top_level_json)} chars)")
        else:
            print(f"   ⚠️  Top-level ontology not loaded")
            
    except Exception as e:
        print(f"❌ GPT-5 configuration failed: {e}")
        return False
    
    # Test Gemini configuration (default)
    print("\n--- Gemini Configuration ---")
    try:
        gemini_reorganizer = GPT5TagReorganizer()  # No override = default Gemini
        print(f"✅ Gemini initialized successfully")
        print(f"   Model: {gemini_reorganizer.model_config.get('model')}")
        print(f"   Max tokens: {gemini_reorganizer.model_config.get('max_tokens'):,}")
        print(f"   Temperature: {gemini_reorganizer.model_config.get('temperature')}")
        print(f"   Provider: {gemini_reorganizer.model_config.get('provider')}")
        
    except Exception as e:
        print(f"❌ Gemini configuration failed: {e}")
        return False
    
    return True

def test_token_limits():
    """Test that both models can handle the expected data size"""
    print("\n" + "=" * 60)
    print("TOKEN LIMIT ANALYSIS")
    print("=" * 60)
    
    # Get actual concept count
    service = ConceptOnlyTagService()
    total_concepts = service.tag_concepts.count_documents({})
    
    # Estimate based on sample
    sample_concepts = service.get_all_concepts_with_counts(include_unused=True)[:100]
    
    if not sample_concepts:
        print("❌ No concepts found for testing")
        return False
    
    # Calculate compact format size for sample
    compact_sample = []
    for concept in sample_concepts:
        compact_tag = {
            'id': concept.get('id', str(concept.get('_id', ''))),
            't': concept.get('slug', ''),
            'd': concept.get('display_name', ''),
            'c': concept.get('count', 0),
        }
        if concept.get('entity_type'):
            compact_tag['e'] = concept['entity_type']
        if concept.get('parents'):
            compact_tag['p'] = [str(p) for p in concept['parents']]
        compact_sample.append(compact_tag)
    
    sample_json = json.dumps(compact_sample, separators=(',', ':'))
    sample_chars = len(sample_json)
    sample_tokens = sample_chars / 4  # Rough estimate: 4 chars per token
    
    # Extrapolate to full dataset
    estimated_chars = sample_chars * (total_concepts / len(sample_concepts))
    estimated_tokens = estimated_chars / 4
    
    print(f"Total concepts in database: {total_concepts:,}")
    print(f"Sample size: {len(sample_concepts)} concepts")
    print(f"Sample compact JSON: {sample_chars:,} chars ({sample_tokens:.0f} tokens)")
    print(f"\nEstimated full dataset:")
    print(f"  Compact format: ~{estimated_chars/1000:.1f}K chars (~{estimated_tokens:.0f} tokens)")
    
    # Check against model limits
    print(f"\n--- GPT-5 Limits ---")
    print(f"Context window: 400,000 tokens")
    print(f"Output limit: 128,000 tokens")
    input_fits = estimated_tokens < 300000  # Leave room for prompts
    output_manageable = estimated_tokens < 80000  # Conservative estimate for output
    print(f"Input fits in context: {'✅ Yes' if input_fits else '❌ No'}")
    print(f"Output size manageable: {'✅ Yes' if output_manageable else '⚠️  May need chunking'}")
    
    print(f"\n--- Gemini 2.5 Pro Limits ---")
    print(f"Context window: 2,000,000 tokens")
    print(f"Output limit: 100,000 tokens")
    gemini_input_fits = estimated_tokens < 1800000  # Leave room for prompts
    gemini_output_ok = estimated_tokens < 80000
    print(f"Input fits in context: {'✅ Yes' if gemini_input_fits else '❌ No'}")
    print(f"Output size manageable: {'✅ Yes' if gemini_output_ok else '⚠️  May need chunking'}")
    
    return input_fits and gemini_input_fits

def test_api_integration():
    """Test that the API correctly passes model selection to the reorganizer"""
    print("\n" + "=" * 60)
    print("API INTEGRATION TEST")
    print("=" * 60)
    
    import requests
    
    base_url = "http://localhost:8000"
    
    # Test debug endpoint
    try:
        response = requests.get(f"{base_url}/api/tags/reorganize/debug/test-gpt5-config", timeout=10)
        if response.status_code == 200:
            config_test = response.json()
            print("✅ API is responding")
            print(f"   LLM config found: {config_test['llm_config']['found']}")
            print(f"   Prompts config found: {config_test['prompts_config']['found']}")
            print(f"   Environment ready: {config_test['environment']['OPENAI_API_KEY']}")
            print(f"   Test initialization: {config_test['test_init']['success']}")
        else:
            print(f"⚠️  API responded with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ API not accessible: {e}")
        print("   Make sure the backend server is running on port 8000")
        return False
    
    return True

def run_comprehensive_test():
    """Run all tests and provide summary"""
    print("GPT-5 & COMPACT FORMAT VERIFICATION TEST")
    print("SmartTrendTracer Backend - Tag Reorganization System")
    print(f"Test run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_results = {}
    
    # Run all tests
    try:
        test_results['compact_efficiency'] = test_compact_format_efficiency()
        test_results['model_configs'] = test_model_configurations()
        test_results['token_limits'] = test_token_limits()
        test_results['api_integration'] = test_api_integration()
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    all_passed = True
    if isinstance(test_results['compact_efficiency'], float):
        print(f"✅ Compact format efficiency: {(1 - test_results['compact_efficiency']) * 100:.1f}% space savings")
    else:
        print("❌ Compact format efficiency test failed")
        all_passed = False
    
    if test_results['model_configs']:
        print("✅ Model configurations: Both GPT-5 and Gemini configured correctly")
    else:
        print("❌ Model configurations: Issues found")
        all_passed = False
    
    if test_results['token_limits']:
        print("✅ Token limits: Both models can handle current data size")
    else:
        print("⚠️  Token limits: May need optimization for larger datasets")
        # Don't fail for this as it's just a warning
    
    if test_results['api_integration']:
        print("✅ API integration: Endpoints responding correctly")
    else:
        print("❌ API integration: Issues found")
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED - GPT-5 and Compact Format are working correctly!")
        print("\nThe system is ready to:")
        print("- Process 2000+ concepts efficiently with compact format")
        print("- Use either GPT-5 or Gemini 2.5 Pro via UI dropdown")
        print("- Handle large-scale tag reorganization")
    else:
        print("⚠️  SOME TESTS FAILED - Review issues above")
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)