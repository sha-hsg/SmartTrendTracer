#!/usr/bin/env python3
"""
Test applying GPT-5 recommendations to the concept system
"""

import json
import requests
from pathlib import Path

def load_latest_gpt5_response():
    """Load the most recent GPT-5 response"""
    response_dir = Path('data/gpt5_responses')
    files = list(response_dir.glob('gpt5_success_*.txt'))
    
    if not files:
        print("No GPT-5 response files found")
        return None
    
    # Get the latest file
    latest_file = max(files, key=lambda f: f.stat().st_mtime)
    print(f"Loading recommendations from: {latest_file.name}")
    
    with open(latest_file, 'r') as f:
        lines = f.readlines()
        # Skip header (first 4 lines)
        json_text = ''.join(lines[4:])
        return json.loads(json_text)

def test_apply_recommendations():
    """Test applying recommendations via API"""
    
    # Load recommendations
    recommendations = load_latest_gpt5_response()
    if not recommendations:
        return
    
    print(f"\nRecommendations summary:")
    print(f"- Concepts: {len(recommendations.get('concepts', []))}")
    print(f"- Aliases: {len(recommendations.get('aliases', []))}")
    print(f"- Root categories: {len(recommendations.get('root_categories', []))}")
    
    # Show sample concepts
    print("\nSample concepts to be created:")
    for concept in recommendations.get('concepts', [])[:5]:
        print(f"  - {concept.get('display_name')} ({concept.get('slug')})")
    
    # Ask for confirmation
    response = input("\nApply these recommendations? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled")
        return
    
    # Apply via API
    print("\nApplying recommendations...")
    
    try:
        response = requests.post(
            'http://localhost:8000/api/tag-reorganization/apply',
            json=recommendations,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Success!")
            print(f"\nResults:")
            stats = result.get('stats', {})
            print(f"  - Concepts created: {stats.get('concepts_created', 0)}")
            print(f"  - Aliases created: {stats.get('aliases_created', 0)}")
            print(f"  - Hierarchy links: {stats.get('hierarchy_links', 0)}")
            print(f"  - Tags mapped: {stats.get('tags_mapped', 0)}")
            
            if stats.get('errors'):
                print(f"\n⚠️ Errors encountered: {len(stats['errors'])}")
                for error in stats['errors'][:5]:
                    print(f"  - {error}")
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")

def check_current_concepts():
    """Check current concepts in the system"""
    from pymongo import MongoClient
    
    client = MongoClient('mongodb://localhost:27017/')
    db = client.smarttrendtracer
    
    print("\nCurrent concept statistics:")
    print(f"- Total concepts: {db.tag_concepts_v2.count_documents({})}")
    print(f"- Total aliases: {db.tag_aliases_v2.count_documents({})}")
    print(f"- Total tag instances: {db.tag_instances.count_documents({})}")
    print(f"- Orphan tags: {db.tag_instances.count_documents({'concept_id': None})}")
    
    # Show root concepts
    root_concepts = list(db.tag_concepts_v2.find({'parents': []}).limit(10))
    if root_concepts:
        print("\nCurrent root concepts:")
        for concept in root_concepts:
            print(f"  - {concept.get('display_name', concept.get('slug'))}")

if __name__ == "__main__":
    print("GPT-5 Recommendations Application Test")
    print("=" * 50)
    
    # Check current state
    check_current_concepts()
    
    # Test applying recommendations
    test_apply_recommendations()
    
    # Check state after
    print("\n" + "=" * 50)
    check_current_concepts()