"""
Twscrape-based Twitter collector (no rate limits)
Uses web scraping instead of official API
"""
import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
import logging
from pathlib import Path

from twscrape import API, gather
from twscrape.models import Tweet as TwscrapeTweet
from sqlalchemy.orm import Session

from ..models import Tweet, TweetMedia
from ..config import ACCOUNTS_TO_FOLLOW

logger = logging.getLogger(__name__)

class TwscrapeCollector:
    """
    Twitter collector using twscrape (web scraping)
    No rate limits but requires login accounts
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.api = API()
        self.accounts_db = Path("data/twscrape_accounts.db")
        self.logged_in = False
        
    async def setup_accounts(self):
        """
        Setup twscrape accounts for scraping
        Can use guest tokens or login credentials
        """
        try:
            # Check if we have any accounts
            accounts = await self.api.pool.accounts_info()
            
            if not accounts:
                logger.info("No accounts found, adding guest account")
                # Use guest account (limited but no login required)
                await self.api.pool.add_account(
                    username="guest",
                    password="guest",
                    email="guest@example.com",
                    email_password="guest"
                )
                await self.api.pool.login_all()
            
            self.logged_in = True
            logger.info(f"Twscrape setup complete with {len(accounts)} accounts")
            
        except Exception as e:
            logger.error(f"Failed to setup twscrape accounts: {e}")
            raise
    
    def _convert_tweet(self, tw_tweet: TwscrapeTweet, account_info: Dict) -> Dict:
        """
        Convert twscrape Tweet to our database format
        """
        return {
            'id': str(tw_tweet.id),
            'text': tw_tweet.rawContent,
            'created_at': tw_tweet.date,
            'author_id': str(tw_tweet.user.id),
            'author_name': tw_tweet.user.displayname,
            'author_username': tw_tweet.user.username,
            'retweet_count': tw_tweet.retweetCount,
            'reply_count': tw_tweet.replyCount,
            'like_count': tw_tweet.likeCount,
            'quote_count': tw_tweet.quoteCount,
            'bookmark_count': tw_tweet.bookmarkCount,
            'impression_count': tw_tweet.viewCount,
            'url': tw_tweet.url,
            'is_retweet': tw_tweet.retweetedTweet is not None,
            'is_quote': tw_tweet.quotedTweet is not None,
            'is_reply': tw_tweet.inReplyToTweetId is not None,
            'replied_to_id': tw_tweet.inReplyToTweetId,
            'quoted_tweet_id': tw_tweet.quotedTweet.id if tw_tweet.quotedTweet else None,
            'retweeted_tweet_id': tw_tweet.retweetedTweet.id if tw_tweet.retweetedTweet else None,
            'collected_at': datetime.now(timezone.utc)
        }
    
    def _save_tweet(self, tweet_data: Dict) -> bool:
        """
        Save tweet to database
        """
        try:
            # Check if tweet already exists
            existing = self.db.query(Tweet).filter(Tweet.id == tweet_data['id']).first()
            if existing:
                return False
            
            # Create new tweet
            tweet = Tweet(**tweet_data)
            self.db.add(tweet)
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving tweet {tweet_data.get('id')}: {e}")
            return False
    
    async def collect_user_tweets(self, username: str, since: Optional[datetime] = None, limit: int = 100) -> int:
        """
        Collect tweets from a specific user
        """
        if not self.logged_in:
            await self.setup_accounts()
        
        new_tweets = 0
        
        try:
            logger.info(f"Collecting tweets from @{username}")
            
            # Find account info
            account_info = next((a for a in ACCOUNTS_TO_FOLLOW if a['username'] == username), None)
            if not account_info:
                logger.warning(f"Account @{username} not in tracked accounts")
                return 0
            
            # Collect tweets
            tweets = []
            async for tweet in self.api.user_tweets(username, limit=limit):
                # Check date if since is provided
                if since and tweet.date < since:
                    break
                
                tweets.append(tweet)
            
            # Save tweets
            for tw_tweet in tweets:
                tweet_data = self._convert_tweet(tw_tweet, account_info)
                if self._save_tweet(tweet_data):
                    new_tweets += 1
                    
                    # Save media if present
                    if tw_tweet.media:
                        for media in tw_tweet.media:
                            media_data = {
                                'tweet_id': str(tw_tweet.id),
                                'media_url': media.get('url', ''),
                                'media_type': media.get('type', 'photo'),
                                'alt_text': media.get('alt_text', '')
                            }
                            
                            try:
                                tweet_media = TweetMedia(**media_data)
                                self.db.add(tweet_media)
                            except Exception as e:
                                logger.error(f"Error saving media: {e}")
            
            self.db.commit()
            logger.info(f"Collected {new_tweets} new tweets from @{username}")
            
        except Exception as e:
            logger.error(f"Error collecting from @{username}: {e}")
            self.db.rollback()
        
        return new_tweets
    
    async def collect_all_accounts(self, since: Optional[datetime] = None) -> int:
        """
        Collect tweets from all tracked accounts
        """
        if not since:
            since = datetime.now(timezone.utc) - timedelta(hours=24)
        
        total_new = 0
        
        for account in ACCOUNTS_TO_FOLLOW:
            try:
                new_tweets = await self.collect_user_tweets(
                    username=account['username'],
                    since=since,
                    limit=100
                )
                total_new += new_tweets
                
                # Small delay between accounts to be respectful
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error collecting from @{account['username']}: {e}")
                continue
        
        return total_new
    
    async def search_tweets(self, query: str, limit: int = 100) -> int:
        """
        Search for tweets (bonus feature not available in API)
        """
        if not self.logged_in:
            await self.setup_accounts()
        
        new_tweets = 0
        
        try:
            logger.info(f"Searching for: {query}")
            
            async for tweet in self.api.search(query, limit=limit):
                # Only save if from tracked accounts
                if tweet.user.username in [a['username'] for a in ACCOUNTS_TO_FOLLOW]:
                    account_info = next(a for a in ACCOUNTS_TO_FOLLOW if a['username'] == tweet.user.username)
                    tweet_data = self._convert_tweet(tweet, account_info)
                    
                    if self._save_tweet(tweet_data):
                        new_tweets += 1
            
            self.db.commit()
            logger.info(f"Found {new_tweets} new tweets for query: {query}")
            
        except Exception as e:
            logger.error(f"Error searching tweets: {e}")
            self.db.rollback()
        
        return new_tweets


def run_twscrape_collection(since_hours: int = 24):
    """
    Synchronous wrapper for async collection
    """
    from ..models import get_db
    
    async def _collect():
        db = next(get_db())
        collector = TwscrapeCollector(db_session=db)
        
        since = datetime.now(timezone.utc) - timedelta(hours=since_hours)
        new_tweets = await collector.collect_all_accounts(since=since)
        
        db.close()
        return new_tweets
    
    return asyncio.run(_collect())