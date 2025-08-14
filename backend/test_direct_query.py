#!/usr/bin/env python3
"""
Test the query directly
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy.orm import joinedload

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import get_db, Tweet, Tag

load_dotenv()

def test_direct_query():
    """Test the query that the API should be using"""
    
    db = next(get_db())
    
    test_tags = [
        "Research & Development",
        "80GB GPU",
        "GPT"
    ]
    
    print("=" * 60)
    print("TESTING DIRECT QUERY")
    print("=" * 60)
    
    for tag_name in test_tags:
        print(f"\n📌 Testing tag: '{tag_name}'")
        print("-" * 40)
        
        # Method 1: Simple join (what we're trying)
        query1 = db.query(Tweet).options(
            joinedload(Tweet.media),
            joinedload(Tweet.tags)
        ).join(Tag).filter(Tag.tag == tag_name).distinct()
        
        tweets1 = query1.limit(5).all()
        print(f"Method 1 (join with options): Found {len(tweets1)} tweets")
        
        if tweets1:
            first = tweets1[0]
            tags = [t.tag for t in first.tags]
            print(f"  First tweet tags: {tags}")
            print(f"  Has target tag: {tag_name in tags}")
        
        # Method 2: Without joinedload
        query2 = db.query(Tweet).join(Tag).filter(Tag.tag == tag_name).distinct()
        tweets2 = query2.limit(5).all()
        print(f"Method 2 (simple join): Found {len(tweets2)} tweets")
        
        # Method 3: Subquery approach
        from sqlalchemy import exists
        query3 = db.query(Tweet).filter(
            exists().where(
                (Tag.tweet_id == Tweet.id) & 
                (Tag.tag == tag_name)
            )
        )
        tweets3 = query3.limit(5).all()
        print(f"Method 3 (exists subquery): Found {len(tweets3)} tweets")
    
    db.close()

if __name__ == "__main__":
    test_direct_query()