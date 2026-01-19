"""
Fix broken image URLs by re-fetching articles from source and downloading images locally.

This script will:
1. Re-fetch each article from its original URL
2. Extract current image URLs from the fresh HTML
3. Download images to local storage
4. Update the database with local image paths
"""

import os
import re
import requests
import hashlib
from urllib.parse import urlparse, urljoin
from pathlib import Path
from pymongo import MongoClient
from bs4 import BeautifulSoup
from datetime import datetime
import time
import json

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client.smarttrendtracer

# Local image storage directory
IMAGE_DIR = Path("data/article_images")
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

# Track progress
progress_file = Path("image_fix_progress.json")

def load_progress():
    """Load progress from file"""
    if progress_file.exists():
        with open(progress_file, 'r') as f:
            return json.load(f)
    return {'processed': [], 'failed': []}

def save_progress(progress):
    """Save progress to file"""
    with open(progress_file, 'w') as f:
        json.dump(progress, f, indent=2)

def get_image_filename(url, article_id):
    """Generate a unique filename for an image"""
    # Create hash from URL for uniqueness
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    
    # Get file extension
    parsed = urlparse(url)
    path = parsed.path
    ext = '.jpg'  # default
    
    if '.' in path:
        ext = path.split('.')[-1]
        if ext in ['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg']:
            ext = '.' + ext
        else:
            ext = '.jpg'
    
    # Create filename: articleId_hash.ext
    filename = f"{article_id}_{url_hash}{ext}"
    return filename

def download_image(url, filepath):
    """Download an image from URL to local file"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30, stream=True)
        response.raise_for_status()
        
        # Check if it's actually an image
        content_type = response.headers.get('content-type', '')
        if 'image' not in content_type and 'svg' not in content_type:
            print(f"    Warning: Not an image content-type: {content_type}")
            return False
        
        # Save the image
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return True
    except Exception as e:
        print(f"    Error downloading image: {e}")
        return False

def fetch_article_html(url):
    """Fetch the current HTML of an article from its URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        return response.text
    except Exception as e:
        print(f"  Error fetching article: {e}")
        return None

def extract_real_url_from_cdn(cdn_url):
    """Extract the real S3 URL from Substack CDN wrapper"""
    # Look for the encoded URL part
    if 'substackcdn.com/image/fetch' in cdn_url:
        match = re.search(r'(https?%3A%2F%2F[^/]+)', cdn_url)
        if match:
            encoded_url = match.group(0)
            # Find everything after this
            remaining = cdn_url[cdn_url.index(encoded_url):]
            # Decode the URL
            decoded_url = requests.utils.unquote(remaining)
            return decoded_url
    return cdn_url

def extract_images_from_html(html, base_url):
    """Extract all image URLs from HTML content"""
    soup = BeautifulSoup(html, 'html.parser')
    images = []
    
    # Find all img tags
    for img in soup.find_all('img'):
        src = img.get('src')
        if src:
            # Make absolute URL
            absolute_url = urljoin(base_url, src)
            
            # Skip data URLs and tracking pixels
            if not absolute_url.startswith('data:') and '1x1' not in absolute_url:
                images.append(absolute_url)
    
    # Also check for images in picture elements
    for picture in soup.find_all('picture'):
        for source in picture.find_all('source'):
            srcset = source.get('srcset')
            if srcset:
                # Extract first URL from srcset
                url = srcset.split(',')[0].split(' ')[0]
                absolute_url = urljoin(base_url, url)
                if not absolute_url.startswith('data:'):
                    images.append(absolute_url)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_images = []
    for img in images:
        if img not in seen:
            seen.add(img)
            unique_images.append(img)
    
    return unique_images

def update_content_with_local_images(content, image_mapping):
    """Replace external image URLs with local paths in content"""
    if not content:
        return content
    
    # Sort by length (longest first) to avoid partial replacements
    for old_url, new_path in sorted(image_mapping.items(), key=lambda x: len(x[0]), reverse=True):
        # Replace in markdown format ![alt](url)
        content = content.replace(f']({old_url})', f']({new_path})')
        # Replace in HTML format src="url"
        content = content.replace(f'src="{old_url}"', f'src="{new_path}"')
        content = content.replace(f"src='{old_url}'", f"src='{new_path}'")
        # Replace plain URLs
        content = content.replace(old_url, new_path)
    
    return content

