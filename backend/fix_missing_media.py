#!/usr/bin/env python3
"""
Fix missing media for tweets that have photo URLs but no media attachments
This will re-fetch specific tweets to get their media
"""

import os
import sys
import tweepy
from datetime import datetime, timezone
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import json
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import Tweet, TweetMedia

load_dotenv()

# Database setup
DATABASE_URL = "sqlite:///../data/tweets.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class MediaFixer:
    def __init__(self):
        """Initialize the fixer"""
        self.bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        if not self.bearer_token:
            raise ValueError("TWITTER_BEARER_TOKEN not found")
        
        self.client = tweepy.Client(bearer_token=self.bearer_token)
        self.db = SessionLocal()
        
    def find_tweets_with_photo_urls(self):
        """Find tweets that have photo URLs but no media attachments"""
        # Find tweets with photo URLs in their URL entities
        all_tweets = self.db.query(Tweet).filter(
            Tweet.urls.like('%photo/1%')
        ).all()
        
        # Filter to only those without media
        tweets_needing_media = []
        for tweet in all_tweets:
            existing_media = self.db.query(TweetMedia).filter(
                TweetMedia.tweet_id == tweet.id
            ).first()
            
            if not existing_media:
                tweets_needing_media.append(tweet)
        
        print(f"Found {len(tweets_needing_media)} tweets with photo URLs but no media attachments")
        return tweets_needing_media
    
    def fetch_and_save_media(self, tweet_id: str) -> bool:
        """Fetch media for a specific tweet and save it"""
        try:
            # Fetch the tweet with media expansions
            response = self.client.get_tweet(
                tweet_id,
                tweet_fields=['attachments', 'entities'],
                media_fields=['url', 'preview_image_url', 'alt_text', 'width', 'height', 'type', 'media_key'],
                expansions=['attachments.media_keys']
            )
            
            if not response.data:
                return False
            
            tweet_data = response.data
            
            # Check if tweet has media attachments
            if hasattr(tweet_data, 'attachments') and tweet_data.attachments:
                media_keys = tweet_data.attachments.get('media_keys', [])
                
                if media_keys and response.includes and 'media' in response.includes:
                    saved_count = 0
                    for media in response.includes['media']:
                        if media.media_key in media_keys:
                            # Check if media already exists
                            existing = self.db.query(TweetMedia).filter(
                                TweetMedia.tweet_id == tweet_id,
                                TweetMedia.media_key == media.media_key
                            ).first()
                            
                            if not existing:
                                # Save the media
                                tweet_media = TweetMedia(
                                    tweet_id=tweet_id,
                                    media_key=media.media_key,
                                    type=media.type,
                                    url=getattr(media, 'url', None),
                                    preview_image_url=getattr(media, 'preview_image_url', None),
                                    alt_text=getattr(media, 'alt_text', None),
                                    width=getattr(media, 'width', None),
                                    height=getattr(media, 'height', None)
                                )
                                self.db.add(tweet_media)
                                saved_count += 1
                                
                                print(f"  ✅ Added {media.type}: {media.url or media.preview_image_url}")
                    
                    if saved_count > 0:
                        self.db.commit()
                        return True
            
            return False
            
        except Exception as e:
            print(f"  ❌ Error fetching media for tweet {tweet_id}: {e}")
            return False
    
    def fix_all_missing_media(self):
        """Fix all tweets with missing media"""
        tweets_to_fix = self.find_tweets_with_photo_urls()
        
        if not tweets_to_fix:
            print("No tweets need media fixes!")
            return
        
        fixed_count = 0
        for i, tweet in enumerate(tweets_to_fix, 1):
            print(f"\n[{i}/{len(tweets_to_fix)}] Processing tweet {tweet.id}")
            print(f"  Author: @{tweet.author_username}")
            print(f"  Text: {tweet.text[:100]}...")
            
            if self.fetch_and_save_media(tweet.id):
                fixed_count += 1
            
            # Rate limiting - be conservative
            if i % 5 == 0:
                print(f"\nProcessed {i} tweets, fixed {fixed_count}. Pausing for rate limits...")
                time.sleep(3)
        
        print(f"\n✅ Complete! Fixed media for {fixed_count} out of {len(tweets_to_fix)} tweets")
        
    def close(self):
        """Close database connection"""
        self.db.close()

def main():
    print("=" * 60)
    print("🖼️  Missing Media Fixer")
    print("This will fetch media for tweets that have photo URLs")
    print("=" * 60)
    
    fixer = MediaFixer()
    
    try:
        fixer.fix_all_missing_media()
    finally:
        fixer.close()
    
    print("\n" + "=" * 60)
    print("Verification: Checking @emollick tweets again...")
    print("=" * 60)
    
    # Re-run the check to verify
    import check_tweet_media
    check_tweet_media.check_tweet_media()

if __name__ == "__main__":
    main()