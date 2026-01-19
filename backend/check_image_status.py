#!/usr/bin/env python
"""Check image processing status for articles"""

from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient()
db = client.smarttrendtracer

# Check articles with GPT in title
articles = list(db.articles.find({'title': {'$regex': 'GPT', '$options': 'i'}}, {'title': 1, 'images': 1}))

print(f"Articles with 'GPT' in title: {len(articles)}")
for article in articles[:5]:
    has_images = 'images' in article and article['images']
    image_count = len(article['images']) if has_images else 0
    print(f"  - {article.get('title', 'Unknown')[:50]} - Images: {image_count}")

# Count total articles processed
total = db.articles.count_documents({})
processed = db.articles.count_documents({'images': {'$exists': True}})
print(f"\nTotal articles: {total}")
print(f"Articles with images field: {processed}")

# Check specific article
illustrated = db.articles.find_one({'url': 'https://newsletter.languagemodels.co/p/the-illustrated-gpt-oss'})
if illustrated:
    print(f"\n'The Illustrated GPT-OSS' article:")
    print(f"  - Has images field: {'images' in illustrated}")
    if 'images' in illustrated:
        print(f"  - Number of images: {len(illustrated['images'])}")