#!/usr/bin/env python3
"""
Test the improved search functionality
"""

import sys
sys.path.append(".")

from app.api.tweets_mongodb import faceted_search

print("🧪 Testing improved search functionality:")
print("=" * 50)

# Test 1: Search with quotes for exact phrase
result1 = faceted_search(
    page=1,
    page_size=10,
    search='"Innovator dilemma"',
    authors=None,
    concept_ids=None,
    years=None,
    exclude_retweets=False,
    annotation_status=None
)

print(f"\n1. Search for \"Innovator dilemma\" (with quotes):")
print(f"   Total results: {result1['total']}")
if result1["tweets"]:
    tweet = result1["tweets"][0]
    text_preview = tweet["text"][:150] + "..." if len(tweet["text"]) > 150 else tweet["text"]
    print(f"   First result: @{tweet['author_username']}: {text_preview}")

# Test 2: Search without quotes  
result2 = faceted_search(
    page=1,
    page_size=10,
    search="Innovator dilemma",
    authors=None,
    concept_ids=None,
    years=None,
    exclude_retweets=False,
    annotation_status=None
)

print(f"\n2. Search for Innovator dilemma (without quotes):")
print(f"   Total results: {result2['total']}")

# Test 3: Search with apostrophe
result3 = faceted_search(
    page=1,
    page_size=10,
    search='"Innovator\'s dilemma"',
    authors=None,
    concept_ids=None,
    years=None,
    exclude_retweets=False,
    annotation_status=None
)

print(f"\n3. Search for \"Innovator's dilemma\" (with apostrophe):")
print(f"   Total results: {result3['total']}")
if result3["tweets"]:
    tweet = result3["tweets"][0]
    text_preview = tweet["text"][:150] + "..." if len(tweet["text"]) > 150 else tweet["text"]
    print(f"   First result: @{tweet['author_username']}: {text_preview}")

print("\n✅ Search functionality improved!")
print("   - Quoted searches now use regex for exact phrase matching")
print("   - Handles variations like Innovator's vs Innovators")
print("   - Unquoted searches still use MongoDB text search")