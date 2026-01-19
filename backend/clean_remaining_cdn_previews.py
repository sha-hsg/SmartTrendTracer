#!/usr/bin/env python
"""Remove remaining CDN URLs from preview fields that can't be replaced"""

from pymongo import MongoClient
import re

# MongoDB connection
client = MongoClient()
db = client.smarttrendtracer

print("Cleaning remaining CDN URLs from preview fields...")

# Get all articles
articles = list(db.articles.find({}, {'title': 1, 'preview': 1}))

cleaned_count = 0

for article in articles:
    preview = article.get('preview', '')
    if not preview:
        continue
    
    # Check if preview has CDN/S3 images
    if 'substackcdn.com' not in preview and 's3.amazonaws.com' not in preview:
        continue
    
    original_preview = preview
    
    # Patterns to remove - these are likely profile images or unavailable images
    patterns = [
        # Remove entire img tags with CDN URLs
        r'<img[^>]*src="[^"]*substackcdn\.com[^"]*"[^>]*>',
        r'<img[^>]*src="[^"]*s3\.amazonaws\.com[^"]*"[^>]*>',
        # Remove markdown images with CDN URLs  
        r'!\[[^\]]*\]\([^)]*substackcdn\.com[^)]*\)',
        r'!\[[^\]]*\]\([^)]*s3\.amazonaws\.com[^)]*\)',
        # Remove bare CDN URLs
        r'https://substackcdn\.com/image/fetch/[^\s\)\'"<]+',
        r'https://[^/]+\.s3\.amazonaws\.com/[^\s\)\'"<]+',
        # Remove profile/avatar images specifically
        r'<img[^>]*alt="[^"]*profile[^"]*"[^>]*>',
        r'<img[^>]*alt="[^"]*avatar[^"]*"[^>]*>',
        r'<img[^>]*class="[^"]*avatar[^"]*"[^>]*>',
        r'<img[^>]*class="[^"]*profile[^"]*"[^>]*>',
    ]
    
    for pattern in patterns:
        preview = re.sub(pattern, '', preview, flags=re.IGNORECASE)
    
    # Clean up any double spaces or empty lines
    preview = re.sub(r'\n\s*\n\s*\n', '\n\n', preview)
    preview = re.sub(r'  +', ' ', preview)
    preview = preview.strip()
    
    # Only update if we made changes
    if preview != original_preview:
        print(f"\nCleaning: {article.get('title', 'Unknown')[:50]}")
        
        result = db.articles.update_one(
            {'_id': article['_id']},
            {'$set': {'preview': preview}}
        )
        
        if result.modified_count > 0:
            cleaned_count += 1
            print(f"  ✅ Removed CDN URLs from preview")

print(f"\n{'='*60}")
print(f"Cleaned {cleaned_count} articles")

# Final verification
articles = list(db.articles.find({}, {'preview': 1}))
cdn_count = 0
local_count = 0

for article in articles:
    preview = article.get('preview', '')
    if 'substackcdn.com' in preview or 's3.amazonaws.com' in preview:
        cdn_count += 1
    if '/api/articles/' in preview:
        local_count += 1

print(f"\nFinal Status:")
print(f"  Articles with CDN images: {cdn_count}")
print(f"  Articles with local images: {local_count}")

if cdn_count == 0:
    print("\n✅ All CDN URLs have been removed from preview fields!")
else:
    print(f"\n⚠️  {cdn_count} articles still have CDN URLs (checking what they are...)")
    
    # Show what's left
    for article in db.articles.find({}, {'title': 1, 'preview': 1}):
        preview = article.get('preview', '')
        if 'substackcdn.com' in preview or 's3.amazonaws.com' in preview:
            urls = re.findall(r'https://[^\s\)\'"<]+', preview)
            cdn_urls = [u for u in urls if 'substackcdn' in u or 's3.amazonaws' in u]
            if cdn_urls:
                print(f"\n  {article.get('title', 'Unknown')[:40]}:")
                for url in cdn_urls[:2]:
                    print(f"    - {url[:80]}...")
                break  # Just show one example