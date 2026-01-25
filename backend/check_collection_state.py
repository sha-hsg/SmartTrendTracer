#!/usr/bin/env python3
"""
Check the collection state in MongoDB

Uses MongoDB for data storage (migrated from SQLite January 2026)
"""
import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.mongodb import get_database

def check_state():
    db = get_database()

    print("Checking Collection State")
    print("=" * 50)

    # Check collection state
    state = db.collection_state.find_one({"key": "main"})

    if state:
        last_run = state.get('last_run')
        print(f"\nCollection State Record:")
        print(f"   Last run (raw): {last_run}")
        print(f"   Last run type: {type(last_run)}")

        if last_run:
            # Calculate proper time difference
            now = datetime.now(timezone.utc)

            # Make last_run timezone-aware if needed
            if hasattr(last_run, 'tzinfo') and last_run.tzinfo is None:
                last_run_aware = last_run.replace(tzinfo=timezone.utc)
            else:
                last_run_aware = last_run

            time_diff = now - last_run_aware
            hours_ago = time_diff.total_seconds() / 3600

            print(f"\nTime calculations:")
            print(f"   Current time UTC: {now}")
            print(f"   Last run (aware): {last_run_aware}")
            print(f"   Time difference: {time_diff}")
            print(f"   Hours ago: {hours_ago:.1f}")

            if hours_ago < 0.1:
                print(f"\nWARNING: Last run appears to be in the future or very recent!")
                print(f"   This might be a timezone issue")
    else:
        print("\nNo collection state found (first run)")

    # Check latest tweets by author
    print(f"\nLatest Tweets by Author:")
    pipeline = [
        {
            '$group': {
                '_id': '$author_username',
                'latest': {'$max': '$created_at'},
                'count': {'$sum': 1}
            }
        },
        {'$sort': {'latest': -1}}
    ]

    results = list(db.tweets.aggregate(pipeline))

    now = datetime.now(timezone.utc)
    for result in results:
        username = result['_id']
        latest = result['latest']
        count = result['count']

        if latest:
            # Make timezone-aware if needed
            if hasattr(latest, 'tzinfo') and latest.tzinfo is None:
                latest_aware = latest.replace(tzinfo=timezone.utc)
            else:
                latest_aware = latest

            hours_ago = (now - latest_aware).total_seconds() / 3600
            print(f"   @{username}: {count} tweets, latest {hours_ago:.1f}h ago")
        else:
            print(f"   @{username}: {count} tweets, no timestamp")

    # Show total count
    total = db.tweets.count_documents({})
    print(f"\nTotal tweets in database: {total}")

if __name__ == "__main__":
    check_state()
