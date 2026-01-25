#!/usr/bin/env python3
"""
Monitor collection status and statistics

Uses MongoDB for data storage (migrated from SQLite January 2026)
"""
import sys
import os
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.mongodb import get_database
from app.config import ACCOUNTS_TO_FOLLOW

def monitor_collection():
    print("COLLECTION MONITOR")
    print("=" * 60)

    db = get_database()

    try:
        # Get collection state
        state = db.collection_state.find_one({"key": "main"})
        last_run = state.get('last_run') if state else None

        if last_run:
            if hasattr(last_run, 'tzinfo') and last_run.tzinfo is None:
                last_run = last_run.replace(tzinfo=timezone.utc)
            time_since = datetime.now(timezone.utc) - last_run
            print(f"\nLast Collection:")
            print(f"   Time: {last_run.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            print(f"   {time_since.total_seconds() / 3600:.1f} hours ago")
        else:
            print("\nNo collection history found")

        # Get database statistics
        total_tweets = db.tweets.count_documents({})

        # Most recent tweet
        recent_tweet = db.tweets.find_one(sort=[('created_at', -1)])
        if recent_tweet:
            created_at = recent_tweet.get('created_at')
            if created_at:
                if hasattr(created_at, 'tzinfo') and created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
                tweet_age = datetime.now(timezone.utc) - created_at
                print(f"\nMost Recent Tweet:")
                print(f"   From: @{recent_tweet.get('author_username', 'unknown')}")
                print(f"   Time: {created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                print(f"   {tweet_age.total_seconds() / 3600:.1f} hours ago")

        # Tweets by time period
        print(f"\nTweet Distribution:")
        periods = [
            (1, "Last hour"),
            (6, "Last 6 hours"),
            (24, "Last 24 hours"),
            (72, "Last 3 days"),
            (168, "Last week")
        ]

        for hours, label in periods:
            since = datetime.now(timezone.utc) - timedelta(hours=hours)
            count = db.tweets.count_documents({'created_at': {'$gte': since}})
            if count > 0:
                print(f"   {label}: {count} tweets")

        print(f"   Total: {total_tweets} tweets")

        # Tweets by account
        print(f"\nTweets by Account:")
        pipeline = [
            {
                '$group': {
                    '_id': '$author_username',
                    'count': {'$sum': 1},
                    'latest': {'$max': '$created_at'}
                }
            },
            {'$sort': {'latest': -1}}
        ]

        account_stats = list(db.tweets.aggregate(pipeline))

        now = datetime.now(timezone.utc)
        for stat in account_stats:
            username = stat['_id']
            count = stat['count']
            latest = stat['latest']

            if latest:
                if hasattr(latest, 'tzinfo') and latest.tzinfo is None:
                    latest = latest.replace(tzinfo=timezone.utc)
                age = now - latest
                age_str = f"{age.total_seconds() / 3600:.1f}h ago"
            else:
                age_str = "unknown"

            print(f"   @{username}: {count} tweets (latest: {age_str})")

        # Check for gaps
        print(f"\nGap Analysis:")

        # Check each account for gaps
        gaps_found = False
        for account in ACCOUNTS_TO_FOLLOW:
            account_tweet = db.tweets.find_one(
                {'author_id': str(account['id'])},
                sort=[('created_at', -1)]
            )

            if account_tweet:
                latest = account_tweet.get('created_at')
                if latest:
                    if hasattr(latest, 'tzinfo') and latest.tzinfo is None:
                        latest = latest.replace(tzinfo=timezone.utc)
                    gap = (now - latest).total_seconds() / 3600

                    if gap > 24:  # More than 24 hours since last tweet
                        print(f"   @{account['username']}: No tweets for {gap:.1f} hours")
                        gaps_found = True

        if not gaps_found:
            print("   No significant gaps detected")

        # Recommendations
        print(f"\nRecommendations:")

        if last_run:
            hours_since = time_since.total_seconds() / 3600
            if hours_since > 6:
                print(f"   Consider running collection (last run {hours_since:.1f}h ago)")
            elif hours_since > 1:
                print(f"   Collection is recent but you can run if needed")
            else:
                print(f"   Collection very recent, no action needed")
        else:
            print(f"   Run initial collection with tweet_collector_service.py")

        print("\n" + "=" * 60)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    monitor_collection()
