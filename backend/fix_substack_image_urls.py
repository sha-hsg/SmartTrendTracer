"""
Fix Substack CDN image URLs in articles
"""

from pymongo import MongoClient
import urllib.parse
import re

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client.smarttrendtracer

def extract_real_image_url(cdn_url):
    """
    Extract the real image URL from Substack CDN wrapper
    Example input: https://substackcdn.com/image/fetch/w_1100,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F7596f5ed-8d5b-4aca-be4b-cdd23f324820_1100x220.png
    Example output: https://substack-post-media.s3.amazonaws.com/public/images/7596f5ed-8d5b-4aca-be4b-cdd23f324820_1100x220.png
    """
    
    if 'substackcdn.com/image/fetch' in cdn_url:
        # Find the actual URL part (after the last /)
        parts = cdn_url.split('/')
        
        # The URL is typically in the last part, after all the image processing params
        for i, part in enumerate(parts):
            if 'http' in part or '%3A%2F%2F' in part.lower():
                # Found the encoded URL
                actual_url = '/'.join(parts[i:])
                
                # Decode the URL
                if '%' in actual_url:
                    actual_url = urllib.parse.unquote(actual_url)
                    # Double-check for double encoding
                    if '%' in actual_url:
                        actual_url = urllib.parse.unquote(actual_url)
                
                # Ensure it starts with http
                if not actual_url.startswith('http'):
                    if actual_url.startswith('//'):
                        actual_url = 'https:' + actual_url
                    elif not actual_url.startswith('/'):
                        actual_url = 'https://' + actual_url
                
                return actual_url
    
    return cdn_url

def fix_markdown_images(content):
    """Fix Substack CDN URLs in markdown content"""
    if not content:
        return content
    
    # Fix markdown image syntax ![alt](url)
    def fix_match(match):
        alt_text = match.group(1)
        url = match.group(2)
        
        # If it's a Substack CDN URL, extract the real URL
        if 'substackcdn.com/image/fetch' in url:
            fixed_url = extract_real_image_url(url)
            print(f"  Fixed CDN URL: {url[:80]}... -> {fixed_url[:80]}...")
            return f"![{alt_text}]({fixed_url})"
        
        return match.group(0)
    
    content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', fix_match, content)
    
    return content

def main():
    # Get all articles
    articles = list(db.articles.find({}))
    
    print(f"Checking {len(articles)} articles for Substack CDN image URLs...")
    
    fixed_count = 0
    total_images_fixed = 0
    
    for article in articles:
        # Check both content and content_markdown fields
        content = article.get('content', '')
        content_markdown = article.get('content_markdown', '')
        
        updated = False
        updates = {}
        
        # Fix content field if it exists and has CDN URLs
        if content and 'substackcdn.com/image/fetch' in content:
            print(f"\nFixing content in article: {article.get('title', 'Untitled')[:60]}...")
            fixed_content = fix_markdown_images(content)
            
            if fixed_content != content:
                # Count how many images were fixed
                original_images = re.findall(r'substackcdn\.com/image/fetch[^)]+', original_content)
                total_images_fixed += len(original_images)
                
                # Update the article
                db.articles.update_one(
                    {'_id': article['_id']},
                    {'$set': {
                        'content': fixed_content,
                        'updated_at': article.get('updated_at')  # Keep original update time
                    }}
                )
                fixed_count += 1
    
    print(f"\n{'='*60}")
    print(f"Fixed {fixed_count} articles")
    print(f"Total images fixed: {total_images_fixed}")
    
    # Verify the fix
    print(f"\n{'='*60}")
    print("Verification - checking for remaining CDN URLs...")
    remaining = db.articles.find({
        'content': {'$regex': 'substackcdn\\.com/image/fetch'}
    }).count()
    
    if remaining > 0:
        print(f"WARNING: {remaining} articles still contain CDN URLs")
    else:
        print("✅ All Substack CDN URLs have been fixed!")

if __name__ == '__main__':
    main()