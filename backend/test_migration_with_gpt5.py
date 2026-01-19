#!/usr/bin/env python3
"""
Test migration with GPT-5 directly (without user input)
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from migrate_to_concept_structure import TagConceptMigrator

def test_migration():
    """Test migration with AI reorganization"""
    print("=" * 60)
    print("Testing Tag Migration with GPT-5")
    print("=" * 60)
    
    migrator = TagConceptMigrator()
    
    # Test with a small subset of tags first
    print("\nTesting with small subset to verify GPT-5 is called...")
    print("NOTE: This will actually call GPT-5 API (costs money)")
    print("-" * 60)
    
    # Get a small sample of tags
    sample_tags = migrator._collect_all_tags()[:10]  # Just 10 tags
    
    if sample_tags:
        print(f"Found {len(sample_tags)} sample tags:")
        for tag in sample_tags:
            print(f"  - {tag['tag']}: {tag['total_count']} uses")
        
        print("\nAttempting GPT-5 reorganization...")
        result = migrator._ai_reorganize_tags(sample_tags)
        
        if result and result.get('concepts'):
            print(f"✅ GPT-5 successfully returned {len(result['concepts'])} concepts!")
            print(f"✅ Created {len(result.get('aliases', []))} aliases")
            
            # Show sample concept
            if result['concepts']:
                sample = result['concepts'][0]
                print(f"\nSample concept:")
                print(f"  ID: {sample.get('id')}")
                print(f"  Slug: {sample.get('slug')}")
                print(f"  Display: {sample.get('display_name')}")
                print(f"  Entity Type: {sample.get('entity_type')}")
        else:
            print("❌ GPT-5 reorganization failed or returned no concepts")
            print("This might be due to:")
            print("  1. API key not configured")
            print("  2. Rate limiting")
            print("  3. Model not available")
    else:
        print("No tags found to test with")
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("If GPT-5 worked, you can run the full migration with:")
    print("  python migrate_to_concept_structure.py")
    print("And choose 'y' for AI reorganization")
    print("=" * 60)

if __name__ == "__main__":
    test_migration()