#!/usr/bin/env python3
"""
Monitor for enhanced retweet collection
"""

from pymongo import MongoClient
from datetime import datetime, timedelta
import time
import sys

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client.smarttrendtracer

print("=" * 60)
print("MONITORING ENHANCED RETWEET COLLECTION")
print("=" * 60)
print("Watching for new retweets with full_text field...")
print("Press Ctrl+C to stop\n")

# Track initial state
initial_enhanced = db.tweets.count_documents({"full_text": {"$exists": True}})
initial_retweets = db.tweets.count_documents({"text": {"$regex": "^RT @"}})

print(f"Starting state:")
print(f"  - Total retweets: {initial_retweets}")
print(f"  - Enhanced retweets: {initial_enhanced}")
print(f"  - Rate limit clears at: ~22:17:52")
print("\nWaiting for new enhanced retweets...\n")

try:
    while True:
        # Check for new enhanced retweets
        current_enhanced = db.tweets.count_documents({"full_text": {"$exists": True}})
        current_retweets = db.tweets.count_documents({"text": {"$regex": "^RT @"}})
        
        if current_enhanced > initial_enhanced:
            print(f"\n✅ ENHANCED COLLECTION ACTIVE!")
            print(f"  New enhanced retweets: {current_enhanced - initial_enhanced}")
            
            # Show a sample
            sample = db.tweets.find_one(
                {"full_text": {"$exists": True}},
                sort=[("created_at", -1)]
            )
            if sample:
                print(f"\n  Sample enhanced retweet:")
                print(f"    Author: @{sample.get('author_username')}")
                print(f"    Truncated: {sample.get('text', '')[:80]}...")
                print(f"    Full text: {sample.get('full_text', '')[:150]}...")
                if sample.get('original_media'):
                    print(f"    Original media: {len(sample['original_media'])} items")
            break
        
        # Show progress dot
        sys.stdout.write(".")
        sys.stdout.flush()
        
        # Check every 30 seconds
        time.sleep(30)
        
except KeyboardInterrupt:
    print("\n\nMonitoring stopped by user")
    
finally:
    # Final status
    final_enhanced = db.tweets.count_documents({"full_text": {"$exists": True}})
    final_retweets = db.tweets.count_documents({"text": {"$regex": "^RT @"}})
    
    print("\n" + "=" * 60)
    print("FINAL STATUS:")
    print(f"  Total retweets: {final_retweets} (+{final_retweets - initial_retweets})")
    print(f"  Enhanced retweets: {final_enhanced} (+{final_enhanced - initial_enhanced})")
    if final_enhanced > 0:
        print(f"  Coverage: {final_enhanced*100//final_retweets}% of retweets have full text")
    print("=" * 60)