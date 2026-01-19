#!/usr/bin/env python
"""Check final status of image processing"""

from pymongo import MongoClient

# MongoDB connection
client = MongoClient()
db = client.smarttrendtracer

# Get all articles
all_articles = list(db.articles.find({}, {'title': 1, 'images': 1, 'url': 1}))

print(f"Total articles: {len(all_articles)}")

with_images = []
without_images = []

for article in all_articles:
    if 'images' in article and article['images']:
        with_images.append(article)
    else:
        without_images.append(article)

print(f"Articles with local images: {len(with_images)}")
print(f"Articles without images: {len(without_images)}")

if with_images:
    print("\nArticles with images:")
    for art in with_images[:5]:
        print(f"  - {art.get('title', 'Unknown')[:50]} ({len(art['images'])} images)")

if without_images and len(without_images) <= 10:
    print("\nArticles still needing processing:")
    for art in without_images:
        print(f"  - {art.get('title', 'Unknown')[:50]}")

print(f"\n{'='*60}")
print(f"Processing status: {'✅ COMPLETE' if len(without_images) == 0 else f'⚠️  {len(without_images)} articles need processing'}")