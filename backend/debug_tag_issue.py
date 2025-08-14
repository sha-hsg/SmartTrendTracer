#!/usr/bin/env python3
"""Debug why tags aren't matching in the API"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import SessionLocal, Tweet, Tag
from sqlalchemy.orm import joinedload
from sqlalchemy import text

db = SessionLocal()

# Test a specific problematic tag
test_tag = "3D interface generation"

print(f"Debugging tag: '{test_tag}'")
print("="*50)

# 1. Check raw SQL
print("\n1. Raw SQL query:")
sql = text("""
    SELECT DISTINCT t.id, t.author_username, SUBSTR(t.text, 1, 50)
    FROM tweets t
    JOIN tags tg ON t.id = tg.tweet_id
    WHERE tg.tag = :tag
    LIMIT 3
""")
results = db.execute(sql, {"tag": test_tag}).fetchall()
print(f"   Found {len(results)} tweets")
for row in results:
    print(f"   - {row[1]}: {row[2]}...")

# 2. Check ORM query (what the API uses)
print("\n2. ORM query (API style):")
query = db.query(Tweet).options(
    joinedload(Tweet.media),
    joinedload(Tweet.tags)
)
query = query.join(Tag).filter(Tag.tag == test_tag).distinct()
tweets = query.limit(3).all()
print(f"   Found {len(tweets)} tweets")
for tweet in tweets:
    print(f"   - {tweet.author_username}: {tweet.text[:50]}...")

# 3. Check if there's a relationship issue
print("\n3. Check Tweet.tags relationship:")
# Get the tweet directly
tweet_with_tag = db.query(Tweet).join(Tag).filter(Tag.tag == test_tag).first()
if tweet_with_tag:
    print(f"   Tweet ID: {tweet_with_tag.id}")
    print(f"   Has tags attribute: {hasattr(tweet_with_tag, 'tags')}")
    if hasattr(tweet_with_tag, 'tags'):
        print(f"   Number of tags: {len(tweet_with_tag.tags)}")
        for tag in tweet_with_tag.tags:
            print(f"     - {tag.tag}")

# 4. Check for any hidden characters in tags
print("\n4. Check for hidden characters:")
tags_like = db.query(Tag).filter(Tag.tag.like(f"%{test_tag.split()[0]}%")).limit(5).all()
for tag in tags_like:
    print(f"   Tag: '{tag.tag}' (len={len(tag.tag)}, bytes={tag.tag.encode('utf-8')})")

db.close()