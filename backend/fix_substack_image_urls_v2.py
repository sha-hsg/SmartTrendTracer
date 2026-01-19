"""
Fix Substack CDN image URLs in articles - Version 2
Handles both content and content_markdown fields
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
    def fix_image_match(match):
        alt_text = match.group(1)
        url = match.group(2)
        
        # If it's a Substack CDN URL, extract the real URL
        if 'substackcdn.com/image/fetch' in url:
            fixed_url = extract_real_image_url(url)
            return f"![{alt_text}]({fixed_url})"
        
        return match.group(0)
    
    # Fix linked images [![alt](img_url)](link_url) where link_url is CDN
    def fix_linked_image_match(match):
        alt_text = match.group(1)
        img_url = match.group(2)
        link_url = match.group(3)
        
        # If the link URL is a Substack CDN URL, just use the image URL
        if 'substackcdn.com/image/fetch' in link_url:
            # Just return the image without the link wrapper
            return f"![{alt_text}]({img_url})"
        
        return match.group(0)
    
    # First fix linked images (must come before regular images)
    content = re.sub(r'\[!\[([^\]]*)\]\(([^)]+)\)\]\(([^)]+)\)', fix_linked_image_match, content)
    
    # Then fix regular images
    content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', fix_image_match, content)
    
    return content

def main():
    # Get all articles with CDN URLs
    query = {
        '$or': [
            {'content': {'$regex': 'substackcdn\\.com/image/fetch'}},
            {'content_markdown': {'$regex': 'substackcdn\\.com/image/fetch'}}
        ]
    }
    
    articles = list(db.articles.find(query))
    
    print(f"Found {len(articles)} articles with Substack CDN image URLs...")
    
    fixed_count = 0
    total_images_fixed = 0
    
    for article in articles:
        print(f"\nProcessing: {article.get('title', 'Untitled')[:60]}...")
        
        updates = {}
        
        # Fix content field
        content = article.get('content', '')
        if content and 'substackcdn.com/image/fetch' in content:
            original_content = content
            fixed_content = fix_markdown_images(content)
            
            if fixed_content != original_content:
                updates['content'] = fixed_content
                # Count images fixed
                cdn_urls = re.findall(r'substackcdn\.com/image/fetch[^)]+', original_content)
                total_images_fixed += len(cdn_urls)
                print(f"  Fixed {len(cdn_urls)} images in content field")
        
        # Fix content_markdown field
        content_markdown = article.get('content_markdown', '')
        if content_markdown and 'substackcdn.com/image/fetch' in content_markdown:
            original_markdown = content_markdown
            fixed_markdown = fix_markdown_images(content_markdown)
            
            if fixed_markdown != original_markdown:
                updates['content_markdown'] = fixed_markdown
                # Count images fixed
                cdn_urls = re.findall(r'substackcdn\.com/image/fetch[^)]+', original_markdown)
                total_images_fixed += len(cdn_urls)
                print(f"  Fixed {len(cdn_urls)} images in content_markdown field")
        
        # Update the article if we made changes
        if updates:
            db.articles.update_one(
                {'_id': article['_id']},
                {'$set': updates}
            )
            fixed_count += 1
            print(f"  ✅ Updated article")
    
    print(f"\n{'='*60}")
    print(f"Fixed {fixed_count} articles")
    print(f"Total images fixed: {total_images_fixed}")
    
    # Verify the fix
    print(f"\n{'='*60}")
    print("Verification - checking for remaining CDN URLs...")
    remaining = db.articles.count_documents({
        '$or': [
            {'content': {'$regex': 'substackcdn\\.com/image/fetch'}},
            {'content_markdown': {'$regex': 'substackcdn\\.com/image/fetch'}}
        ]
    })
    
    if remaining > 0:
        print(f"WARNING: {remaining} articles still contain CDN URLs")
        # Show one example
        example = db.articles.find_one({
            '$or': [
                {'content': {'$regex': 'substackcdn\\.com/image/fetch'}},
                {'content_markdown': {'$regex': 'substackcdn\\.com/image/fetch'}}
            ]
        })
        if example:
            print(f"Example: {example.get('title', 'Untitled')[:60]}")
    else:
        print("✅ All Substack CDN URLs have been fixed!")

if __name__ == '__main__':
    main()