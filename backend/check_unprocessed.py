#!/usr/bin/env python
"""Check which article hasn't been processed"""

from pymongo import MongoClient

# MongoDB connection
client = MongoClient()
db = client.smarttrendtracer

# Find articles without images
articles = list(db.articles.find({}, {'title': 1, 'url': 1, '_id': 1, 'images': 1}))

without_images = []
for art in articles:
    if 'images' not in art or not art.get('images'):
        without_images.append(art)

print(f"Total articles: {len(articles)}")
print(f"Articles without images: {len(without_images)}")
print()

for art in without_images:
    print(f"Title: {art.get('title', 'Unknown')}")
    print(f"ID: {art.get('_id')}")
    print(f"URL: {art.get('url', 'No URL')}")
    print()