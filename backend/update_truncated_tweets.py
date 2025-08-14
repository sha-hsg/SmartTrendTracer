#!/usr/bin/env python3
"""
Update truncated tweets to get their full text using note_tweet field
"""
import sys
import os
import tweepy
from datetime import datetime
from dotenv import load_dotenv

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db, Tweet
from sqlalchemy import func

load_dotenv()

def update_truncated_tweets():
    """Find and update tweets that appear to be truncated"""
    
    db = next(get_db())
    bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
    client = tweepy.Client(bearer_token=bearer_token)
    
    # Find potentially truncated tweets (ending with ...)
    truncated = db.query(Tweet).filter(
        Tweet.text.like('%...')
    ).all()
    
    print(f"Found {len(truncated)} potentially truncated tweets")
    
    updated_count = 0
    batch_size = 100  # Twitter API allows up to 100 IDs per request
    
    # Process in batches
    for i in range(0, len(truncated), batch_size):
        batch = truncated[i:i+batch_size]
        tweet_ids = [t.id for t in batch]
        
        try:
            print(f"\nFetching batch {i//batch_size + 1} ({len(tweet_ids)} tweets)...")
            
            # Fetch tweets with note_tweet field for full text
            response = client.get_tweets(
                ids=tweet_ids,
                tweet_fields=['text', 'note_tweet', 'created_at'],
                expansions=['referenced_tweets.id']
            )
            
            if response.data:
                # Also get referenced tweets for RTs
                referenced_dict = {}
                if response.includes and 'tweets' in response.includes:
                    for ref_tweet in response.includes['tweets']:
                        referenced_dict[str(ref_tweet.id)] = ref_tweet
                
                for tweet_data in response.data:
                    # Find the database tweet
                    db_tweet = next((t for t in batch if t.id == str(tweet_data.id)), None)
                    if not db_tweet:
                        continue
                    
                    # Get full text
                    if hasattr(tweet_data, 'note_tweet') and tweet_data.note_tweet:
                        full_text = tweet_data.note_tweet.get('text', tweet_data.text)
                    else:
                        full_text = tweet_data.text
                    
                    # For retweets, get original tweet's full text
                    if full_text.startswith('RT @') and hasattr(tweet_data, 'referenced_tweets'):
                        for ref in tweet_data.referenced_tweets:
                            if ref.type == 'retweeted' and str(ref.id) in referenced_dict:
                                original = referenced_dict[str(ref.id)]
                                rt_prefix = full_text.split(':', 1)[0] + ': '
                                
                                # Get original's full text
                                if hasattr(original, 'note_tweet') and original.note_tweet:
                                    original_text = original.note_tweet.get('text', original.text)
                                else:
                                    original_text = original.text
                                    
                                full_text = rt_prefix + original_text
                                break
                    
                    # Update if we got more text
                    if len(full_text) > len(db_tweet.text):
                        old_len = len(db_tweet.text)
                        db_tweet.text = full_text
                        updated_count += 1
                        print(f"  ✅ Updated @{db_tweet.author_username}: {old_len} → {len(full_text)} chars")
                    
        except tweepy.errors.TooManyRequests:
            print("⚠️  Rate limited! Please wait 15 minutes and run again.")
            break
        except Exception as e:
            print(f"❌ Error processing batch: {e}")
            continue
    
    # Commit all updates
    if updated_count > 0:
        db.commit()
        print(f"\n✅ Successfully updated {updated_count} tweets with full text!")
    else:
        print("\n📝 No tweets needed updating.")
    
    db.close()

if __name__ == "__main__":
    print("🔄 Updating truncated tweets to full text...")
    print("=" * 60)
    update_truncated_tweets()