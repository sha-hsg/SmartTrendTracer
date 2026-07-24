#!/usr/bin/env python
"""Fix the specific CDN image that's still causing 404 errors"""

import requests
import hashlib
from pathlib import Path
from pymongo import MongoClient
from bson import ObjectId
import re

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client.smarttrendtracer

# The problematic image
cdn_url = "https://substackcdn.com/image/fetch/w_1100,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F7596f5ed-8d5b-4aca-be4b-cdd23f324820_1100x220.png"
s3_url = "https://substack-post-media.s3.amazonaws.com/public/images/7596f5ed-8d5b-4aca-be4b-cdd23f324820_1100x220.png"
image_id = "7596f5ed-8d5b-4aca-be4b-cdd23f324820"

# Local image storage directory
IMAGE_DIR = Path("data/article_images")
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

# Find all articles with this image
articles = db.articles.find({}, {'_id': 1, 'title': 1, 'content': 1, 'content_markdown': 1, 'images': 1})

articles_to_fix = []
for article in articles:
    content = str(article.get('content', '')) + str(article.get('content_markdown', ''))
    if image_id in content:
        articles_to_fix.append(article)

print(f"Found {len(articles_to_fix)} articles with image {image_id}")

# Download the image once
filename = f"shared_{image_id}.png"
filepath = IMAGE_DIR / filename

if not filepath.exists():
    print(f"Trying CDN URL first...")
    downloaded = False
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(cdn_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        print(f"✅ Downloaded from CDN to {filename}")
        downloaded = True
    except Exception as e:
        print(f"❌ CDN failed: {e}")
    
    if not downloaded:
        print(f"Trying S3 URL...")
        try:
            response = requests.get(s3_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            print(f"✅ Downloaded from S3 to {filename}")
        except Exception as e:
            print(f"❌ S3 also failed: {e}")
            print("This image is no longer accessible. Will remove references.")
            # Don't process articles if we can't download the image
            
else:
    print(f"✅ Image already exists: {filename}")

# Only process if we have the image
if not filepath.exists():
    print("\n⚠️  Cannot fix articles - image is not accessible")
    print("Will remove broken references from content")
    
    # Remove broken image references from all articles
    for article in articles_to_fix:
        article_id = str(article['_id'])
        print(f"\nRemoving from: {article.get('title', 'Unknown')[:50]}")
        
        updates = {}
        
        # Patterns to remove
        patterns = [
            # Image tags with this URL
            rf'<img[^>]*src="[^"]*{image_id}[^"]*"[^>]*>',
            # Markdown images
            rf'!\[[^\]]*\]\([^)]*{image_id}[^)]*\)',
            # Just the URLs themselves
            rf'https://substackcdn\.com/image/fetch/[^/\s\)]+/https%3A%2F%2Fsubstack-post-media\.s3\.amazonaws\.com%2Fpublic%2Fimages%2F{image_id}[^\s\)]*',
            rf'https://substack-post-media\.s3\.amazonaws\.com/public/images/{image_id}[^\s\)]*'
        ]
        
        if article.get('content'):
            content = article['content']
            for pattern in patterns:
                content = re.sub(pattern, '', content)
            updates['content'] = content
        
        if article.get('content_markdown'):
            content_md = article['content_markdown']
            for pattern in patterns:
                content_md = re.sub(pattern, '', content_md)
            updates['content_markdown'] = content_md
        
        # Update the article
        if updates:
            result = db.articles.update_one(
                {'_id': article['_id']},
                {'$set': updates}
            )
            print(f"  ✅ Removed references: {result.modified_count} document modified")
    
    print(f"\n{'='*60}")
    print(f"Removed broken image references from {len(articles_to_fix)} articles")
    exit(0)

# Fix each article with the downloaded image
for article in articles_to_fix:
    article_id = str(article['_id'])
    print(f"\nFixing: {article.get('title', 'Unknown')[:50]}")
    
    # Create local URL
    local_url = f"/api/articles/{article_id}/images/{filename}"
    
    # Update content to replace all variants of this image URL
    updates = {}
    
    # Patterns to replace
    patterns = [
        # Full CDN URLs with any parameters
        rf'https://substackcdn\.com/image/fetch/[^/\s\)]+/https%3A%2F%2Fsubstack-post-media\.s3\.amazonaws\.com%2Fpublic%2Fimages%2F{image_id}[^\s\)]*',
        # Direct S3 URLs
        rf'https://substack-post-media\.s3\.amazonaws\.com/public/images/{image_id}[^\s\)]*',
        # Encoded versions
        rf'https%3A%2F%2Fsubstack-post-media\.s3\.amazonaws\.com%2Fpublic%2Fimages%2F{image_id}[^\s\)]*'
    ]
    
    if article.get('content'):
        content = article['content']
        for pattern in patterns:
            content = re.sub(pattern, local_url, content)
        updates['content'] = content
    
    if article.get('content_markdown'):
        content_md = article['content_markdown']
        for pattern in patterns:
            content_md = re.sub(pattern, local_url, content_md)
        updates['content_markdown'] = content_md
    
    # Add to images metadata if not already there
    images = article.get('images', [])
    if not any(image_id in img.get('original_url', '') for img in images):
        images.append({
            'original_url': cdn_url,
            'real_url': s3_url,
            'local_path': str(filepath),
            'local_url': local_url,
            'filename': filename,
            'size': filepath.stat().st_size
        })
        updates['images'] = images
    
    # Update the article
    if updates:
        result = db.articles.update_one(
            {'_id': article['_id']},
            {'$set': updates}
        )
        print(f"  ✅ Updated: {result.modified_count} document modified")

print(f"\n{'='*60}")
print(f"Fixed {len(articles_to_fix)} articles with the problematic image")