#!/usr/bin/env python
"""Fix images for a single article"""

from fix_and_localize_article_images import process_article
from pymongo import MongoClient
from bson import ObjectId

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client.smarttrendtracer

# Get The Illustrated GPT-OSS article
article_id = "68ad9b073bc929e6a5c35253"
article = db.articles.find_one({'_id': ObjectId(article_id)})

if article:
    print(f"Processing: {article.get('title')}")
    success = process_article(article)
    if success:
        print("✅ Successfully processed!")
    else:
        print("❌ No images found or processing failed")
else:
    print(f"Article {article_id} not found")