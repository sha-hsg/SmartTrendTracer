#!/usr/bin/env python3
"""
Collect ALL tweets including retweets using cookies
"""
import sys
import os
from datetime import datetime, timezone, timedelta
import requests
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db, Tweet, CollectionState
from app.config import ACCOUNTS_TO_FOLLOW
from sqlalchemy import func

def collect_with_cookies():
    print("🍪 COOKIE-BASED COLLECTION (WITH RETWEETS!)")
    print("=" * 60)
    
    # Your cookies
    cookies = {
        'auth_token': '8a9436096a3a228509a01a63659538d58332aec5',
        'ct0': 'fab91742a9bda85ada33f4435e0793ce4ead14b6c07b88210ce59afac02d68d35ca0e1f6c052a22d67835e4d063f2d8eecf74ca7e23a62d21529209d00bf5ecd741c8daaa948bd2083085d813036c1d0'
    }
    
    headers = {
        'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
        'x-csrf-token': cookies['ct0'],
        'x-twitter-active-user': 'yes',
        'x-twitter-auth-type': 'OAuth2Session',
        'Cookie': f"auth_token={cookies['auth_token']}; ct0={cookies['ct0']}"
    }
    
    db = next(get_db())
    
    print("📊 Collecting from accounts:")
    for account in ACCOUNTS_TO_FOLLOW:
        print(f"   • @{account['username']}")
    print()
    
    new_tweets = 0
    new_retweets = 0
    
    for account in ACCOUNTS_TO_FOLLOW:
        try:
            print(f"\n🔄 Checking @{account['username']}...")
            
            # Use Twitter API v1.1 endpoint that includes retweets
            url = f"https://api.twitter.com/1.1/statuses/user_timeline.json"
            params = {
                'user_id': account['id'],
                'count': 50,
                'include_rts': 'true',  # This is the key - includes retweets!
                'tweet_mode': 'extended'
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                tweets = response.json()
                
                for tweet_data in tweets:
                    # Check if it's a retweet
                    is_retweet = 'retweeted_status' in tweet_data
                    
                    tweet_id = str(tweet_data['id_str'])
                    
                    # Check if already exists
                    existing = db.query(Tweet).filter(Tweet.id == tweet_id).first()
                    if existing:
                        continue
                    
                    # Get text
                    if is_retweet:
                        text = f"RT @{tweet_data['retweeted_status']['user']['screen_name']}: {tweet_data['retweeted_status'].get('full_text', tweet_data['retweeted_status'].get('text', ''))}"
                        new_retweets += 1
                        print(f"   🔁 Found RETWEET: {text[:60]}...")
                    else:
                        text = tweet_data.get('full_text', tweet_data.get('text', ''))
                    
                    # Create tweet record
                    tweet = Tweet(
                        id=tweet_id,
                        text=text,
                        author_id=str(account['id']),
                        author_name=account.get('name', account['username']),
                        author_username=account['username'],
                        created_at=datetime.strptime(tweet_data['created_at'], '%a %b %d %H:%M:%S +0000 %Y').replace(tzinfo=timezone.utc),
                        retweet_count=tweet_data.get('retweet_count', 0),
                        reply_count=0,
                        like_count=tweet_data.get('favorite_count', 0),
                        quote_count=tweet_data.get('quote_count', 0),
                        is_retweet=is_retweet,
                        collected_at=datetime.now(timezone.utc)
                    )
                    
                    db.add(tweet)
                    new_tweets += 1
                
                print(f"   ✅ Got {len(tweets)} items")
            
            elif response.status_code == 401:
                print(f"   ❌ Authentication failed - cookies might be expired")
                print("   Please login to Twitter and get fresh cookies")
                break
            elif response.status_code == 429:
                print(f"   ⚠️  Rate limited (but much higher than API!)")
            else:
                print(f"   ❌ Error {response.status_code}: {response.text[:100]}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    db.commit()
    
    # Update collection state
    CollectionState.update_last_run(db, tweet_count=new_tweets)
    
    # Get stats
    total_tweets = db.query(func.count(Tweet.id)).scalar()
    recent_tweets = db.query(func.count(Tweet.id)).filter(
        Tweet.created_at >= datetime.now(timezone.utc) - timedelta(hours=24)
    ).scalar()
    total_retweets = db.query(func.count(Tweet.id)).filter(Tweet.is_retweet == True).scalar()
    
    print("\n" + "=" * 60)
    print("🎉 COOKIE COLLECTION COMPLETE!")
    print("=" * 60)
    print(f"📊 Results:")
    print(f"   • New tweets collected: {new_tweets}")
    print(f"   • New RETWEETS found: {new_retweets} 🎆")
    print(f"   • Total tweets in DB: {total_tweets}")
    print(f"   • Total retweets in DB: {total_retweets}")
    print(f"   • Last 24h tweets: {recent_tweets}")
    
    if new_retweets > 0:
        print(f"\n✨ SUCCESS! We captured {new_retweets} retweets that the API misses!")
    
    db.close()

if __name__ == "__main__":
    print("This will collect ALL tweets including RETWEETS using cookies.\n")
    collect_with_cookies()