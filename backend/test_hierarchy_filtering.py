#!/usr/bin/env python3
"""
Test that the hierarchy filtering is working
"""

from app.models import get_db, Tag
from app.models.tag_ontology import TagOntologyService, TagConcept
import requests

def test_hierarchy_filtering():
    """Test that parent tags include children in filtering"""
    
    db = next(get_db())
    service = TagOntologyService(db)
    
    print("🧪 Testing Hierarchy Filtering")
    print("=" * 60)
    
    # Get the root concepts
    root_concepts = db.query(TagConcept).filter(TagConcept.parent_id.is_(None)).all()
    
    print(f"\n📁 Root Categories in Hierarchy ({len(root_concepts)}):")
    for concept in root_concepts:
        print(f"  - {concept.display_name}")
    
    # Test filtering with a parent category
    test_tag = "AI_Models_And_Platforms"
    concept = db.query(TagConcept).filter(TagConcept.tag == test_tag).first()
    
    if concept:
        print(f"\n🔍 Testing with: {concept.display_name} ({test_tag})")
        
        # Get all tags that would be included
        mapped_tags = service.get_tags_for_filtering(test_tag)
        print(f"  This maps to {len(mapped_tags)} tags")
        
        # Test the API endpoint
        try:
            response = requests.get(f"http://localhost:8000/api/tweets?tag={test_tag}&limit=5")
            if response.status_code == 200:
                tweets = response.json()
                print(f"  API returns {len(tweets)} tweets")
                
                if tweets:
                    print("\n  Sample tweets:")
                    for tweet in tweets[:3]:
                        tags = [t['tag'] for t in tweet.get('tags', [])]
                        print(f"    - @{tweet['author_username']}: {tweet['text'][:50]}...")
                        print(f"      Tags: {', '.join(tags[:5])}")
            else:
                print(f"  ❌ API error: {response.status_code}")
        except Exception as e:
            print(f"  ❌ Error testing API: {e}")
    
    # Show what the UI tag cloud sees
    print("\n📊 What the Tag Cloud Shows (raw tags):")
    popular_tags = db.query(Tag.tag, db.func.count(Tag.id).label('count'))\
                     .group_by(Tag.tag)\
                     .order_by(db.desc('count'))\
                     .limit(10)\
                     .all()
    
    for tag, count in popular_tags:
        print(f"  - {tag}: {count} tweets")
    
    print("\n💡 The Issue:")
    print("  The Tag Cloud shows RAW TAGS from tweets (what you see)")
    print("  The HIERARCHY works for filtering but isn't visible in the cloud")
    print("\n  To see hierarchy working:")
    print("  1. URL: http://localhost:8000/api/tweets?tag=AI_Models_And_Platforms")
    print("  2. This SHOULD return tweets tagged with GPT, Claude, etc.")
    
    db.close()

if __name__ == "__main__":
    test_hierarchy_filtering()