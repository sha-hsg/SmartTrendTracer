#!/usr/bin/env python3
"""
Collect missing media for tweets that should have images/videos
"""
import sys
import os
import tweepy
from datetime import datetime
from dotenv import load_dotenv

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db, Tweet, TweetMedia
from app.config import ACCOUNTS_TO_FOLLOW

load_dotenv()

def collect_missing_media():
    """Find tweets with t.co links but no media and fetch their media"""
    
    db = next(get_db())
    bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
    client = tweepy.Client(bearer_token=bearer_token)
    
    # Find recent tweets with t.co links but no media
    # These likely have media that wasn't collected
    tweets_with_links = db.query(Tweet).filter(
        Tweet.text.like('%t.co%')
    ).order_by(Tweet.created_at.desc()).limit(100).all()
    
    missing_media_tweets = []
    for tweet in tweets_with_links:
        # Check if this tweet has media
        media_count = db.query(TweetMedia).filter(TweetMedia.tweet_id == tweet.id).count()
        if media_count == 0:
            missing_media_tweets.append(tweet)
    
    print(f"Found {len(missing_media_tweets)} tweets with t.co links but no media")
    
    if not missing_media_tweets:
        print("All tweets have media!")
        return
    
    # Process in batches of 100
    batch_size = 100
    total_media_added = 0
    
    for i in range(0, len(missing_media_tweets), batch_size):
        batch = missing_media_tweets[i:i+batch_size]
        tweet_ids = [t.id for t in batch]
        
        try:
            print(f"\n📥 Fetching media for batch {i//batch_size + 1} ({len(tweet_ids)} tweets)...")
            
            # Fetch tweets with media expansions
            response = client.get_tweets(
                ids=tweet_ids,
                tweet_fields=['attachments', 'entities', 'referenced_tweets'],
                media_fields=['url', 'preview_image_url', 'alt_text', 'width', 'height', 'type'],
                expansions=['attachments.media_keys', 'referenced_tweets.id', 'referenced_tweets.id.attachments.media_keys']
            )
            
            if not response.data:
                continue
            
            # Build media dictionary
            media_dict = {}
            if response.includes and 'media' in response.includes:
                for media in response.includes['media']:
                    media_dict[media.media_key] = media
            
            # Process referenced tweets for RTs
            referenced_media_keys = {}
            if response.includes and 'tweets' in response.includes:
                for ref_tweet in response.includes['tweets']:
                    if hasattr(ref_tweet, 'attachments') and ref_tweet.attachments:
                        referenced_media_keys[str(ref_tweet.id)] = ref_tweet.attachments.get('media_keys', [])
            
            # Process each tweet
            for tweet_data in response.data:
                db_tweet = next((t for t in batch if t.id == str(tweet_data.id)), None)
                if not db_tweet:
                    continue
                
                media_keys_to_save = []
                
                # Get media from the tweet itself
                if hasattr(tweet_data, 'attachments') and tweet_data.attachments:
                    media_keys_to_save.extend(tweet_data.attachments.get('media_keys', []))
                
                # For retweets, get media from original tweet
                if hasattr(tweet_data, 'referenced_tweets') and tweet_data.referenced_tweets:
                    for ref in tweet_data.referenced_tweets:
                        if ref.type == 'retweeted' and str(ref.id) in referenced_media_keys:
                            media_keys_to_save.extend(referenced_media_keys[str(ref.id)])
                            break
                
                # Save media
                media_added = 0
                for media_key in media_keys_to_save:
                    if media_key in media_dict:
                        # Check if already exists
                        existing = db.query(TweetMedia).filter(
                            TweetMedia.tweet_id == db_tweet.id,
                            TweetMedia.media_key == media_key
                        ).first()
                        
                        if not existing:
                            media = media_dict[media_key]
                            tweet_media = TweetMedia(
                                tweet_id=db_tweet.id,
                                media_key=media_key,
                                type=media.type,
                                url=getattr(media, 'url', None),
                                preview_image_url=getattr(media, 'preview_image_url', None),
                                alt_text=getattr(media, 'alt_text', None),
                                width=getattr(media, 'width', None),
                                height=getattr(media, 'height', None)
                            )
                            db.add(tweet_media)
                            media_added += 1
                            total_media_added += 1
                
                if media_added > 0:
                    print(f"  ✅ Added {media_added} media items for @{db_tweet.author_username}")
                    
        except tweepy.errors.TooManyRequests:
            print("⚠️  Rate limited! Saving progress...")
            db.commit()
            print(f"Added {total_media_added} media items before rate limit")
            print("Please wait 15 minutes and run again.")
            return
        except Exception as e:
            print(f"❌ Error processing batch: {e}")
            continue
    
    # Commit all changes
    db.commit()
    
    print(f"\n✅ Successfully added {total_media_added} media items!")
    
    # Show statistics
    total_with_media = db.query(TweetMedia.tweet_id).distinct().count()
    print(f"📊 Total tweets with media: {total_with_media}")
    
    db.close()

if __name__ == "__main__":
    print("🖼️  Collecting missing media for tweets...")
    print("=" * 60)
    collect_missing_media()