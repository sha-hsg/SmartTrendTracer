#!/usr/bin/env python3
"""
Fix missing media with rate limit handling and resume capability
Saves progress and can resume from where it left off
"""

import os
import sys
import tweepy
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import json
import time
import pickle

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import Tweet, TweetMedia

load_dotenv()

# Database setup
DATABASE_URL = "sqlite:///../data/tweets.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

PROGRESS_FILE = "media_fix_progress.pkl"

class MediaFixerWithResume:
    def __init__(self):
        """Initialize the fixer"""
        self.bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        if not self.bearer_token:
            raise ValueError("TWITTER_BEARER_TOKEN not found")
        
        self.client = tweepy.Client(bearer_token=self.bearer_token)
        self.db = SessionLocal()
        self.progress = self.load_progress()
        
    def load_progress(self):
        """Load progress from file if it exists"""
        if os.path.exists(PROGRESS_FILE):
            try:
                with open(PROGRESS_FILE, 'rb') as f:
                    progress = pickle.load(f)
                    print(f"📂 Resuming from previous run. Already processed: {len(progress['completed'])} tweets")
                    return progress
            except:
                pass
        
        return {
            'completed': set(),
            'failed': set(),
            'last_run': datetime.now(timezone.utc)
        }
    
    def save_progress(self):
        """Save current progress"""
        self.progress['last_run'] = datetime.now(timezone.utc)
        with open(PROGRESS_FILE, 'wb') as f:
            pickle.dump(self.progress, f)
    
    def find_tweets_needing_media(self):
        """Find tweets that need media but haven't been processed yet"""
        # Find all tweets with photo URLs
        all_tweets = self.db.query(Tweet).filter(
            Tweet.urls.like('%photo/1%')
        ).all()
        
        tweets_to_process = []
        for tweet in all_tweets:
            # Skip if already processed
            if tweet.id in self.progress['completed'] or tweet.id in self.progress['failed']:
                continue
                
            # Check if it already has media
            existing_media = self.db.query(TweetMedia).filter(
                TweetMedia.tweet_id == tweet.id
            ).first()
            
            if not existing_media:
                tweets_to_process.append(tweet)
        
        print(f"📊 Status:")
        print(f"   Total tweets with photo URLs: {len(all_tweets)}")
        print(f"   Already processed: {len(self.progress['completed'])}")
        print(f"   Failed previously: {len(self.progress['failed'])}")
        print(f"   To process now: {len(tweets_to_process)}")
        
        return tweets_to_process
    
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
            
        except tweepy.errors.TooManyRequests as e:
            print(f"  ⚠️ Rate limited! Will pause and retry later.")
            raise e
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False
    
    def fix_media_batch(self, batch_size=5):
        """Fix media in batches with rate limit handling"""
        tweets_to_fix = self.find_tweets_needing_media()
        
        if not tweets_to_fix:
            print("\n✅ All tweets have been processed!")
            return 0
        
        fixed_count = 0
        rate_limit_hit = False
        
        for i, tweet in enumerate(tweets_to_fix[:batch_size], 1):
            if tweet.id in self.progress['completed']:
                continue
                
            print(f"\n[{i}/{min(batch_size, len(tweets_to_fix))}] Processing tweet {tweet.id}")
            print(f"  Author: @{tweet.author_username}")
            print(f"  Text: {tweet.text[:100]}...")
            
            try:
                if self.fetch_and_save_media(tweet.id):
                    fixed_count += 1
                    self.progress['completed'].add(tweet.id)
                else:
                    self.progress['failed'].add(tweet.id)
                
                # Save progress after each tweet
                self.save_progress()
                
                # Small delay between requests
                time.sleep(1)
                
            except tweepy.errors.TooManyRequests:
                rate_limit_hit = True
                print("\n⏸️ Rate limit reached. Progress saved.")
                break
        
        return fixed_count, rate_limit_hit
    
    def close(self):
        """Close database connection"""
        self.db.close()

def main():
    print("=" * 60)
    print("🖼️  Media Fixer with Resume Capability")
    print("=" * 60)
    
    fixer = MediaFixerWithResume()
    
    try:
        # Process in small batches
        fixed_count, rate_limited = fixer.fix_media_batch(batch_size=5)
        
        print("\n" + "=" * 60)
        print(f"✅ Fixed {fixed_count} tweets in this run")
        
        if rate_limited:
            # Calculate wait time (15 minutes from now)
            wait_until = datetime.now() + timedelta(minutes=15)
            print(f"⏰ Rate limited. Try again after: {wait_until.strftime('%H:%M:%S')}")
            print("\nTo continue, run this script again in 15 minutes.")
            print("Progress has been saved and will resume automatically.")
        else:
            remaining = len(fixer.find_tweets_needing_media())
            if remaining > 0:
                print(f"📋 {remaining} tweets still need processing.")
                print("Run this script again to continue.")
            else:
                print("🎉 All tweets have been processed!")
                # Clean up progress file
                if os.path.exists(PROGRESS_FILE):
                    os.remove(PROGRESS_FILE)
                    print("Progress file cleaned up.")
        
    finally:
        fixer.close()

if __name__ == "__main__":
    main()