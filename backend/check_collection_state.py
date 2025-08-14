#!/usr/bin/env python3
"""
Check the collection state in the database
"""
import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db, CollectionState, Tweet
from sqlalchemy import func

def check_state():
    db = next(get_db())
    
    print("🔍 Checking Collection State")
    print("=" * 50)
    
    # Check collection state
    state = db.query(CollectionState).filter(CollectionState.key == "main").first()
    
    if state:
        print(f"\n📊 Collection State Record:")
        print(f"   Last run (raw): {state.last_run}")
        print(f"   Last run type: {type(state.last_run)}")
        print(f"   Timezone info: {state.last_run.tzinfo}")
        
        # Calculate proper time difference
        now = datetime.now(timezone.utc)
        
        # Make last_run timezone-aware if needed
        if state.last_run.tzinfo is None:
            last_run_aware = state.last_run.replace(tzinfo=timezone.utc)
        else:
            last_run_aware = state.last_run
            
        time_diff = now - last_run_aware
        hours_ago = time_diff.total_seconds() / 3600
        
        print(f"\n⏰ Time calculations:")
        print(f"   Current time UTC: {now}")
        print(f"   Last run (aware): {last_run_aware}")
        print(f"   Time difference: {time_diff}")
        print(f"   Hours ago: {hours_ago:.1f}")
        
        if hours_ago < 0.1:
            print(f"\n⚠️  WARNING: Last run appears to be in the future or very recent!")
            print(f"   This might be a timezone issue")
    else:
        print("\n❌ No collection state found (first run)")
    
    # Check latest tweets
    print(f"\n📝 Latest Tweets:")
    latest_tweets = db.query(
        Tweet.author_username,
        func.max(Tweet.created_at).label('latest'),
        func.count(Tweet.id).label('count')
    ).group_by(Tweet.author_username).all()
    
    for tweet in latest_tweets:
        if tweet.latest.tzinfo is None:
            tweet_time = tweet.latest.replace(tzinfo=timezone.utc)
        else:
            tweet_time = tweet.latest
            
        hours_ago = (datetime.now(timezone.utc) - tweet_time).total_seconds() / 3600
        print(f"   @{tweet.author_username}: {tweet.count} tweets, latest {hours_ago:.1f}h ago")
    
    db.close()

if __name__ == "__main__":
    check_state()