#!/usr/bin/env python3
"""Test tag filtering to debug the issue"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import SessionLocal, Tweet, Tag, TweetMedia
from sqlalchemy.orm import joinedload

def test_tag_filter(tag_name):
    db = SessionLocal()
    
    print(f"\nTesting tag filter for: '{tag_name}'")
    
    # Check if tag exists
    tag_exists = db.query(Tag).filter(Tag.tag == tag_name).first()
    if not tag_exists:
        print(f"  ❌ Tag not found in database")
        return
    
    print(f"  ✓ Tag exists in database")
    
    # Count tweets with this tag
    tag_count = db.query(Tag).filter(Tag.tag == tag_name).count()
    print(f"  Found {tag_count} tag occurrences")
    
    # Try the exact query from the API
    query = db.query(Tweet).options(
        joinedload(Tweet.media),
        joinedload(Tweet.tags)
    )
    
    # This is what the API does
    query = query.join(Tag).filter(Tag.tag == tag_name).distinct()
    
    # Execute and count
    tweets = query.limit(5).all()
    total_count = query.count()
    
    print(f"  Query returned {total_count} tweets")
    
    if tweets:
        for tweet in tweets[:3]:
            print(f"    - @{tweet.author_username}: {tweet.text[:50]}...")
    
    # Try alternative query approach
    print("\n  Alternative query (using subquery):")
    tweet_ids = db.query(Tag.tweet_id).filter(Tag.tag == tag_name).subquery()
    alt_tweets = db.query(Tweet).filter(Tweet.id.in_(tweet_ids)).limit(5).all()
    
    if alt_tweets:
        for tweet in alt_tweets[:3]:
            print(f"    - @{tweet.author_username}: {tweet.text[:50]}...")
    
    db.close()

# Test problematic tags
test_tags = [
    '3D interface generation',
    '16GB devices',
    'Communication Strategy',
    'AI Ethics & Future',
    'AI Advancements',
    'AI Evaluation Metrics'
]

for tag in test_tags:
    test_tag_filter(tag)