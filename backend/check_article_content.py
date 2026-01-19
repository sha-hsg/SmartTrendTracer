#!/usr/bin/env python
"""Check article content for images"""

from pymongo import MongoClient
from bson import ObjectId
import re

# MongoDB connection
client = MongoClient()
db = client.smarttrendtracer

# Check The Illustrated GPT-OSS
article = db.articles.find_one({'_id': ObjectId('68ad9b073bc929e6a5c35253')})

if article:
    print(f"Title: {article.get('title')}")
    print(f"URL: {article.get('url')}")
    
    content = article.get('content_markdown', '') or article.get('content', '')
    print(f"\nContent length: {len(content)} chars")
    print(f"First 500 chars of content:\n{content[:500]}")
    
    # Look for any image patterns
    patterns = [
        r'https?://[^\s\)]+\.(jpg|jpeg|png|gif|webp|svg)',
        r'https?://[^\s\)]+substackcdn[^\s\)]*',
        r'https?://[^\s\)]+\.s3\.amazonaws[^\s\)]*',
        r'!\[.*?\]\(.*?\)'
    ]
    
    for pattern_name, pattern in zip(['Direct images', 'Substack CDN', 'S3 URLs', 'Markdown images'], patterns):
        matches = re.findall(pattern, content, re.IGNORECASE)
        print(f"\n{pattern_name}: {len(matches)}")
        for match in matches[:2]:
            print(f"  - {str(match)[:100]}")