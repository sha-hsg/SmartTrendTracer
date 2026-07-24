"""
Fix Substack CDN URLs in article content_markdown field
"""

from pymongo import MongoClient
import urllib.parse
import re

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client.smarttrendtracer

def fix_substack_cdn_url(url):
    """
    Fix malformed Substack CDN URLs
    The URLs have broken parameters like $s_!lRtE! that should be removed
    """
    
    # Pattern for Substack CDN URLs with broken parameters
    if 'substackcdn.com/image/fetch' in url:
        # Extract the actual image URL from the parameters
        # Look for the actual URL which starts with https%3A%2F%2F
        match = re.search(r'https%3A%2F%2F[^)]+', url)
        if match:
            encoded_url = match.group(0)
            # Decode the URL
            decoded_url = urllib.parse.unquote(encoded_url)
            return decoded_url
        else:
            # If we can't find the encoded URL, try to clean up the parameters
            # Remove the broken parameter part
            url = re.sub(r'\$s_[^,]+,', '', url)
            return url
    
    return url

def fix_markdown_content(content):
    """Fix all image URLs in markdown content"""
    if not content:
        return content
    
    fixed_count = 0
    
    # Fix markdown image syntax ![alt](url)
    def fix_match(match):
        nonlocal fixed_count
        alt_text = match.group(1)
        url = match.group(2)
        
        if 'substackcdn.com/image/fetch' in url:
            fixed_url = fix_substack_cdn_url(url)
            if fixed_url != url:
                fixed_count += 1
                print(f"  Fixed: {url[:80]}...")
                print(f"     To: {fixed_url[:80]}...")
            return f"![{alt_text}]({fixed_url})"
        
        return match.group(0)
    
    content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', fix_match, content)
    
    return content, fixed_count

def main():
    # Get all articles with content_markdown
    articles = list(db.articles.find({
        'content_markdown': {'$exists': True, '$ne': None, '$ne': ''}
    }))
    
    print(f"Found {len(articles)} articles with content_markdown")
    
    total_fixed = 0
    articles_fixed = 0
    
    for article in articles:
        content = article.get('content_markdown', '')
        
        if 'substackcdn.com/image/fetch' in content:
            print(f"\nProcessing: {article.get('title', 'Untitled')[:60]}...")
            
            fixed_content, fix_count = fix_markdown_content(content)
            
            if fix_count > 0:
                # Update the article
                db.articles.update_one(
                    {'_id': article['_id']},
                    {'$set': {
                        'content_markdown': fixed_content
                    }}
                )
                
                articles_fixed += 1
                total_fixed += fix_count
                print(f"  Fixed {fix_count} images")
    
    print(f"\n{'='*60}")
    print(f"Fixed {articles_fixed} articles")
    print(f"Total images fixed: {total_fixed}")
    
    # Verify
    remaining = db.articles.count_documents({
        'content_markdown': {'$regex': r'substackcdn\.com/image/fetch/\$s_'}
    })
    
    if remaining > 0:
        print(f"\nWARNING: {remaining} articles still have broken URLs")
    else:
        print("\n✅ All Substack CDN URLs have been fixed!")

if __name__ == '__main__':
    main()