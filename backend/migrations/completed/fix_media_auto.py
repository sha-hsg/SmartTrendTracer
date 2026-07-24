#!/usr/bin/env python3
"""
Fix missing media with automatic rate limit handling
Automatically pauses 15 minutes when rate limited and continues
"""

import os
import sys
import tweepy
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
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

class AutoMediaFixer:
    def __init__(self):
        """Initialize the fixer"""
        self.bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        if not self.bearer_token:
            raise ValueError("TWITTER_BEARER_TOKEN not found")
        
        self.client = tweepy.Client(bearer_token=self.bearer_token)
        self.db = SessionLocal()
        self.progress = self.load_progress()
        self.requests_made = 0
        self.max_requests_per_window = 8  # Conservative limit (actual is 10)
        
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
        
        return tweets_to_process
    
    def print_status(self):
        """Print current status"""
        all_with_urls = self.db.query(Tweet).filter(
            Tweet.urls.like('%photo/1%')
        ).count()
        
        tweets_remaining = self.find_tweets_needing_media()
        
        print("\n" + "=" * 60)
        print(f"📊 Current Status at {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 60)
        print(f"   Total tweets with photo URLs: {all_with_urls}")
        print(f"   ✅ Successfully processed: {len(self.progress['completed'])}")
        print(f"   ❌ Failed: {len(self.progress['failed'])}")
        print(f"   📋 Remaining to process: {len(tweets_remaining)}")
        print("=" * 60 + "\n")
        
        return len(tweets_remaining)
    
    def fetch_and_save_media(self, tweet_id: str) -> bool:
        """Fetch media for a specific tweet and save it"""
        try:
            # Increment request counter
            self.requests_made += 1
            
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
                    else:
                        print(f"  ℹ️ No new media to add")
            else:
                print(f"  ⚠️ No media attachments found in API response")
            
            return False
            
        except tweepy.errors.TooManyRequests as e:
            print(f"  ⚠️ Rate limited!")
            raise e
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False
    
    def wait_for_rate_limit(self):
        """Wait for rate limit window to reset"""
        wait_minutes = 15
        wait_seconds = wait_minutes * 60 + 30  # Add 30 seconds buffer
        
        print(f"\n⏰ Rate limit reached after {self.requests_made} requests")
        print(f"   Waiting {wait_minutes} minutes before continuing...")
        
        # Show countdown
        end_time = datetime.now() + timedelta(seconds=wait_seconds)
        
        while datetime.now() < end_time:
            remaining = (end_time - datetime.now()).total_seconds()
            mins, secs = divmod(int(remaining), 60)
            print(f"   Time remaining: {mins:02d}:{secs:02d}", end='\r')
            time.sleep(1)
        
        print(f"\n✅ Wait complete! Resuming at {datetime.now().strftime('%H:%M:%S')}\n")
        self.requests_made = 0  # Reset counter
    
    def run_continuous(self):
        """Run continuously until all media is collected"""
        print("=" * 60)
        print("🖼️  Automatic Media Fixer")
        print("This will run continuously until all media is collected")
        print("Press Ctrl+C to stop (progress will be saved)")
        print("=" * 60)
        
        total_fixed = 0
        
        try:
            while True:
                # Check current status
                remaining = self.print_status()
                
                if remaining == 0:
                    print("🎉 All tweets have been processed!")
                    # Clean up progress file
                    if os.path.exists(PROGRESS_FILE):
                        os.remove(PROGRESS_FILE)
                        print("Progress file cleaned up.")
                    break
                
                # Process batch
                print(f"🔄 Processing batch (up to {self.max_requests_per_window} tweets)...")
                batch_fixed = 0
                tweets_to_fix = self.find_tweets_needing_media()
                
                for i, tweet in enumerate(tweets_to_fix[:self.max_requests_per_window], 1):
                    if tweet.id in self.progress['completed']:
                        continue
                    
                    print(f"\n[{i}/{min(self.max_requests_per_window, len(tweets_to_fix))}] Tweet {tweet.id}")
                    print(f"  Author: @{tweet.author_username}")
                    print(f"  Text: {tweet.text[:80]}...")
                    
                    try:
                        if self.fetch_and_save_media(tweet.id):
                            batch_fixed += 1
                            total_fixed += 1
                            self.progress['completed'].add(tweet.id)
                        else:
                            self.progress['failed'].add(tweet.id)
                        
                        # Save progress after each tweet
                        self.save_progress()
                        
                        # Small delay between requests
                        time.sleep(1)
                        
                    except tweepy.errors.TooManyRequests:
                        # Wait for rate limit to reset
                        self.wait_for_rate_limit()
                        # Try this tweet again after waiting
                        try:
                            if self.fetch_and_save_media(tweet.id):
                                batch_fixed += 1
                                total_fixed += 1
                                self.progress['completed'].add(tweet.id)
                            else:
                                self.progress['failed'].add(tweet.id)
                            self.save_progress()
                        except:
                            self.progress['failed'].add(tweet.id)
                            self.save_progress()
                
                print(f"\n✅ Batch complete: Fixed {batch_fixed} tweets")
                
                # If we haven't hit rate limit yet but have more to process, wait anyway
                remaining = self.find_tweets_needing_media()
                if remaining and self.requests_made >= self.max_requests_per_window:
                    self.wait_for_rate_limit()
                elif not remaining:
                    break
                    
        except KeyboardInterrupt:
            print("\n\n⚠️ Interrupted by user")
            print(f"Progress saved. Fixed {total_fixed} tweets in this session.")
            print("Run the script again to continue from where you left off.")
        
        finally:
            self.close()
            print(f"\n📊 Final summary: Fixed {total_fixed} tweets in this session")
    
    def close(self):
        """Close database connection"""
        self.db.close()

def main():
    fixer = AutoMediaFixer()
    fixer.run_continuous()

if __name__ == "__main__":
    main()