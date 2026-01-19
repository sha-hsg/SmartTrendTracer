#!/usr/bin/env python3
"""Test improved paper tag suggestions"""

import sys
import os
import requests
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_paper_tag_suggestions(paper_id: int = 1):
    """Test tag suggestions for a paper"""
    
    # Get paper details first
    response = requests.get(f"http://localhost:8000/api/papers/{paper_id}")
    if response.status_code == 404:
        print(f"Paper {paper_id} not found")
        return
    
    paper = response.json()
    print(f"Testing tag suggestions for paper {paper_id}")
    print(f"Title: {paper['title'][:80]}...")
    print(f"Current tags: {paper.get('tags', [])}")
    print("-" * 50)
    
    # Get tag suggestions
    response = requests.post(f"http://localhost:8000/api/papers/{paper_id}/tags/suggest")
    
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        return
    
    suggestions = response.json()
    
    print(f"\n📊 RESULTS:")
    print(f"Model used: {suggestions.get('model_used', 'Unknown')}")
    print(f"Total suggestions: {suggestions.get('total_suggestions', 0)}")
    
    # Show existing similar tags
    existing = suggestions.get('existing_suggestions', [])
    if existing:
        print(f"\n🔍 Similar Existing Tags ({len(existing)}):")
        for i, tag in enumerate(existing[:10], 1):
            score = f"{tag.get('score', 0)*100:.1f}%" if tag.get('score') else "N/A"
            usage = tag.get('usage_count', 0)
            print(f"  {i:2}. {tag['tag']:<30} (Similarity: {score}, Used: {usage} times)")
    else:
        print("\n🔍 No similar existing tags found")
    
    # Show AI-generated suggestions
    new_tags = suggestions.get('new_suggestions', [])
    if new_tags:
        print(f"\n✨ AI-Generated Suggestions ({len(new_tags)}):")
        for i, tag in enumerate(new_tags[:10], 1):
            print(f"  {i:2}. {tag['tag']}")
    else:
        print("\n✨ No AI-generated suggestions")
    
    # Show already tagged
    already = suggestions.get('already_tagged', [])
    if already:
        print(f"\n✅ Already Tagged ({len(already)}):")
        print(f"  {', '.join(already)}")

if __name__ == "__main__":
    # Test with paper ID from command line or default to 1
    paper_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    test_paper_tag_suggestions(paper_id)