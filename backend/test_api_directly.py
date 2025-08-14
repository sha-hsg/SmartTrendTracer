#!/usr/bin/env python3
"""Test the API directly to see what's happening"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import SessionLocal, Tweet, Tag, TagOntologyService
from sqlalchemy.orm import joinedload

def simulate_api_call(tag_param: str, use_ontology: bool = True):
    """Simulate exactly what the API does"""
    db = SessionLocal()
    
    print(f"\nSimulating API call with tag='{tag_param}', use_ontology={use_ontology}")
    print("="*60)
    
    # Start with base query
    query = db.query(Tweet).options(
        joinedload(Tweet.media),
        joinedload(Tweet.tags)
    )
    
    # Filter by tag if provided
    if tag_param:
        # Simulate the exact API code
        tag = tag_param.strip()
        
        print(f"1. After strip: '{tag}'")
        
        # Check if the tag exists in the database
        tag_count = db.query(Tag).filter(Tag.tag == tag).count()
        if tag_count == 0:
            print(f"2. Tag not found in database")
        else:
            print(f"2. Tag found {tag_count} times in database")
        
        if use_ontology:
            # Use ontology to get all related tags
            service = TagOntologyService(db)
            filter_tags = service.get_tags_for_filtering(tag)
            print(f"3. Ontology filter tags: {filter_tags}")
            
            # Check if the ontology returned slugified tags
            # If the only result is a slugified version of the original tag, 
            # just use the original tag instead
            if len(filter_tags) == 1:
                slugified = tag.lower().replace(' ', '-').replace('&', '&')
                if filter_tags[0] == slugified:
                    # Ontology just returned the slugified version, use original instead
                    print(f"   Ontology returned slugified tag, using original: '{tag}'")
                    filter_tags = [tag]
            
            if filter_tags:
                # Use distinct to avoid duplicates from multiple tag associations
                query = query.join(Tag).filter(Tag.tag.in_(filter_tags)).distinct()
                print(f"4. Using ontology filter with tags: {filter_tags}")
            else:
                # Tag not in ontology, use direct match
                print(f"4. Tag not in ontology, using direct match")
                query = query.join(Tag).filter(Tag.tag == tag).distinct()
        else:
            # Direct tag match without ontology
            print(f"3. Direct tag match (ontology disabled)")
            query = query.join(Tag).filter(Tag.tag == tag).distinct()
    
    # Execute query
    try:
        tweets = query.order_by(Tweet.created_at.desc()).limit(5).all()
        print(f"\n5. Query returned {len(tweets)} tweets")
        
        for tweet in tweets[:3]:
            print(f"   - @{tweet.author_username}: {tweet.text[:50]}...")
            
    except Exception as e:
        print(f"\n5. Error executing query: {e}")
        tweets = []
    
    db.close()
    return len(tweets)

# Test problematic tags
test_tags = [
    "Geopolitical AI Landscape",
    "blog update",
    "3D interface generation",
    "AI Ethics & Future"
]

for tag in test_tags:
    count = simulate_api_call(tag, use_ontology=True)
    if count == 0:
        print("\n   >>> PROBLEM: This tag returns 0 tweets!")
        # Try without ontology
        print("\n   Trying without ontology...")
        simulate_api_call(tag, use_ontology=False)