#!/usr/bin/env python3
"""
Direct test of tag suggestion logic without API
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.vector_store_openai import get_vector_store
from app.services.llm_service import get_llm_service
from app.models import get_db, Tweet, Tag

load_dotenv()

def test_direct_suggestion():
    """Test tag suggestions directly"""
    
    db = next(get_db())
    vector_store = get_vector_store()
    llm_service = get_llm_service()
    
    # Get a test tweet
    tweet = db.query(Tweet).filter(
        ~Tweet.text.like('RT @%')
    ).order_by(Tweet.created_at.desc()).first()
    
    if not tweet:
        print("No tweet found")
        db.close()
        return
    
    # Get already tagged
    existing_tags_on_tweet = db.query(Tag.tag).filter(Tag.tweet_id == tweet.id).all()
    already_tagged = [t[0] for t in existing_tags_on_tweet]
    
    print("=" * 80)
    print("DIRECT TAG SUGGESTION TEST")
    print("=" * 80)
    
    print(f"\n📝 TWEET:")
    print(f"  Author: @{tweet.author_username}")
    print(f"  Text: {tweet.text[:150]}...")
    print(f"  Already tagged: {already_tagged if already_tagged else 'None'}")
    
    # 1. Search for similar existing tags
    print("\n" + "-" * 80)
    print("1️⃣ SEARCHING VECTOR STORE FOR SIMILAR TAGS...")
    print("-" * 80)
    
    search_results = vector_store.search_similar_tags(
        query_text=tweet.text,
        k=8,
        min_similarity=0.5
    )
    
    if search_results:
        print(f"Found {len(search_results)} similar tags:")
        similar_tags = []
        for tag, score, count in search_results:
            if tag not in already_tagged:
                similar_tags.append({
                    'tag': tag,
                    'score': round(score, 3),
                    'usage_count': count,
                    'type': 'existing'
                })
                print(f"  • {tag:<30} (similarity: {score*100:.1f}%, used: {count}x)")
        
        # Keep top 5
        similar_tags = similar_tags[:5]
    else:
        print("  No similar tags found in vector store")
        similar_tags = []
    
    # 2. Generate new tags with LLM
    print("\n" + "-" * 80)
    print("2️⃣ GENERATING NEW TAGS WITH LLM...")
    print("-" * 80)
    
    suggested_tags = llm_service.suggest_tags(
        tweet_text=tweet.text,
        author=tweet.author_username
    )
    
    # Check if API was used
    api_was_used = "__api_success__" in suggested_tags if suggested_tags else False
    if api_was_used:
        suggested_tags = [tag for tag in suggested_tags if tag != "__api_success__"]
        model_used = "gpt-4o-mini"
    else:
        model_used = "spacy-fallback"
    
    print(f"Model used: {model_used}")
    print(f"Generated {len(suggested_tags)} tags:")
    
    # Filter out duplicates
    similar_tag_names = [t['tag'] for t in similar_tags]
    new_tags = []
    for tag in suggested_tags:
        if tag not in already_tagged and tag not in similar_tag_names:
            new_tags.append({
                'tag': tag,
                'type': 'new',
                'model': model_used
            })
            print(f"  • {tag:<30} (model: {model_used})")
    
    # Keep top 5 new tags
    new_tags = new_tags[:5]
    
    # 3. Final results
    print("\n" + "=" * 80)
    print("📊 FINAL TAG SUGGESTIONS")
    print("=" * 80)
    
    print(f"\n🔍 EXISTING TAGS (from vector store): {len(similar_tags)}")
    for tag in similar_tags:
        print(f"  • {tag['tag']:<25} | Score: {tag['score']:.3f} | Used: {tag['usage_count']}x")
    
    print(f"\n✨ NEW TAGS (from LLM): {len(new_tags)}")
    for tag in new_tags:
        print(f"  • {tag['tag']:<25} | Model: {tag['model']}")
    
    print(f"\n📌 ALREADY TAGGED: {len(already_tagged)}")
    for tag in already_tagged:
        print(f"  • {tag}")
    
    print("\n" + "=" * 80)
    print("💡 HOW IT WORKS")
    print("=" * 80)
    print("1. Vector store searches 612 existing tags for semantic similarity")
    print("2. LLM generates new contextual tags based on tweet content")
    print("3. Both are presented separately in the UI:")
    print("   - Green tags = existing (with usage stats)")
    print("   - Purple tags = new AI-generated")
    print("4. Already tagged items are filtered out from suggestions")
    
    db.close()

if __name__ == "__main__":
    test_direct_suggestion()