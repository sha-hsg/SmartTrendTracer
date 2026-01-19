#!/usr/bin/env python
"""Fix broken image references in preview and summary fields"""

from pymongo import MongoClient
import re

# MongoDB connection
client = MongoClient()
db = client.smarttrendtracer

# The problematic image ID
image_id = "7596f5ed-8d5b-4aca-be4b-cdd23f324820"

# Get all articles
articles = list(db.articles.find({}))

print(f"Checking {len(articles)} articles for broken image in preview/summary fields...")

articles_to_fix = []

for article in articles:
    needs_fix = False
    fields_with_image = []
    
    # Check all text fields
    for field in ['preview', 'summary', 'content', 'content_markdown']:
        if field in article and article[field]:
            if image_id in str(article[field]):
                needs_fix = True
                fields_with_image.append(field)
    
    if needs_fix:
        articles_to_fix.append((article, fields_with_image))

print(f"\nFound {len(articles_to_fix)} articles with the broken image")

# Patterns to remove
patterns = [
    # HTML img tags
    rf'<img[^>]*src="[^"]*{image_id}[^"]*"[^>]*>',
    # Markdown images
    rf'!\[[^\]]*\]\([^)]*{image_id}[^)]*\)',
    # URLs in HTML  
    rf'https://substackcdn\.com/image/fetch/[^/\s\)"\']+/https%3A%2F%2Fsubstack-post-media\.s3\.amazonaws\.com%2Fpublic%2Fimages%2F{image_id}[^\s\)"\']*',
    # Direct S3 URLs
    rf'https://substack-post-media\.s3\.amazonaws\.com/public/images/{image_id}[^\s\)"\']*',
    # Encoded URLs
    rf'https%3A%2F%2Fsubstack-post-media\.s3\.amazonaws\.com%2Fpublic%2Fimages%2F{image_id}[^\s\)"\']*'
]

# Fix each article
for article, fields in articles_to_fix:
    print(f"\nFixing: {article.get('title', 'Unknown')[:50]}")
    print(f"  Fields with broken image: {fields}")
    
    updates = {}
    
    for field in fields:
        if field in article and article[field]:
            content = article[field]
            original_length = len(content)
            
            # Remove all patterns
            for pattern in patterns:
                content = re.sub(pattern, '', content, flags=re.IGNORECASE)
            
            # Clean up any double spaces or empty lines left behind
            content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
            content = re.sub(r'  +', ' ', content)
            
            if len(content) != original_length:
                updates[field] = content
                print(f"  ✓ Cleaned {field} (removed {original_length - len(content)} chars)")
    
    # Update the article
    if updates:
        result = db.articles.update_one(
            {'_id': article['_id']},
            {'$set': updates}
        )
        print(f"  ✅ Updated: {result.modified_count} document modified")
    else:
        print(f"  ⚠️  No changes needed")

print(f"\n{'='*60}")
print(f"Completed! Fixed {len(articles_to_fix)} articles")

# Verify the fix
print("\nVerifying...")
remaining = 0
for article in db.articles.find({}):
    for field in ['preview', 'summary', 'content', 'content_markdown']:
        if field in article and article[field] and image_id in str(article[field]):
            remaining += 1
            print(f"  ⚠️ Still found in {article.get('title', 'Unknown')[:30]} - {field}")
            break

if remaining == 0:
    print("✅ All broken image references have been removed!")
else:
    print(f"⚠️  {remaining} articles still have the broken image reference")