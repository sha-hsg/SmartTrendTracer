#!/usr/bin/env python
"""Find which article contains a specific image ID"""

from pymongo import MongoClient

# MongoDB connection
client = MongoClient()
db = client.smarttrendtracer

# Image ID to search for
image_id = "7596f5ed-8d5b-4aca-be4b-cdd23f324820"

# Search all articles
articles = db.articles.find({}, {'title': 1, 'content': 1, 'content_markdown': 1, 'images': 1, '_id': 1})

found_articles = []

for article in articles:
    # Check in content fields
    content = str(article.get('content', '')) + str(article.get('content_markdown', ''))
    
    if image_id in content:
        found_articles.append(article)

print(f"Found {len(found_articles)} articles containing image {image_id}")

for art in found_articles:
    print(f"\nArticle: {art.get('title')}")
    print(f"ID: {art.get('_id')}")
    print(f"Has images field: {'images' in art and art['images']}")
    
    # Check if this image is in the processed images
    if 'images' in art:
        for img in art['images']:
            if image_id in img.get('original_url', '') or image_id in img.get('real_url', ''):
                print(f"  ✓ Image was processed: {img.get('local_url')}")
                break
        else:
            print(f"  ✗ Image {image_id} not in processed images list")
    
    # Check if it's still in the content
    if image_id in str(article.get('content_markdown', '')):
        print(f"  ⚠️ Image still in content_markdown")
    if image_id in str(article.get('content', '')):
        print(f"  ⚠️ Image still in content HTML")