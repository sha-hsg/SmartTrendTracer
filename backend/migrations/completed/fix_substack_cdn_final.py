"""
Final fix for Substack CDN image URLs
Handles special characters in URLs
"""

from pymongo import MongoClient
import re
import urllib.parse

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client.smarttrendtracer

def extract_real_url_from_cdn(cdn_url):
    """
    Extract the actual S3 URL from the Substack CDN wrapper
    Handles URLs with special tokens like $s_!naQx!
    """
    # Look for the encoded URL part (starts with http)
    match = re.search(r'(https?%3A%2F%2F[^)]+)', cdn_url)
    if match:
        encoded_url = match.group(1)
        # Decode the URL
        decoded_url = urllib.parse.unquote(encoded_url)
        return decoded_url
    
    return cdn_url

def fix_article_images(article):
    """Fix all CDN URLs in an article"""
    
    updated = False
    
    # Fix content_markdown
    if article.get('content_markdown'):
        content = article['content_markdown']
        
        # Find all substackcdn URLs
        cdn_pattern = r'https://substackcdn\.com/image/fetch/[^)]+(?:\)|$)'
        
        def replace_cdn_url(match):
            cdn_url = match.group(0)
            real_url = extract_real_url_from_cdn(cdn_url)
            if real_url != cdn_url:
                print(f"  Replacing CDN URL with: {real_url[:80]}...")
                return real_url
            return cdn_url
        
        new_content = re.sub(cdn_pattern, replace_cdn_url, content)
        
        if new_content != content:
            updated = True
            article['content_markdown'] = new_content
    
    # Fix content field too if present
    if article.get('content'):
        content = article['content']
        
        def replace_cdn_url(match):
            cdn_url = match.group(0)
            real_url = extract_real_url_from_cdn(cdn_url)
            if real_url != cdn_url:
                return real_url
            return cdn_url
        
        new_content = re.sub(cdn_pattern, replace_cdn_url, content)
        
        if new_content != content:
            updated = True
            article['content'] = new_content
    
    return updated

def main():
    # Find all articles with CDN URLs
    query = {
        '$or': [
            {'content': {'$regex': 'substackcdn\\.com/image/fetch'}},
            {'content_markdown': {'$regex': 'substackcdn\\.com/image/fetch'}}
        ]
    }
    
    articles = list(db.articles.find(query))
    print(f"Found {len(articles)} articles with Substack CDN URLs")
    
    fixed_count = 0
    
    for article in articles:
        print(f"\nProcessing: {article.get('title', 'Untitled')[:60]}...")
        
        if fix_article_images(article):
            # Update the article
            db.articles.update_one(
                {'_id': article['_id']},
                {'$set': {
                    'content': article.get('content'),
                    'content_markdown': article.get('content_markdown')
                }}
            )
            fixed_count += 1
            print("  ✅ Article updated")
    
    print(f"\n{'='*60}")
    print(f"Fixed {fixed_count} articles")
    
    # Verify
    remaining = db.articles.count_documents(query)
    if remaining > 0:
        print(f"WARNING: {remaining} articles still contain CDN URLs")
    else:
        print("✅ All Substack CDN URLs have been fixed!")

if __name__ == '__main__':
    main()