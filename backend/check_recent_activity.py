#!/usr/bin/env python3
"""
Check recent activity including retweets using search
"""
import sys
import os
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tweepy
from app.config import TWITTER_BEARER_TOKEN, ACCOUNTS_TO_FOLLOW
from app.rate_limiter import get_rate_limiter

def check_recent_activity():
    print("🔍 CHECKING RECENT TWITTER ACTIVITY")
    print("=" * 60)
    
    client = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN)
    rate_limiter = get_rate_limiter()
    
    print("⚠️  Note: Twitter API v2 Basic tier limitations:")
    print("   • get_users_tweets excludes retweets (no way to include them)")
    print("   • Search API not available in Basic tier")
    print("   • User timeline endpoint not available in Basic tier")
    print()
    
    for account in ACCOUNTS_TO_FOLLOW:
        try:
            print(f"\n👤 @{account['username']} (ID: {account['id']})")
            
            # Check rate limit
            if not rate_limiter.can_make_request():
                print("   ❌ Rate limited, stopping")
                break
            
            rate_limiter.record_request()
            
            # Get recent tweets (excludes retweets unfortunately)
            tweets = client.get_users_tweets(
                id=account['id'],
                max_results=5,
                tweet_fields=['created_at', 'public_metrics', 'referenced_tweets'],
                exclude=['replies']
            )
            
            if tweets.data:
                for i, tweet in enumerate(tweets.data, 1):
                    age = datetime.now(timezone.utc) - tweet.created_at
                    hours_ago = age.total_seconds() / 3600
                    
                    # Check if it's a retweet (won't appear but check referenced_tweets)
                    tweet_type = "Tweet"
                    if tweet.referenced_tweets:
                        for ref in tweet.referenced_tweets:
                            if ref.type == 'retweeted':
                                tweet_type = "Retweet"
                            elif ref.type == 'quoted':
                                tweet_type = "Quote Tweet"
                    
                    print(f"   {i}. {tweet_type} ({hours_ago:.1f}h ago)")
                    print(f"      {tweet.text[:80]}...")
                    print(f"      ❤️ {tweet.public_metrics['like_count']} 🔁 {tweet.public_metrics['retweet_count']}")
            else:
                print("   No recent tweets found")
            
            # Try to get user info to see tweet count
            try:
                rate_limiter.record_request()
                user = client.get_user(
                    id=account['id'],
                    user_fields=['public_metrics', 'created_at']
                )
                
                if user.data:
                    print(f"   📊 Total tweets: {user.data.public_metrics['tweet_count']}")
            except:
                pass
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("💡 IMPORTANT: Retweets are NOT captured!")
    print("   Twitter API v2 Basic tier cannot retrieve retweets.")
    print("   The Hugging Face retweet you saw won't appear in our data.")
    print("\n🔧 Solutions:")
    print("   1. Upgrade to Twitter API Pro tier ($100/month) for full access")
    print("   2. Use web scraping (twscrape) with manual login")
    print("   3. Accept that we only track original tweets (current state)")

if __name__ == "__main__":
    check_recent_activity()