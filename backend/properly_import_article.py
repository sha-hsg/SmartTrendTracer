#!/usr/bin/env python
"""Properly re-import The Illustrated GPT-OSS article"""

import requests
from bs4 import BeautifulSoup
import html2text
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

# MongoDB connection
client = MongoClient()
db = client.smarttrendtracer

# Fetch the article
url = "https://newsletter.languagemodels.co/p/the-illustrated-gpt-oss"
print(f"Fetching: {url}")

response = requests.get(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find the article content
    article_div = soup.find('div', class_='available-content')
    if not article_div:
        article_div = soup.find('article')
    if not article_div:
        article_div = soup.find('div', class_='post-content')
    
    if article_div:
        # Convert to markdown
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.body_width = 0
        markdown_content = h.handle(str(article_div))
        
        print(f"Content length: {len(markdown_content)} chars")
        print(f"First 500 chars:\n{markdown_content[:500]}")
        
        # Count images
        import re
        images = re.findall(r'https?://[^\s\)]+', markdown_content)
        print(f"\nFound {len(images)} URLs in content")
        
        # Update the article
        result = db.articles.update_one(
            {'_id': ObjectId('68ad9b073bc929e6a5c35253')},
            {'$set': {
                'content': str(article_div),
                'content_markdown': markdown_content,
                'word_count': len(markdown_content.split()),
                'updated_at': datetime.utcnow()
            }}
        )
        
        print(f"\n✅ Updated article: {result.modified_count} document modified")
    else:
        print("❌ Could not find article content in HTML")
else:
    print(f"❌ Failed to fetch: {response.status_code}")