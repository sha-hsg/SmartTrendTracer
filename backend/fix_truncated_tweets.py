#!/usr/bin/env python3
"""
Fix tweets that are truncated at 280 characters by fetching their full text
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

def fix_truncated_tweets():
    """Find and update tweets that are truncated at 280 character limit"""
    
    db = next(get_db())
    bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
    client = tweepy.Client(bearer_token=bearer_token)
    
    # Find tweets that are likely truncated (exactly 280 chars or 275-280 with no ending punctuation)
    likely_truncated = db.query(Tweet).filter(
        func.length(Tweet.text) >= 275,
        func.length(Tweet.text) <= 280
    ).all()
    
    # Also check tweets ending with "…" (ellipsis character)
    ellipsis_tweets = db.query(Tweet).filter(
        Tweet.text.like('%…')
    ).all()
    
    # Combine and deduplicate
    all_truncated = list({t.id: t for t in likely_truncated + ellipsis_tweets}.values())
    
    print(f"Found {len(all_truncated)} potentially truncated tweets:")
    for t in all_truncated[:5]:  # Show first 5
        print(f"  @{t.author_username}: {len(t.text)} chars - ...{t.text[-30:]}")
    
    if len(all_truncated) > 5:
        print(f"  ... and {len(all_truncated) - 5} more")
    
    updated_count = 0
    failed_count = 0
    batch_size = 100  # Twitter API allows up to 100 IDs per request
    
    # Process in batches
    for i in range(0, len(all_truncated), batch_size):
        batch = all_truncated[i:i+batch_size]
        tweet_ids = [t.id for t in batch]
        
        try:
            print(f"\n📥 Fetching batch {i//batch_size + 1} ({len(tweet_ids)} tweets)...")
            
            # Fetch tweets with note_tweet field for full text
            response = client.get_tweets(
                ids=tweet_ids,
                tweet_fields=['text', 'note_tweet', 'created_at', 'author_id'],
                expansions=['referenced_tweets.id', 'author_id']
            )
            
            if not response.data:
                print("  ❌ No data returned from API")
                continue
            
            # Build author map if we have includes
            author_map = {}
            if response.includes and 'users' in response.includes:
                for user in response.includes['users']:
                    author_map[user.id] = user.username
            
            # Process referenced tweets for RTs
            referenced_dict = {}
            if response.includes and 'tweets' in response.includes:
                for ref_tweet in response.includes['tweets']:
                    # Check if ref tweet has note_tweet
                    if hasattr(ref_tweet, 'note_tweet') and ref_tweet.note_tweet:
                        ref_full_text = ref_tweet.note_tweet.get('text', ref_tweet.text)
                    else:
                        ref_full_text = ref_tweet.text
                    referenced_dict[str(ref_tweet.id)] = ref_full_text
            
            for tweet_data in response.data:
                # Find the database tweet
                db_tweet = next((t for t in batch if t.id == str(tweet_data.id)), None)
                if not db_tweet:
                    continue
                
                # Get full text from note_tweet if available
                if hasattr(tweet_data, 'note_tweet') and tweet_data.note_tweet:
                    full_text = tweet_data.note_tweet.get('text', tweet_data.text)
                    print(f"  📝 Found note_tweet for @{db_tweet.author_username}")
                else:
                    full_text = tweet_data.text
                
                # For retweets, check if we can get the full original
                if full_text.startswith('RT @') and hasattr(tweet_data, 'referenced_tweets'):
                    for ref in tweet_data.referenced_tweets:
                        if ref.type == 'retweeted' and str(ref.id) in referenced_dict:
                            rt_prefix = full_text.split(':', 1)[0] + ': '
                            original_full = referenced_dict[str(ref.id)]
                            
                            # Only update if we got more text
                            if len(original_full) > len(full_text) - len(rt_prefix):
                                full_text = rt_prefix + original_full
                                print(f"  📝 Got full RT text for @{db_tweet.author_username}")
                            break
                
                # Update if we got more text
                old_len = len(db_tweet.text)
                new_len = len(full_text)
                
                if new_len > old_len:
                    db_tweet.text = full_text
                    updated_count += 1
                    print(f"  ✅ Updated @{db_tweet.author_username}: {old_len} → {new_len} chars (+{new_len - old_len})")
                    
                    # Show preview of new ending
                    if new_len > 280:
                        print(f"     New ending: ...{full_text[-50:]}")
                else:
                    # Check if it's actually different even if same length
                    if full_text != db_tweet.text:
                        db_tweet.text = full_text
                        updated_count += 1
                        print(f"  ✅ Updated @{db_tweet.author_username}: content changed (same length)")
                    
        except tweepy.errors.TooManyRequests:
            print("⚠️  Rate limited! Please wait 15 minutes and run again.")
            print(f"  Processed {updated_count} tweets before rate limit")
            break
        except Exception as e:
            print(f"❌ Error processing batch: {e}")
            failed_count += len(batch)
            continue
    
    # Commit all updates
    if updated_count > 0:
        db.commit()
        print(f"\n✅ Successfully updated {updated_count} tweets with full text!")
    else:
        print("\n📝 No tweets were updated.")
        print("   This might mean:")
        print("   - The tweets are intentionally short with '...'")
        print("   - They're not eligible for note_tweet (only tweets >280 chars)")
        print("   - The API doesn't have extended versions")
    
    if failed_count > 0:
        print(f"⚠️  Failed to process {failed_count} tweets")
    
    # Final check
    remaining = db.query(Tweet).filter(
        func.length(Tweet.text) == 280
    ).count()
    
    print(f"\n📊 Remaining tweets at exactly 280 chars: {remaining}")
    
    db.close()

if __name__ == "__main__":
    print("🔧 Fixing truncated tweets (280 char limit)...")
    print("=" * 60)
    fix_truncated_tweets()