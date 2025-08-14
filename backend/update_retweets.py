#!/usr/bin/env python3
"""
Update existing truncated retweets with full text
This script will check for truncated retweets in the database and update them with full text
"""

import os
import sys
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tweepy
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import Tweet
from app.config import ACCOUNTS_TO_FOLLOW

load_dotenv()

# Database setup
DATABASE_URL = "sqlite:///tweets.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class RetweetUpdater:
    def __init__(self):
        """Initialize the updater"""
        self.bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        if not self.bearer_token:
            raise ValueError("TWITTER_BEARER_TOKEN not found")
        
        self.client = tweepy.Client(bearer_token=self.bearer_token)
        self.db = SessionLocal()
        
    def find_truncated_retweets(self):
        """Find all retweets that appear to be truncated"""
        # Find tweets that start with RT and contain ellipsis
        truncated = self.db.query(Tweet).filter(
            Tweet.text.like('RT @%'),
            Tweet.text.like('%…%')
        ).all()
        
        print(f"Found {len(truncated)} potentially truncated retweets")
        return truncated
    
    def update_tweet_text(self, tweet_id: str):
        """Fetch and update the full text for a tweet"""
        try:
            # Fetch the tweet with expansions
            response = self.client.get_tweet(
                tweet_id,
                tweet_fields=['referenced_tweets', 'created_at', 'public_metrics'],
                expansions=['referenced_tweets.id']
            )
            
            if not response.data:
                return False
            
            tweet_data = response.data
            
            # Check if it's a retweet and we have the referenced tweet
            if hasattr(tweet_data, 'referenced_tweets') and tweet_data.referenced_tweets:
                for ref in tweet_data.referenced_tweets:
                    if ref.type == 'retweeted':
                        # Get the original tweet
                        if response.includes and 'tweets' in response.includes:
                            for included_tweet in response.includes['tweets']:
                                if str(included_tweet.id) == str(ref.id):
                                    # Update the database
                                    db_tweet = self.db.query(Tweet).filter(Tweet.id == tweet_id).first()
                                    if db_tweet:
                                        # Extract RT prefix and combine with full text
                                        rt_prefix = db_tweet.text.split(':', 1)[0] + ': '
                                        full_text = rt_prefix + included_tweet.text
                                        
                                        print(f"Updating tweet {tweet_id}")
                                        print(f"  Old: {db_tweet.text[:100]}...")
                                        print(f"  New: {full_text[:100]}...")
                                        
                                        db_tweet.text = full_text
                                        self.db.commit()
                                        return True
            
            return False
            
        except Exception as e:
            print(f"Error updating tweet {tweet_id}: {e}")
            return False
    
    def update_all_truncated(self):
        """Update all truncated retweets"""
        truncated = self.find_truncated_retweets()
        
        if not truncated:
            print("No truncated retweets found!")
            return
        
        updated_count = 0
        for i, tweet in enumerate(truncated, 1):
            print(f"\n[{i}/{len(truncated)}] Processing tweet {tweet.id}")
            
            if self.update_tweet_text(tweet.id):
                updated_count += 1
                
            # Rate limiting - be conservative
            if i % 10 == 0:
                print(f"Processed {i} tweets, updated {updated_count}. Pausing for rate limits...")
                import time
                time.sleep(5)
        
        print(f"\n✅ Complete! Updated {updated_count} out of {len(truncated)} truncated retweets")
        
    def close(self):
        """Close database connection"""
        self.db.close()

def main():
    print("=" * 60)
    print("Retweet Text Updater")
    print("This will update truncated retweets with their full text")
    print("=" * 60)
    
    updater = RetweetUpdater()
    
    try:
        updater.update_all_truncated()
    finally:
        updater.close()

if __name__ == "__main__":
    main()