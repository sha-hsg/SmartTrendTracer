#!/usr/bin/env python3
"""
Check if a specific tweet has media attachments
"""

import sys
import os
from datetime import datetime, timezone
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import get_db, Tweet, TweetMedia
from sqlalchemy import or_

def check_tweet_media():
    """Check tweets from emollick for media"""
    db = next(get_db())
    
    # Find the specific tweet or recent tweets from emollick
    tweets = db.query(Tweet).filter(
        Tweet.author_username == 'emollick',
        or_(
            Tweet.text.like('%OpenAI agrees%'),
            Tweet.text.like('%t.co%')
        )
    ).order_by(Tweet.created_at.desc()).limit(10).all()
    
    print("=" * 60)
    print("📸 Checking @emollick tweets for media")
    print("=" * 60)
    
    for tweet in tweets:
        print(f"\nTweet ID: {tweet.id}")
        print(f"Date: {tweet.created_at}")
        print(f"Text: {tweet.text[:100]}...")
        
        # Check for media
        media = db.query(TweetMedia).filter(TweetMedia.tweet_id == tweet.id).all()
        if media:
            print(f"✅ Has {len(media)} media attachments:")
            for m in media:
                print(f"   - Type: {m.type}")
                print(f"   - URL: {m.url}")
                print(f"   - Preview: {m.preview_image_url}")
        else:
            print("❌ No media attachments found")
        
        # Check URLs in entities
        if tweet.urls:
            try:
                urls = json.loads(tweet.urls)
                if urls:
                    print(f"🔗 Has {len(urls)} URLs:")
                    for url in urls:
                        print(f"   - {url.get('expanded_url', url.get('url', 'Unknown'))}")
            except:
                pass
        
        # Check if it's a retweet
        if tweet.referenced_tweets:
            try:
                refs = json.loads(tweet.referenced_tweets)
                print(f"🔄 Referenced tweets: {refs}")
            except:
                pass
        
        print("-" * 40)
    
    # Check overall media statistics
    total_media = db.query(TweetMedia).count()
    tweets_with_media = db.query(Tweet.id).join(TweetMedia).distinct().count()
    total_tweets = db.query(Tweet).count()
    
    print(f"\n📊 Media Statistics:")
    print(f"   Total tweets: {total_tweets}")
    print(f"   Tweets with media: {tweets_with_media}")
    print(f"   Total media items: {total_media}")
    print(f"   Media percentage: {tweets_with_media/total_tweets*100:.1f}%")
    
    db.close()

if __name__ == "__main__":
    check_tweet_media()