def process_article(article):
    """Process a single article to fix its images"""
    article_id = str(article['_id'])
    title = article.get('title', 'Untitled')[:60]
    url = article.get('url')
    
    if not url:
        print(f"  Skipping (no URL): {title}")
        return False
    
    print(f"\n{title}...")
    print(f"  URL: {url}")
    
    # Check if it's a Substack article
    is_substack = 'substack.com' in url
    
    # For Substack articles, we should definitely re-fetch
    # For others, we might want to be more careful
    if not is_substack:
        print("  Non-Substack article - checking existing images first")
        # Check if images in content are already broken
        content = article.get('content_markdown', '') or article.get('content', '')
        if not re.search(r'https?://[^\s\)]+\.(jpg|jpeg|png|gif|webp|svg)', content, re.IGNORECASE):
            print("  No external images found")
            return False
    
    # Re-fetch the article HTML
    print("  Fetching current article HTML...")
    html = fetch_article_html(url)
    if not html:
        print("  Failed to fetch article")
        return False
    
    # Extract current image URLs
    print("  Extracting image URLs...")
    image_urls = extract_images_from_html(html, url)
    
    if not image_urls:
        print("  No images found in article")
        return True
    
    # Also get any S3 URLs already in the content
    existing_content = article.get('content_markdown', '') or article.get('content', '')
    s3_urls = re.findall(r'https?://[^\s\)]+\.s3\.amazonaws\.com[^\s\)]*', existing_content)
    
    # Combine all image URLs (from HTML + existing content)
    all_image_urls = list(set(image_urls + s3_urls))
    
    print(f"  Found {len(image_urls)} images in HTML")
    print(f"  Found {len(s3_urls)} S3 images in existing content") 
    print(f"  Total unique images to process: {len(all_image_urls)}")
    
    # Download images and create mapping
    image_mapping = {}
    images_metadata = []
    
    for img_url in all_image_urls:
        # Extract the real URL if it's a CDN wrapper
        real_url = extract_real_url_from_cdn(img_url)
        
        filename = get_image_filename(img_url, article_id)
        filepath = IMAGE_DIR / filename
        local_url = f"/api/articles/{article_id}/images/{filename}"
        
        # Skip if already downloaded
        if filepath.exists():
            print(f"    Already exists: {filename}")
        else:
            print(f"    Downloading: {img_url[:60]}...")
            if download_image(img_url, filepath):
                print(f"    Saved as: {filename}")
            else:
                print(f"    Failed to download")
                continue
        
        # Map both the CDN URL and the real URL to local path
        image_mapping[img_url] = local_url
        if real_url != img_url:
            image_mapping[real_url] = local_url
            print(f"    Mapped both CDN and real URL")
        
        images_metadata.append({
            'original_url': img_url,
            'real_url': real_url,
            'local_path': str(filepath),
            'local_url': local_url,
            'filename': filename,
            'size': filepath.stat().st_size if filepath.exists() else 0
        })
    
    # Update article content with local image URLs
    updates = {}
    
    if article.get('content'):
        updates['content'] = update_content_with_local_images(
            article['content'], image_mapping
        )
    
    if article.get('content_markdown'):
        updates['content_markdown'] = update_content_with_local_images(
            article['content_markdown'], image_mapping
        )
    
    # Store images metadata
    updates['images'] = images_metadata
    updates['images_updated_at'] = datetime.utcnow()
    
    # Update the article
    if updates:
        db.articles.update_one(
            {'_id': article['_id']},
            {'$set': updates}
        )
        print(f"  ✅ Updated with {len(images_metadata)} local images")
        return True
    
    return False

def main():
    """Main function to process all articles"""
    progress = load_progress()
    
    # Get all articles
    articles = list(db.articles.find().sort('published_at', -1))
    total = len(articles)
    
    print(f"Found {total} articles to process")
    print(f"Already processed: {len(progress['processed'])}")
    print(f"Previously failed: {len(progress['failed'])}")
    
    fixed_count = 0
    
    for i, article in enumerate(articles, 1):
        article_id = str(article['_id'])
        
        # Skip if already processed
        if article_id in progress['processed']:
            continue
        
        # Skip if previously failed (unless retry flag is set)
        if article_id in progress['failed']:
            continue
        
        print(f"\n[{i}/{total}] Processing article...")
        
        try:
            if process_article(article):
                fixed_count += 1
                progress['processed'].append(article_id)
            else:
                progress['processed'].append(article_id)  # Mark as processed even if no changes
            
            # Save progress periodically
            if i % 5 == 0:
                save_progress(progress)
            
            # Be nice to servers
            time.sleep(1)
            
        except Exception as e:
            print(f"  Error: {e}")
            progress['failed'].append(article_id)
            save_progress(progress)
    
    # Final save
    save_progress(progress)
    
    print(f"\n{'='*60}")
    print(f"Completed! Fixed {fixed_count} articles")
    print(f"Total processed: {len(progress['processed'])}")
    print(f"Failed: {len(progress['failed'])}")

if __name__ == '__main__':
    main()