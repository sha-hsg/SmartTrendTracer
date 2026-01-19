#!/usr/bin/env python
"""Update preview fields to use local images"""

from pymongo import MongoClient
import re

# MongoDB connection
client = MongoClient()
db = client.smarttrendtracer

print("Updating preview fields to use local images...")

# Get all articles with images field
articles = list(db.articles.find({'images': {'$exists': True}}, {'title': 1, 'preview': 1, 'images': 1}))

updated_count = 0

for article in articles:
    preview = article.get('preview', '')
    if not preview:
        continue
    
    # Check if preview has CDN images
    if 'substackcdn.com' not in preview and 's3.amazonaws.com' not in preview:
        continue
    
    print(f"\nUpdating: {article.get('title', 'Unknown')[:50]}")
    
    updated_preview = preview
    images_map = {}
    
    # Build a map of original URLs to local URLs
    for img in article.get('images', []):
        if 'original_url' in img and 'local_url' in img:
            images_map[img['original_url']] = img['local_url']
        if 'real_url' in img and 'local_url' in img:
            images_map[img['real_url']] = img['local_url']
    
    # Find all image URLs in the preview
    # Pattern for both CDN and S3 URLs
    patterns = [
        r'https://substackcdn\.com/image/fetch/[^\s\)\'"]+',
        r'https://[^/]+\.s3\.amazonaws\.com/[^\s\)\'"]+',
        r'https%3A%2F%2F[^/]+\.s3\.amazonaws\.com[^\s\)\'"]+',
    ]
    
    replacements_made = 0
    
    for pattern in patterns:
        urls = re.findall(pattern, updated_preview)
        for url in urls:
            # Try to find a matching local URL
            local_url = None
            
            # Check if this URL is in our map
            for orig_url, local in images_map.items():
                # Check if the URL contains part of the original URL (for CDN wrapped URLs)
                if url in orig_url or orig_url in url:
                    local_url = local
                    break
                
                # Check for image ID match
                # Extract image ID from both URLs
                id_pattern = r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})'
                url_ids = re.findall(id_pattern, url)
                orig_ids = re.findall(id_pattern, orig_url)
                
                if url_ids and orig_ids and url_ids[0] == orig_ids[0]:
                    local_url = local
                    break
            
            if local_url:
                updated_preview = updated_preview.replace(url, local_url)
                replacements_made += 1
                print(f"  ✓ Replaced CDN URL with {local_url}")
            else:
                # If no local URL found, try to extract image ID and find it
                image_ids = re.findall(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', url)
                if image_ids:
                    for img in article.get('images', []):
                        if image_ids[0] in img.get('original_url', '') or image_ids[0] in img.get('real_url', ''):
                            updated_preview = updated_preview.replace(url, img['local_url'])
                            replacements_made += 1
                            print(f"  ✓ Found by ID and replaced with {img['local_url']}")
                            break
    
    # Update the article if changes were made
    if replacements_made > 0:
        result = db.articles.update_one(
            {'_id': article['_id']},
            {'$set': {'preview': updated_preview}}
        )
        if result.modified_count > 0:
            updated_count += 1
            print(f"  ✅ Updated preview with {replacements_made} local image URLs")
    else:
        print(f"  ⚠️  No matching local images found for CDN URLs")

print(f"\n{'='*60}")
print(f"Updated {updated_count} articles with local images in preview")

# Verify
articles = list(db.articles.find({}, {'preview': 1}))
cdn_count = 0
local_count = 0

for article in articles:
    preview = article.get('preview', '')
    if 'substackcdn.com' in preview or 's3.amazonaws.com' in preview:
        cdn_count += 1
    if '/api/articles/' in preview:
        local_count += 1

print(f"\nVerification:")
print(f"  Articles with CDN images in preview: {cdn_count}")
print(f"  Articles with local images in preview: {local_count}")