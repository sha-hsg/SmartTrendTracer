#!/usr/bin/env python3
"""
Test script to investigate the search issue with "Innovator's dilemma"
"""

from pymongo import MongoClient
import json
import re

client = MongoClient("mongodb://localhost:27017/")
db = client.smarttrendtracer

print("🔍 Investigating search issue for 'Innovator's dilemma'")
print("=" * 60)

# Check for indexes on tweets collection
print("\n1. Checking indexes on tweets collection:")
indexes = list(db.tweets.list_indexes())
has_text_index = False
for idx in indexes:
    index_keys = list(idx["key"].keys())
    print(f"  - {idx['name']}: {index_keys}")
    if "text" in str(idx["key"]) or "_fts" in idx["name"]:
        has_text_index = True
        print(f"    ✅ Text index found!")

if not has_text_index:
    print("  ⚠️  No text index found - this is likely the issue!")

# Test different search approaches
print("\n2. Testing different search methods:")

# Test 1: Current implementation - MongoDB text search
try:
    result1 = list(db.tweets.find({"$text": {"$search": "Innovator dilemma"}}).limit(3))
    print(f"  a) Text search for 'Innovator dilemma': {len(result1)} results")
except Exception as e:
    print(f"  a) Text search failed: {e}")

# Test 2: Text search with quotes
try:
    result2 = list(db.tweets.find({"$text": {"$search": '"Innovator dilemma"'}}).limit(3))
    print(f"  b) Text search with quotes: {len(result2)} results")
except Exception as e:
    print(f"  b) Quoted text search failed: {e}")

# Test 3: Regex search (case insensitive)
regex_pattern = re.compile(r"innovator.*dilemma", re.IGNORECASE)
result3 = list(db.tweets.find({"text": regex_pattern}).limit(5))
print(f"  c) Regex search (case insensitive): {len(result3)} results")

# Test 4: Simple substring search
result4 = list(db.tweets.find({"text": {"$regex": "Innovator", "$options": "i"}}).limit(5))
print(f"  d) Simple substring search for 'Innovator': {len(result4)} results")

# Check the specific tweet we know has it
print("\n3. Checking specific tweet 1948585378991976525:")
specific_tweet = db.tweets.find_one({"_id": "1948585378991976525"})
if specific_tweet:
    text = specific_tweet.get("text", "")
    print(f"  ✅ Tweet found")
    print(f"  - Contains 'Innovator': {'Innovator' in text}")
    print(f"  - Contains 'dilemma': {'dilemma' in text}")
    print(f"  - Text preview: {text[:150]}...")
else:
    print(f"  ❌ Tweet not found")

# Show sample results from regex search
if result3:
    print("\n4. Sample tweets found with regex search:")
    for i, tweet in enumerate(result3[:2], 1):
        text = tweet.get("text", "")
        # Highlight the matched text
        highlighted = re.sub(r"(innovator.*?dilemma)", r"**\1**", text, flags=re.IGNORECASE)
        preview = highlighted[:200] + "..." if len(highlighted) > 200 else highlighted
        print(f"  {i}. @{tweet.get('author_username', 'unknown')}: {preview}")

# Recommendation
print("\n5. RECOMMENDATION:")
if not has_text_index:
    print("  🔧 Create a text index: db.tweets.createIndex({text: 'text'})")
    print("  OR")
print("  🔧 Use regex search for more flexible matching")
print("  🔧 The current $text search may not handle possessives (Innovator's) well")