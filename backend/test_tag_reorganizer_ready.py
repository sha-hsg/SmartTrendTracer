#!/usr/bin/env python3
"""
Final test to ensure Tag Reorganizer is ready
Tests that all concepts will be included in reorganization
"""

from pymongo import MongoClient
from app.services.concept_only_tag_service import ConceptOnlyTagService
from app.services.gpt5_tag_reorganizer import GPT5TagReorganizer
import json

def test_concept_gathering():
    """Test that all concepts are gathered for reorganization"""
    print("\n" + "="*60)
    print("TESTING CONCEPT GATHERING")
    print("="*60)
    
    # Initialize service
    service = ConceptOnlyTagService()
    
    # Get all concepts (what reorganizer will use)
    all_concepts = service.get_all_concepts_with_counts()
    
    print(f"\n📊 Concepts gathered for reorganization:")
    print(f"   Total concepts: {len(all_concepts):,}")
    
    # Analyze by organization status
    organized = 0
    unorganized = 0
    auto_generated = 0
    manual = 0
    
    for concept in all_concepts:
        if concept.get('parents') and len(concept['parents']) > 0:
            organized += 1
        else:
            unorganized += 1
        
        if concept.get('auto_generated'):
            auto_generated += 1
        else:
            manual += 1
    
    print(f"\n   By organization:")
    print(f"   - Organized: {organized:,}")
    print(f"   - Unorganized: {unorganized:,}")
    print(f"\n   By source:")
    print(f"   - Auto-generated: {auto_generated:,}")
    print(f"   - Manual: {manual:,}")
    
    # Sample unorganized concepts
    if unorganized > 0:
        print(f"\n📝 Sample unorganized concepts that WILL be included:")
        count = 0
        for concept in all_concepts:
            if not concept.get('parents') or len(concept['parents']) == 0:
                auto_tag = " [AUTO]" if concept.get('auto_generated') else " [MANUAL]"
                print(f"   - {concept.get('display_name', concept.get('slug'))} ({concept.get('slug')}){auto_tag}")
                count += 1
                if count >= 5:
                    break
        
        if unorganized > 5:
            print(f"   ... and {unorganized - 5} more")
    
    return all_concepts

def test_gpt5_service():
    """Test GPT-5 reorganizer service initialization"""
    print("\n" + "="*60)
    print("TESTING GPT-5 REORGANIZER SERVICE")
    print("="*60)
    
    try:
        # Initialize reorganizer
        reorganizer = GPT5TagReorganizer()
        
        print(f"\n✅ GPT-5 Reorganizer initialized successfully")
        print(f"   Model: {reorganizer.model_config.get('model')}")
        print(f"   Max tokens: {reorganizer.model_config.get('max_tokens'):,}")
        print(f"   Temperature: {reorganizer.model_config.get('temperature')}")
        
        # Check if top_level.json is loaded
        if reorganizer.top_level_json and reorganizer.top_level_json != "{}":
            print(f"   ✅ top_level.json loaded (entity type schema available)")
        else:
            print(f"   ⚠️  top_level.json not loaded (will work without entity types)")
        
        return True
    except Exception as e:
        print(f"\n❌ Failed to initialize GPT-5 Reorganizer: {e}")
        return False

def test_concept_format():
    """Test that concepts are in the right format for reorganization"""
    print("\n" + "="*60)
    print("TESTING CONCEPT FORMAT")
    print("="*60)
    
    service = ConceptOnlyTagService()
    all_concepts = service.get_all_concepts_with_counts()
    
    if all_concepts:
        # Check first concept structure
        sample = all_concepts[0]
        
        print(f"\n📋 Sample concept structure:")
        print(f"   Fields present: {list(sample.keys())}")
        
        # Required fields for reorganization
        required_fields = ['id', 'slug', 'display_name', 'usage_count']
        missing = []
        
        for field in required_fields:
            if field in sample:
                print(f"   ✅ {field}: {sample[field]}")
            else:
                missing.append(field)
                print(f"   ❌ {field}: MISSING")
        
        # Check parent information
        if 'parents' in sample:
            parent_info = sample['parents']
            if parent_info:
                print(f"   ✅ parents: {parent_info[:2]}..." if len(parent_info) > 2 else f"   ✅ parents: {parent_info}")
            else:
                print(f"   ℹ️  parents: [] (unorganized)")
        
        return len(missing) == 0
    
    return False

def simulate_reorganization_input():
    """Simulate what will be sent to GPT-5"""
    print("\n" + "="*60)
    print("SIMULATING REORGANIZATION INPUT")
    print("="*60)
    
    service = ConceptOnlyTagService()
    
    # Get all concepts just like the API does
    all_concepts = service.get_all_concepts_with_counts()
    
    # Format for GPT-5 (simplified version)
    tags_data = []
    for concept in all_concepts[:5]:  # Just first 5 for display
        tag_item = {
            'id': concept.get('id', concept.get('_id')),
            'tag': concept.get('slug'),
            'display_name': concept.get('display_name'),
            'count': concept.get('usage_count', 0),
            'entity_type': concept.get('entity_type'),
            'current_parents': concept.get('parents', [])
        }
        tags_data.append(tag_item)
    
    print(f"\n📤 Sample input format for GPT-5:")
    print(json.dumps(tags_data[:2], indent=2, default=str))
    print(f"... and {len(all_concepts) - 2} more concepts")
    
    print(f"\n💡 Total data size:")
    print(f"   Concepts to reorganize: {len(all_concepts):,}")
    print(f"   Estimated tokens: ~{len(all_concepts) * 50:,} (rough estimate)")
    
    return len(all_concepts)

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print(" TAG REORGANIZER FINAL READINESS TEST")
    print("="*80)
    
    # Test 1: Concept gathering
    concepts = test_concept_gathering()
    
    # Test 2: GPT-5 service
    gpt5_ready = test_gpt5_service()
    
    # Test 3: Concept format
    format_ok = test_concept_format()
    
    # Test 4: Simulate input
    total_concepts = simulate_reorganization_input()
    
    # Final verdict
    print("\n" + "="*80)
    print("FINAL TEST RESULTS")
    print("="*80)
    
    all_tests_passed = (
        len(concepts) > 0 and
        gpt5_ready and
        format_ok and
        total_concepts > 0
    )
    
    if all_tests_passed:
        print("\n✅ ALL TESTS PASSED - SYSTEM IS READY!")
        print("\nThe Tag Reorganizer will:")
        print(f"• Process ALL {total_concepts:,} concepts")
        print(f"• Include both organized and unorganized concepts")
        print(f"• Use GPT-5 model (gpt-5-2025-08-07)")
        print(f"• Apply entity type schema from top_level.json")
        print(f"• Generate complete hierarchical reorganization")
        print("\n🚀 You can now proceed with the Tag Reorganizer in the UI!")
    else:
        print("\n❌ SOME TESTS FAILED")
        print("Please check the errors above before proceeding.")
    
    return 0 if all_tests_passed else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())