#!/usr/bin/env python3
"""
Test the summarization endpoint to see what's happening
"""

import sys
import os
from datetime import datetime, timezone, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import get_db, Tweet
from app.api.analytics import summarize_tweets

def test_summary():
    """Test the summary generation"""
    db = next(get_db())
    
    print("=" * 60)
    print("Testing Summarization")
    print("=" * 60)
    
    # Check how many tweets we have today
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
    today_tweets = db.query(Tweet).filter(
        Tweet.created_at >= today_start
    ).all()
    
    print(f"\n📊 Tweets today (since {today_start}):")
    print(f"   Count: {len(today_tweets)}")
    
    if today_tweets:
        print("\n   Sample tweets:")
        for tweet in today_tweets[:3]:
            print(f"   - @{tweet.author_username}: {tweet.text[:100]}...")
    
    # Check tweets in last 3 days
    three_days_ago = datetime.now(timezone.utc) - timedelta(days=3)
    recent_tweets = db.query(Tweet).filter(
        Tweet.created_at >= three_days_ago
    ).all()
    
    print(f"\n📊 Tweets in last 3 days:")
    print(f"   Count: {len(recent_tweets)}")
    
    # Check all tweets
    all_tweets = db.query(Tweet).all()
    print(f"\n📊 Total tweets in database:")
    print(f"   Count: {len(all_tweets)}")
    
    if all_tweets:
        # Get date range (handle timezone)
        dates = []
        for t in all_tweets:
            if t.created_at:
                if t.created_at.tzinfo is None:
                    dates.append(t.created_at.replace(tzinfo=timezone.utc))
                else:
                    dates.append(t.created_at)
        if dates:
            oldest = min(dates)
            newest = max(dates)
            print(f"   Date range: {oldest} to {newest}")
    
    # Test the summarization function directly
    print("\n" + "=" * 60)
    print("Testing summarization function directly...")
    print("=" * 60)
    
    # Test with "3days" period since "today" might not have tweets
    result = summarize_tweets(
        period="3days",
        tags=None,
        author=None,
        db=db
    )
    
    print(f"\n📝 Summary result:")
    print(f"   Summary length: {len(result.get('summary', ''))}")
    print(f"   Tweet count: {result.get('stats', {}).get('tweet_count', 0)}")
    print(f"   Summary preview: {result.get('summary', 'No summary')[:200]}...")
    
    db.close()

if __name__ == "__main__":
    test_summary()