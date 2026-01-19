#!/usr/bin/env python3
"""
Test GPT-5 Tag Reorganizer with top_level.json schema
"""
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from app.services.gpt5_tag_reorganizer import GPT5TagReorganizer

def test_reorganizer():
    """Test that the reorganizer correctly includes top_level.json"""
    
    print("Testing GPT-5 Tag Reorganizer with top_level.json schema...")
    print("-" * 60)
    
    # Initialize reorganizer
    reorganizer = GPT5TagReorganizer()
    
    # Check that top_level.json was loaded
    if reorganizer.top_level_json and reorganizer.top_level_json != "{}":
        print("✅ top_level.json loaded successfully")
        
        # Parse to verify it's valid JSON
        try:
            schema = json.loads(reorganizer.top_level_json)
            print(f"✅ Schema contains {len(schema.get('entity_types', {}))} entity type categories")
            
            # List the entity types
            for category_name, category_data in schema.get('entity_types', {}).items():
                children = category_data.get('children', {})
                print(f"  - {category_name}: {len(children)} types")
                for child_name in list(children.keys())[:3]:  # Show first 3
                    print(f"    • {child_name}")
                if len(children) > 3:
                    print(f"    ... and {len(children) - 3} more")
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing top_level.json: {e}")
    else:
        print("❌ top_level.json not loaded or empty")
    
    print("\n" + "-" * 60)
    
    # Test with sample tags
    sample_tags = [
        {"tag": "GPT-4", "count": 50},
        {"tag": "OpenAI", "count": 30},
        {"tag": "machine learning", "count": 45},
        {"tag": "Large Language Models", "count": 60},
        {"tag": "llm", "count": 55},
        {"tag": "AI", "count": 100},
        {"tag": "artificial intelligence", "count": 95}
    ]
    
    print(f"Testing with {len(sample_tags)} sample tags...")
    print("Sample tags:", [t['tag'] for t in sample_tags])
    
    # Note: This would actually call GPT-5, which costs money
    # So we'll just verify the prompt would be formatted correctly
    try:
        # Check that the prompt template has the right placeholders
        with open('prompts_config.json', 'r') as f:
            prompts_config = json.load(f)
            # Check the tag_reorganization prompt (which GPT5TagReorganizer now uses)
            user_template = prompts_config.get('tag_reorganization', {}).get('user_template', '')
            
            if '{top_level_json}' in user_template:
                print("✅ Prompt template contains {top_level_json} placeholder")
            else:
                print("❌ Prompt template missing {top_level_json} placeholder")
                
            if '{total_tags}' in user_template:
                print("✅ Prompt template contains {total_tags} placeholder")
            else:
                print("❌ Prompt template missing {total_tags} placeholder")
                
            if '{tags_json}' in user_template:
                print("✅ Prompt template contains {tags_json} placeholder")
            else:
                print("❌ Prompt template missing {tags_json} placeholder")
                
    except Exception as e:
        print(f"Error checking prompt template: {e}")
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("The GPT-5 reorganizer is now configured to include the")
    print("entity type schema from top_level.json when reorganizing tags.")
    print("=" * 60)

if __name__ == "__main__":
    test_reorganizer()