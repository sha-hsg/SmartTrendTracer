"""
Twitter Data Collector using Tweepy
Collects tweets from specified accounts and stores them in the database
"""
import tweepy
import os
import html
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from dotenv import load_dotenv
import json

from app.config import ACCOUNTS_TO_FOLLOW
from app.rate_limiter import get_rate_limiter

load_dotenv()

class TwitterCollector:
    def __init__(self, db_session: Session = None):
        """Initialize Twitter collector with API credentials"""
        self.bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        
        if not self.bearer_token:
            raise ValueError("TWITTER_BEARER_TOKEN not found in environment variables")
        
        # Initialize Tweepy client
        self.client = tweepy.Client(bearer_token=self.bearer_token)
        
        # Keep track of media added in current session to avoid duplicates
        self.session_media_keys = set()
        
        # Database session
        
        # Rate limiter
        self.rate_limiter = get_rate_limiter()
    
    def collect_tweets(self, max_results: int = 100) -> int:
        """
        Collect recent tweets from followed accounts
        Returns the number of new tweets collected
        """
        new_tweets_count = 0
        
        # Clear session media tracking for new collection
        self.session_media_keys.clear()
        
        for account in ACCOUNTS_TO_FOLLOW:
            try:
                print(f"Collecting tweets from @{account['username']}...")
                
                # Wait if rate limited
                self.rate_limiter.wait_if_needed()
                
                # Get user's tweets with referenced tweets expanded for full text
                self.rate_limiter.record_request()
                tweets = self.client.get_users_tweets(
                    id=account['id'],
                    max_results=min(max_results, 100),
                    tweet_fields=['created_at', 'public_metrics', 'referenced_tweets', 'entities', 'note_tweet', 'attachments'],
                    media_fields=['url', 'preview_image_url', 'alt_text', 'width', 'height', 'type'],
                    expansions=['attachments.media_keys', 'referenced_tweets.id', 'referenced_tweets.id.attachments.media_keys']
                )
                
                if not tweets.data:
                    continue
                
                # Process media if available
                media_dict = {}
                if tweets.includes and 'media' in tweets.includes:
                    for media in tweets.includes['media']:
                        media_dict[media.media_key] = media
                
                # Process referenced tweets (for getting full text of retweets)
                referenced_tweets_dict = {}
                if tweets.includes and 'tweets' in tweets.includes:
                    for ref_tweet in tweets.includes['tweets']:
                        referenced_tweets_dict[str(ref_tweet.id)] = ref_tweet
                
                # Save tweets to database
                for tweet in tweets.data:
                    if self._save_tweet(tweet, account, media_dict, referenced_tweets_dict):
                        new_tweets_count += 1
                
            except tweepy.errors.TooManyRequests as e:
                print(f"  ⚠️ Rate limited on @{account['username']}: {e}")
                wait_time = self.rate_limiter.handle_429_error()
                print(f"  ⏳ Will retry after {wait_time} seconds")
                continue
            except Exception as e:
                print(f"Error collecting tweets from {account['username']}: {e}")
        
        self.db.commit()
        return new_tweets_count
    
    def _save_tweet(self, tweet_data: Any, account: Dict, media_dict: Dict, referenced_tweets_dict: Dict = None) -> bool:
        """
        Save a single tweet to the database
        Returns True if tweet was new, False if already existed
        """
        # Check if tweet already exists
        existing = self.db.query(Tweet).filter(Tweet.id == str(tweet_data.id)).first()
        if existing:
            return False
        
        # Get the full text - check for long tweets first (note_tweet)
        if hasattr(tweet_data, 'note_tweet') and tweet_data.note_tweet:
            # This is a long tweet, get the full text from note_tweet
            tweet_text = html.unescape(tweet_data.note_tweet.get('text', tweet_data.text))
        else:
            tweet_text = html.unescape(tweet_data.text)
        
        # Track if this is a retweet or quote tweet and get referenced tweet's media
        referenced_tweet_media_keys = []
        quoted_tweet_id = None
        
        # Check if this is a retweet or quoted tweet and we have the referenced tweet
        if referenced_tweets_dict and hasattr(tweet_data, 'referenced_tweets') and tweet_data.referenced_tweets:
            for ref in tweet_data.referenced_tweets:
                if ref.type == 'retweeted' and str(ref.id) in referenced_tweets_dict:
                    original_tweet = referenced_tweets_dict[str(ref.id)]
                    # Use the original tweet's full text, but keep RT prefix
                    if tweet_text.startswith('RT @'):
                        # Extract the RT @username: part and combine with full text
                        rt_prefix = tweet_text.split(':', 1)[0] + ': '
                        tweet_text = rt_prefix + html.unescape(original_tweet.text)
                    
                    # Get media keys from original tweet
                    if hasattr(original_tweet, 'attachments') and original_tweet.attachments:
                        referenced_tweet_media_keys = original_tweet.attachments.get('media_keys', [])
                    break
                elif ref.type == 'quoted' and str(ref.id) in referenced_tweets_dict:
                    # For quoted tweets, we don't modify the text but we note the quoted tweet
                    quoted_tweet = referenced_tweets_dict[str(ref.id)]
                    quoted_tweet_id = str(ref.id)
                    
                    # Get media keys from quoted tweet (these are often what people are referring to)
                    if hasattr(quoted_tweet, 'attachments') and quoted_tweet.attachments:
                        referenced_tweet_media_keys = quoted_tweet.attachments.get('media_keys', [])
        
        # Ensure created_at is timezone-aware (Twitter API returns UTC)
        created_at = tweet_data.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        
        # Create tweet object
        tweet = Tweet(
            id=str(tweet_data.id),
            text=tweet_text,
            author_id=account['id'],
            author_username=account['username'],
            created_at=created_at,
            retweet_count=tweet_data.public_metrics.get('retweet_count', 0),
            like_count=tweet_data.public_metrics.get('like_count', 0),
            reply_count=tweet_data.public_metrics.get('reply_count', 0),
            quote_count=tweet_data.public_metrics.get('quote_count', 0),
            processed=False,
            media_count=0  # Will be updated later
        )
        
        # Add entities as JSON
        if hasattr(tweet_data, 'entities'):
            if tweet_data.entities:
                tweet.hashtags = json.dumps(tweet_data.entities.get('hashtags', []))
                tweet.mentions = json.dumps(tweet_data.entities.get('mentions', []))
                tweet.urls = json.dumps(tweet_data.entities.get('urls', []))
        
        # Add referenced tweets (including quoted tweets)
        if hasattr(tweet_data, 'referenced_tweets'):
            if tweet_data.referenced_tweets:
                tweet.referenced_tweets = json.dumps([
                    {'type': ref.type, 'id': str(ref.id)} 
                    for ref in tweet_data.referenced_tweets
                ])
        
        self.db.add(tweet)
        
        # Add media if present (from the tweet itself OR from original tweet if RT)
        media_keys_to_save = []
        
        # Get media keys from the tweet itself
        if hasattr(tweet_data, 'attachments') and tweet_data.attachments:
            media_keys_to_save.extend(tweet_data.attachments.get('media_keys', []))
        
        # Add media keys from referenced tweet (retweet or quote tweet)
        if referenced_tweet_media_keys:
            media_keys_to_save.extend(referenced_tweet_media_keys)
        
        # Update media count
        tweet.media_count = len(media_keys_to_save)
        
        # Save all media
        media_saved = 0
        for media_key in media_keys_to_save:
            if media_key in media_dict:
                # Create a composite key for tracking this specific tweet-media combination
                composite_key = f"{tweet_data.id}_{media_key}"
                
                # Check if we've already added this media in current session
                if composite_key in self.session_media_keys:
                    continue
                
                # Check if media already exists for this tweet in database
                existing_media = self.db.query(TweetMedia).filter(
                    TweetMedia.tweet_id == str(tweet_data.id),
                    TweetMedia.media_key == media_key
                ).first()
                
                if not existing_media:
                    media = media_dict[media_key]
                    tweet_media = TweetMedia(
                        tweet_id=str(tweet_data.id),
                        media_key=media_key,
                        type=media.type,
                        url=getattr(media, 'url', None),
                        preview_image_url=getattr(media, 'preview_image_url', None),
                        alt_text=getattr(media, 'alt_text', None),
                        width=getattr(media, 'width', None),
                        height=getattr(media, 'height', None)
                    )
                    self.db.add(tweet_media)
                    self.session_media_keys.add(composite_key)
                    media_saved += 1
        
        # Log if media was expected but not saved
        if media_keys_to_save and media_saved == 0:
            print(f"  ⚠️ Tweet {tweet_data.id} has {len(media_keys_to_save)} media keys but none were in media_dict")
        
        return True
    
    def collect_since_timestamp(self, since_time: datetime) -> int:
        """
        Collect all tweets since a specific timestamp
        """
        # Format datetime for Twitter API (RFC3339 without microseconds)
        start_time = since_time.replace(microsecond=0).isoformat().replace('+00:00', 'Z')
        end_time = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
        new_tweets_count = 0
        
        # Clear session media tracking for new collection
        self.session_media_keys.clear()
        
        print(f"Collecting tweets from {start_time} to {end_time}...")
        
        for account in ACCOUNTS_TO_FOLLOW:
            try:
                print(f"  Checking @{account['username']}...")
                
                # Wait if rate limited
                self.rate_limiter.wait_if_needed()
                
                # Get tweets since the last run with referenced tweets expanded
                self.rate_limiter.record_request()
                tweets = self.client.get_users_tweets(
                    id=account['id'],
                    start_time=start_time,
                    end_time=end_time,
                    max_results=100,
                    tweet_fields=['created_at', 'public_metrics', 'referenced_tweets', 'entities', 'note_tweet', 'attachments'],
                    media_fields=['url', 'preview_image_url', 'alt_text', 'width', 'height', 'type'],
                    expansions=['attachments.media_keys', 'referenced_tweets.id', 'referenced_tweets.id.attachments.media_keys']
                )
                
                if not tweets.data:
                    print(f"    No new tweets")
                    continue
                
                # Process media
                media_dict = {}
                if tweets.includes and 'media' in tweets.includes:
                    for media in tweets.includes['media']:
                        media_dict[media.media_key] = media
                
                # Process referenced tweets (for getting full text of retweets)
                referenced_tweets_dict = {}
                if tweets.includes and 'tweets' in tweets.includes:
                    for ref_tweet in tweets.includes['tweets']:
                        referenced_tweets_dict[str(ref_tweet.id)] = ref_tweet
                
                # Save tweets
                account_new = 0
                for tweet in tweets.data:
                    if self._save_tweet(tweet, account, media_dict, referenced_tweets_dict):
                        account_new += 1
                        new_tweets_count += 1
                
                if account_new > 0:
                    print(f"    ✅ Collected {account_new} new tweets")
                
            except tweepy.errors.TooManyRequests as e:
                print(f"  ⚠️ Rate limited on @{account['username']}")
                wait_time = self.rate_limiter.handle_429_error()
                print(f"  ⏳ Backing off for {wait_time} seconds")
                continue
            except Exception as e:
                print(f"  ❌ Error with {account['username']}: {e}")
        
        self.db.commit()
        return new_tweets_count
    
    def collect_historical_tweets(self, days: int = 7) -> int:
        """
        Collect historical tweets from the last N days
        """
        # Format datetime for Twitter API (RFC3339 without microseconds)
        start_dt = datetime.now(timezone.utc) - timedelta(days=days)
        start_time = start_dt.replace(microsecond=0).isoformat().replace('+00:00', 'Z')
        new_tweets_count = 0
        
        # Clear session media tracking for new collection
        self.session_media_keys.clear()
        
        for account in ACCOUNTS_TO_FOLLOW:
            try:
                print(f"Collecting historical tweets from @{account['username']}...")
                
                # Wait if rate limited
                self.rate_limiter.wait_if_needed()
                
                self.rate_limiter.record_request()
                tweets = self.client.get_users_tweets(
                    id=account['id'],
                    start_time=start_time,
                    max_results=100,
                    tweet_fields=['created_at', 'public_metrics', 'referenced_tweets', 'entities', 'note_tweet', 'attachments'],
                    media_fields=['url', 'preview_image_url', 'alt_text', 'width', 'height', 'type'],
                    expansions=['attachments.media_keys', 'referenced_tweets.id', 'referenced_tweets.id.attachments.media_keys']
                )
                
                if not tweets.data:
                    continue
                
                # Process media
                media_dict = {}
                if tweets.includes and 'media' in tweets.includes:
                    for media in tweets.includes['media']:
                        media_dict[media.media_key] = media
                
                # Process referenced tweets (for getting full text of retweets)
                referenced_tweets_dict = {}
                if tweets.includes and 'tweets' in tweets.includes:
                    for ref_tweet in tweets.includes['tweets']:
                        referenced_tweets_dict[str(ref_tweet.id)] = ref_tweet
                
                # Save tweets
                for tweet in tweets.data:
                    if self._save_tweet(tweet, account, media_dict, referenced_tweets_dict):
                        new_tweets_count += 1
                
            except Exception as e:
                print(f"Error collecting historical tweets from {account['username']}: {e}")
        
        self.db.commit()
        return new_tweets_count
    
    def get_latest_tweet_time(self, username: str) -> datetime:
        """Get the timestamp of the most recent tweet for a user"""
        latest = self.db.query(Tweet).filter(
            Tweet.author_username == username
        ).order_by(Tweet.created_at.desc()).first()
        
        return latest.created_at if latest else datetime.now(timezone.utc) - timedelta(days=7)

def main():
    """Main function to run the collector"""
    collector = TwitterCollector()
    
    # Collect recent tweets
    print("Starting tweet collection...")
    new_tweets = collector.collect_tweets(max_results=50)
    print(f"Collected {new_tweets} new tweets")
    
    # Collect historical if needed
    if new_tweets == 0:
        print("No new tweets found, collecting historical data...")
        historical = collector.collect_historical_tweets(days=3)
        print(f"Collected {historical} historical tweets")

if __name__ == "__main__":
    main()