#!/usr/bin/env python3
"""
Check if enhanced retweet collection is working
"""

from pymongo import MongoClient
from datetime import datetime, timedelta

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client.smarttrendtracer

print("=" * 60)
print("RETWEET ENHANCEMENT STATUS CHECK")
print("=" * 60)

# Check total tweets
total = db.tweets.count_documents({})
print(f"\n📊 Total tweets in database: {total}")

# Check retweets
retweets = db.tweets.count_documents({"text": {"$regex": "^RT @"}})
print(f"📝 Total retweets: {retweets}")

# Check enhanced retweets (with full_text)
enhanced = db.tweets.count_documents({"full_text": {"$exists": True}})
print(f"✨ Enhanced retweets (with full_text): {enhanced}")

# Check recent retweets
recent_date = datetime.utcnow() - timedelta(hours=24)
recent_retweets = list(db.tweets.find({
    "text": {"$regex": "^RT @"},
    "created_at": {"$gte": recent_date}
}).limit(5))

if recent_retweets:
    print(f"\n🕐 Recent retweets (last 24 hours):")
    for tweet in recent_retweets:
        has_full = "✅" if "full_text" in tweet else "❌"
        print(f"  {has_full} {tweet['created_at'].strftime('%Y-%m-%d %H:%M')} - {tweet['text'][:80]}...")
        if "full_text" in tweet:
            print(f"      Full text: {tweet['full_text'][:100]}...")
else:
    print("\n📭 No retweets collected in the last 24 hours")

# Check for original_media in retweets
media_retweets = db.tweets.count_documents({"original_media": {"$exists": True, "$ne": []}})
print(f"\n🖼️  Retweets with original media: {media_retweets}")

# Show collection state
state = db.collection_state.find_one({"_id": "global"})
if state and "last_collection_time" in state:
    print(f"\n⏰ Last collection: {state['last_collection_time']}")

print("\n" + "=" * 60)
print("SUMMARY:")
if enhanced > 0:
    print("✅ Enhanced retweet collection is ACTIVE")
    print(f"   {enhanced}/{retweets} retweets have full text ({enhanced*100//retweets if retweets else 0}%)")
else:
    print("⚠️  Enhanced retweet collection NOT YET ACTIVE")
    print("   The enhanced collector is running but hasn't collected new retweets yet")
    print("   It will fetch full text for new retweets once rate limits clear")
print("=" * 60)