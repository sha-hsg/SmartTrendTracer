#!/usr/bin/env python3
"""Test tweet query logic directly"""

from app.models import get_db
from app.models.tweet import Tweet, Tag
from sqlalchemy import func, distinct, desc

def test_tweet_query():
    """Test the query logic we're using in faceted search"""
    db = next(get_db())
    
    try:
        # Test basic query
        print("Testing basic tweet query...")
        tweets = db.query(Tweet).limit(5).all()
        print(f"✅ Found {len(tweets)} tweets")
        
        # Test retweet detection
        print("\nTesting retweet detection...")
        for tweet in tweets[:3]:
            is_retweet = tweet.text.startswith('RT @') if tweet.text else False
            print(f"  Tweet {tweet.id[:10]}... - Is Retweet: {is_retweet}")
            print(f"    Text preview: {tweet.text[:50]}...")
        
        # Test author facets query
        print("\nTesting author facets...")
        author_facets = db.query(
            Tweet.author_username,
            func.count(Tweet.id).label('count')
        ).group_by(Tweet.author_username)\
         .order_by(desc('count'))\
         .limit(5)\
         .all()
        
        for username, count in author_facets:
            print(f"  @{username}: {count} tweets")
        
        # Test tag facets
        print("\nTesting tag facets...")
        tag_facets = db.query(
            Tag.tag,
            func.count(Tag.id).label('count')
        ).group_by(Tag.tag)\
         .order_by(desc('count'))\
         .limit(5)\
         .all()
        
        for tag, count in tag_facets:
            print(f"  {tag}: {count} uses")
            
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_tweet_query()