"""
Fix double-encoded image URLs in existing articles
"""

from pymongo import MongoClient
import urllib.parse
import re

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client.smarttrendtracer

def fix_image_url(url):
    """Decode double-encoded URLs"""
    if '%' in url:
        try:
            decoded = urllib.parse.unquote(url)
            # Check if it was double-encoded
            if '%' in decoded and decoded != url:
                decoded = urllib.parse.unquote(decoded)
            return decoded
        except:
            return url
    return url

def fix_markdown_images(content):
    """Fix image URLs in markdown content"""
    if not content:
        return content
    
    # Fix markdown image syntax ![alt](url)
    def fix_match(match):
        alt_text = match.group(1)
        url = match.group(2)
        fixed_url = fix_image_url(url)
        return f"![{alt_text}]({fixed_url})"
    
    content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', fix_match, content)
    
    # Also fix HTML img tags that might be in the markdown
    def fix_html_img(match):
        full_tag = match.group(0)
        url = match.group(1)
        fixed_url = fix_image_url(url)
        return full_tag.replace(url, fixed_url)
    
    content = re.sub(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>', fix_html_img, content)
    
    return content

def main():
    # Get all articles
    articles = db.articles.find({})
    
    fixed_count = 0
    total_count = 0
    
    for article in articles:
        total_count += 1
        
        # Check if content needs fixing
        content = article.get('content', '')
        preview = article.get('preview', '')
        
        if not content:
            continue
        
        # Check if there are encoded URLs
        if '%3A%2F%2F' in content or '%2F' in content:
            # Fix the content
            fixed_content = fix_markdown_images(content)
            fixed_preview = fix_markdown_images(preview) if preview else preview
            
            # Update the article
            if fixed_content != content:
                db.articles.update_one(
                    {'_id': article['_id']},
                    {'$set': {
                        'content': fixed_content,
                        'preview': fixed_preview
                    }}
                )
                fixed_count += 1
                print(f"Fixed article: {article.get('title', 'Untitled')[:50]}...")
    
    print(f"\nFixed {fixed_count} out of {total_count} articles")
    
    # Also check for any articles with substackcdn.com images
    substack_articles = db.articles.find({
        'content': {'$regex': 'substackcdn\\.com'}
    })
    
    substack_count = 0
    for article in substack_articles:
        substack_count += 1
        
    print(f"Found {substack_count} articles with Substack CDN images")

if __name__ == '__main__':
    main()