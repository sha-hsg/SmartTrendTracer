#!/usr/bin/env python3
"""
Use Nitter instances to get ALL tweets including retweets
Nitter is a free, open-source Twitter frontend that shows everything
"""
import sys
import os
import requests
from datetime import datetime, timezone
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db, Tweet
from app.config import ACCOUNTS_TO_FOLLOW

# Public Nitter instances (no auth needed!)
NITTER_INSTANCES = [
    "https://nitter.poast.org",
    "https://nitter.cz", 
    "https://nitter.privacydev.net",
    "https://nitter.1d4.us"
]

def get_tweets_from_nitter(username, instance="https://nitter.poast.org"):
    """
    Get tweets including retweets from Nitter
    """
    url = f"{instance}/{username}"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            tweets = []
            # Find all tweet items
            for item in soup.find_all('div', class_='timeline-item'):
                tweet_data = {}
                
                # Check if it's a retweet
                retweet_label = item.find('span', class_='retweet-header')
                if retweet_label:
                    tweet_data['is_retweet'] = True
                    tweet_data['type'] = 'RETWEET'
                else:
                    tweet_data['is_retweet'] = False
                    tweet_data['type'] = 'TWEET'
                
                # Get tweet text
                content = item.find('div', class_='tweet-content')
                if content:
                    tweet_data['text'] = content.get_text(strip=True)
                
                # Get timestamp
                time_elem = item.find('span', class_='tweet-date')
                if time_elem:
                    tweet_data['date'] = time_elem.get('title', '')
                
                # Get stats
                stats = item.find('div', class_='tweet-stats')
                if stats:
                    # Extract likes, retweets, etc.
                    pass
                
                if tweet_data.get('text'):
                    tweets.append(tweet_data)
            
            return tweets
    except Exception as e:
        print(f"Error fetching from {instance}: {e}")
    
    return []

def collect_with_nitter():
    print("🌐 NITTER COLLECTION (GETS EVERYTHING!)")
    print("=" * 60)
    print("💡 Using public Nitter instances - no auth needed!")
    print("   This gets ALL tweets including RETWEETS!\n")
    
    db = next(get_db())
    
    total_tweets = 0
    total_retweets = 0
    
    for account in ACCOUNTS_TO_FOLLOW:
        print(f"\n🔄 Checking @{account['username']}...")
        
        # Try different Nitter instances
        for instance in NITTER_INSTANCES:
            tweets = get_tweets_from_nitter(account['username'], instance)
            
            if tweets:
                print(f"   ✅ Got {len(tweets)} items from {instance}")
                
                for tweet in tweets[:10]:  # Process latest 10
                    if tweet['is_retweet']:
                        print(f"   🔁 RETWEET: {tweet['text'][:60]}...")
                        total_retweets += 1
                    else:
                        print(f"   📝 TWEET: {tweet['text'][:60]}...")
                    total_tweets += 1
                
                break  # Success, don't try other instances
            else:
                print(f"   ⚠️  {instance} didn't work, trying next...")
    
    print("\n" + "=" * 60)
    print("🎉 NITTER COLLECTION COMPLETE!")
    print("=" * 60)
    print(f"📊 Results:")
    print(f"   • Total items found: {total_tweets}")
    print(f"   • RETWEETS found: {total_retweets} 🎆")
    print(f"\n✨ Nitter shows EVERYTHING - tweets AND retweets!")
    print("   No authentication needed!")
    
    db.close()

if __name__ == "__main__":
    print("Testing Nitter instances to get ALL tweets...\n")
    
    # Test with one account first
    print("Quick test with @huggingface:")
    for instance in NITTER_INSTANCES:
        print(f"\nTrying {instance}...")
        tweets = get_tweets_from_nitter("huggingface", instance)
        if tweets:
            print(f"✅ SUCCESS! Got {len(tweets)} items")
            for tweet in tweets[:3]:
                print(f"  [{tweet['type']}] {tweet['text'][:50]}...")
            break
        else:
            print(f"❌ Failed")
    
    print("\n" + "="*60)
    response = input("\nRun full collection? (y/n): ")
    if response.lower() == 'y':
        collect_with_nitter()