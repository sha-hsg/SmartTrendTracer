#!/usr/bin/env python
"""Check for any remaining CDN images in previews"""

from pymongo import MongoClient
import re

# MongoDB connection
client = MongoClient()
db = client.smarttrendtracer

articles = list(db.articles.find({}, {'title': 1, 'preview': 1}))

print(f"Checking {len(articles)} articles for CDN images in preview field...")

articles_with_cdn = []

for article in articles:
    preview = article.get('preview', '')
    if preview and re.search(r'substackcdn\.com/image/fetch', preview):
        # Extract the CDN URLs
        cdn_urls = re.findall(r'https://substackcdn[^)\s"\']+', preview)
        articles_with_cdn.append((article, cdn_urls))

if articles_with_cdn:
    print(f"\n⚠️  Found {len(articles_with_cdn)} articles with CDN images in preview:")
    for art, urls in articles_with_cdn[:5]:  # Show first 5
        print(f"\n  Article: {art.get('title', 'Unknown')[:50]}")
        for url in urls[:2]:  # Show first 2 URLs
            print(f"    - {url[:80]}...")
else:
    print("\n✅ No CDN images found in preview fields!")

# Also check for local images to confirm they were replaced
local_count = 0
for article in articles:
    preview = article.get('preview', '')
    if preview and '/api/articles/' in preview:
        local_count += 1

print(f"\n✅ {local_count} articles have local image paths in their previews")