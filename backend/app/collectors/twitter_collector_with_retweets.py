"""
Twitter collector that includes retweets
Uses the user timeline endpoint with exclude_retweets=False
"""
import os
import tweepy
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from ..models import Tweet, TweetMedia
from ..config import TWITTER_BEARER_TOKEN, ACCOUNTS_TO_FOLLOW
from ..rate_limiter import get_rate_limiter

class TwitterCollectorWithRetweets:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.client = tweepy.Client(
            bearer_token=TWITTER_BEARER_TOKEN,
            wait_on_rate_limit=False  # We handle rate limiting ourselves
        )
        self.rate_limiter = get_rate_limiter()
    
    def collect_all_tweets(self, max_results: int = 100) -> int:
        """
        Collect tweets INCLUDING RETWEETS from all tracked accounts
        """
        new_tweets_count = 0
        
        for account in ACCOUNTS_TO_FOLLOW:
            try:
                print(f"Collecting tweets (including RTs) from @{account['username']}...")
                
                # Wait if rate limited
                self.rate_limiter.wait_if_needed()
                
                # Record the request
                self.rate_limiter.record_request()
                
                # Get user's tweets INCLUDING retweets
                # Note: The API v2 get_users_tweets doesn't have exclude_retweets parameter
                # It excludes retweets by default and there's no way to include them
                # We need to use the timeline endpoint or get referenced tweets
                
                tweets = self.client.get_users_tweets(
                    id=account['id'],
                    max_results=min(max_results, 100),
                    tweet_fields=['created_at', 'public_metrics', 'referenced_tweets', 'entities', 'author_id'],
                    media_fields=['url', 'preview_image_url', 'alt_text'],
                    expansions=['attachments.media_keys', 'referenced_tweets.id', 'referenced_tweets.id.author_id'],
                    exclude=['replies']  # Still exclude replies but we want retweets
                )
                
                if not tweets.data:
                    print(f"  No tweets found")
                    continue
                
                # Process regular tweets
                media_dict = {}
                if tweets.includes and 'media' in tweets.includes:
                    for media in tweets.includes['media']:
                        media_dict[media.media_key] = media
                
                # Process referenced tweets (includes retweets)
                referenced_tweets = {}
                if tweets.includes and 'tweets' in tweets.includes:
                    for ref_tweet in tweets.includes['tweets']:
                        referenced_tweets[str(ref_tweet.id)] = ref_tweet
                
                # Save tweets
                for tweet in tweets.data:
                    # Check if it's a retweet
                    is_retweet = False
                    retweeted_text = None
                    
                    if tweet.referenced_tweets:
                        for ref in tweet.referenced_tweets:
                            if ref.type == 'retweeted':
                                is_retweet = True
                                # Get the original tweet text if available
                                if str(ref.id) in referenced_tweets:
                                    retweeted_text = referenced_tweets[str(ref.id)].text
                                break
                    
                    # Save the tweet (or retweet)
                    if self._save_tweet_with_retweet_info(tweet, account, media_dict, is_retweet, retweeted_text):
                        new_tweets_count += 1
                        if is_retweet:
                            print(f"  ✅ Saved retweet from @{account['username']}")
                
                print(f"  Total: {new_tweets_count} new items (tweets + retweets)")
                
            except tweepy.errors.TooManyRequests as e:
                print(f"  ⚠️ Rate limited: {e}")
                self.rate_limiter.handle_429_error()
                break
            except Exception as e:
                print(f"  ❌ Error: {e}")
                continue
        
        self.db.commit()
        return new_tweets_count
    
    def collect_since_with_retweets(self, since_time: datetime) -> int:
        """
        Collect tweets and retweets since a specific time
        """
        if since_time.tzinfo is None:
            since_time = since_time.replace(tzinfo=timezone.utc)
        
        start_time = since_time.replace(microsecond=0).isoformat().replace('+00:00', 'Z')
        end_time = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
        
        new_count = 0
        
        for account in ACCOUNTS_TO_FOLLOW:
            try:
                print(f"Checking @{account['username']} (with retweets)...")
                
                self.rate_limiter.wait_if_needed()
                self.rate_limiter.record_request()
                
                # Get tweets AND retweets
                tweets = self.client.get_users_tweets(
                    id=account['id'],
                    start_time=start_time,
                    end_time=end_time,
                    max_results=100,
                    tweet_fields=['created_at', 'public_metrics', 'referenced_tweets', 'entities', 'author_id'],
                    expansions=['referenced_tweets.id', 'referenced_tweets.id.author_id'],
                    exclude=['replies']
                )
                
                if not tweets.data:
                    print(f"  No new tweets/retweets")
                    continue
                
                # Process referenced tweets
                referenced_tweets = {}
                if tweets.includes and 'tweets' in tweets.includes:
                    for ref_tweet in tweets.includes['tweets']:
                        referenced_tweets[str(ref_tweet.id)] = ref_tweet
                
                # Save all tweets and retweets
                account_count = 0
                for tweet in tweets.data:
                    is_retweet = any(
                        ref.type == 'retweeted' 
                        for ref in (tweet.referenced_tweets or [])
                    )
                    
                    retweeted_text = None
                    if is_retweet and tweet.referenced_tweets:
                        for ref in tweet.referenced_tweets:
                            if ref.type == 'retweeted' and str(ref.id) in referenced_tweets:
                                retweeted_text = referenced_tweets[str(ref.id)].text
                                break
                    
                    if self._save_tweet_with_retweet_info(tweet, account, {}, is_retweet, retweeted_text):
                        account_count += 1
                        new_count += 1
                
                if account_count > 0:
                    print(f"  ✅ {account_count} new items (tweets/RTs)")
                
            except Exception as e:
                if "429" in str(e):
                    print(f"  ❌ Rate limited")
                    self.rate_limiter.handle_429_error()
                    break
                print(f"  Error: {e}")
        
        self.db.commit()
        return new_count
    
    def _save_tweet_with_retweet_info(self, tweet_data: Any, account: Dict, media_dict: Dict, 
                                       is_retweet: bool, retweeted_text: Optional[str]) -> bool:
        """
        Save tweet with retweet information
        """
        # Check if already exists
        existing = self.db.query(Tweet).filter(Tweet.id == str(tweet_data.id)).first()
        if existing:
            return False
        
        # For retweets, combine the RT indicator with original text
        text = tweet_data.text
        if is_retweet and retweeted_text:
            text = f"RT: {retweeted_text}"
        elif is_retweet:
            text = f"RT: {text}"
        
        # Create tweet record
        tweet = Tweet(
            id=str(tweet_data.id),
            text=text,
            author_id=account['id'],
            author_name=account.get('name', account['username']),
            author_username=account['username'],
            created_at=tweet_data.created_at,
            retweet_count=tweet_data.public_metrics.get('retweet_count', 0) if tweet_data.public_metrics else 0,
            reply_count=tweet_data.public_metrics.get('reply_count', 0) if tweet_data.public_metrics else 0,
            like_count=tweet_data.public_metrics.get('like_count', 0) if tweet_data.public_metrics else 0,
            quote_count=tweet_data.public_metrics.get('quote_count', 0) if tweet_data.public_metrics else 0,
            bookmark_count=tweet_data.public_metrics.get('bookmark_count', 0) if tweet_data.public_metrics else 0,
            impression_count=tweet_data.public_metrics.get('impression_count', 0) if tweet_data.public_metrics else 0,
            is_retweet=is_retweet,
            collected_at=datetime.now(timezone.utc)
        )
        
        # Handle referenced tweets
        if tweet_data.referenced_tweets:
            for ref in tweet_data.referenced_tweets:
                if ref.type == 'retweeted':
                    tweet.retweeted_tweet_id = str(ref.id)
                elif ref.type == 'quoted':
                    tweet.quoted_tweet_id = str(ref.id)
                    tweet.is_quote = True
                elif ref.type == 'replied_to':
                    tweet.replied_to_id = str(ref.id)
                    tweet.is_reply = True
        
        self.db.add(tweet)
        
        # Save media if present
        if hasattr(tweet_data, 'attachments') and tweet_data.attachments and 'media_keys' in tweet_data.attachments:
            for media_key in tweet_data.attachments['media_keys']:
                if media_key in media_dict:
                    media = media_dict[media_key]
                    tweet_media = TweetMedia(
                        tweet_id=str(tweet_data.id),
                        media_url=media.url if hasattr(media, 'url') else media.preview_image_url,
                        media_type=media.type,
                        alt_text=media.alt_text if hasattr(media, 'alt_text') else None
                    )
                    self.db.add(tweet_media)
        
        return True