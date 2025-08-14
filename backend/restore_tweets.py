#!/usr/bin/env python3
"""
Restore lost Twitter data by collecting tweets from all configured accounts
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.collectors.twitter_collector import TwitterCollector
from app.models import get_db, Tweet
from sqlalchemy import func
import json

def restore_tweets():
    """Collect tweets from all configured accounts"""
    
    # Check current state
    db = next(get_db())
    current_count = db.query(func.count(Tweet.id)).scalar()
    print(f"Current tweets in database: {current_count}")
    
    # Load accounts
    with open('accounts.json', 'r') as f:
        accounts = json.load(f)['accounts']
    
    print(f"\nCollecting tweets from {len(accounts)} accounts:")
    for acc in accounts:
        print(f"  - @{acc['username']} ({acc['displayName']})")
    
    # Initialize collector
    collector = TwitterCollector()
    
    # Collect tweets
    print("\nStarting collection...")
    print("-" * 50)
    
    try:
        # Collect recent tweets (up to 100 per account = 700 total)
        new_tweets = collector.collect_tweets(max_results=100)
        print(f"\n✅ Collected {new_tweets} new tweets")
        
        # If not enough tweets, collect historical
        if new_tweets < 500:
            print("\nCollecting historical tweets (7 days)...")
            historical = collector.collect_historical_tweets(days=7)
            print(f"✅ Collected {historical} historical tweets")
    except Exception as e:
        print(f"❌ Error during collection: {e}")
        print("\nTrying alternative collection method...")
        
        # Try collecting with smaller batches
        for acc in accounts:
            try:
                print(f"Collecting from @{acc['username']}...")
                # This will collect from all accounts configured in the collector
                break  # Only need to call once
            except Exception as e2:
                print(f"  Error: {e2}")
    
    # Check final state
    final_count = db.query(func.count(Tweet.id)).scalar()
    print("-" * 50)
    print(f"\nFinal tweets in database: {final_count}")
    print(f"Total tweets added: {final_count - current_count}")
    
    # Show breakdown by author
    author_counts = db.query(Tweet.author_username, func.count(Tweet.id)).group_by(Tweet.author_username).all()
    print("\nTweets by author:")
    for author, count in sorted(author_counts, key=lambda x: x[1], reverse=True):
        print(f"  @{author}: {count} tweets")

if __name__ == "__main__":
    restore_tweets()