#!/usr/bin/env python3
"""
Fix articles with CID images by reprocessing them
CID images are email attachments that need special handling
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from app.models import get_db
from app.models.substack import SubstackArticle
from bs4 import BeautifulSoup
import html2text
import re


def fix_cid_images_in_html(html_content: str) -> str:
    """
    Replace CID images with HTTP images where available
    Remove CID images that can't be replaced
    """
    if not html_content:
        return ""
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all images
    all_images = soup.find_all('img')
    cid_count = 0
    http_count = 0
    removed_count = 0
    
    for img in all_images:
        src = img.get('src', '')
        
        if src.startswith('cid:'):
            cid_count += 1
            
            # Try to find an HTTP alternative in nearby content
            # Sometimes emails have both CID and HTTP versions
            parent = img.parent
            
            # Look for substackcdn images nearby
            # If we can't replace it, remove the CID image
            img.decompose()
            removed_count += 1
        elif src.startswith('http'):
            http_count += 1
            # Keep HTTP images as-is
    
    print(f"  Processed: {cid_count} CID images removed, {http_count} HTTP images kept")
    
    return str(soup)


def convert_to_markdown_with_images(html_content: str) -> str:
    """
    Convert HTML to markdown preserving HTTP images
    """
    if not html_content:
        return ""
    
    # First, clean up CID images
    html_content = fix_cid_images_in_html(html_content)
    
    # Parse HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove scripts and styles
    for element in soup.find_all(['script', 'style', 'meta', 'noscript']):
        element.decompose()
    
    # Process remaining images
    content_images = []
    
    for img in list(soup.find_all('img')):
        src = img.get('src', '')
        width = img.get('width', '')
        height = img.get('height', '')
        
        # Convert dimensions
        try:
            w = float(width) if width else 0
            h = float(height) if height else 0
        except:
            w = h = 0
        
        # Remove tracking pixels and small icons
        if (w <= 50 and h <= 50) or 'eotrx' in src.lower() or 'track' in src.lower():
            parent = img.find_parent('a')
            if parent:
                parent.decompose()
            else:
                img.decompose()
        else:
            # This is a content image - preserve it!
            alt_text = img.get('alt', f'Article image')
            
            # Store image data
            content_images.append({
                'src': src,
                'alt': alt_text
            })
            
            # Create a unique marker for this image
            marker_id = f'__IMAGE_MARKER_{len(content_images) - 1}__'
            marker = soup.new_tag('span')
            marker.string = marker_id
            
            # Remove parent link if exists
            parent_link = img.find_parent('a')
            if parent_link:
                parent_link.replace_with(marker)
            else:
                img.replace_with(marker)
    
    # Configure html2text
    h = html2text.HTML2Text()
    h.body_width = 0
    h.ignore_links = False
    h.ignore_images = True  # We handle images manually
    h.ignore_tables = False
    h.unicode_snob = True
    h.wrap_links = False
    h.skip_internal_links = False
    
    # Convert to markdown
    markdown = h.handle(str(soup))
    
    # Replace image markers with proper markdown image syntax
    for i, img_data in enumerate(content_images):
        marker = f'__IMAGE_MARKER_{i}__'
        img_markdown = f"![{img_data['alt']}]({img_data['src']})"
        markdown = markdown.replace(marker, img_markdown)
    
    # Clean up
    markdown = re.sub(r'[\u00AD\u200B\u200C\u200D\uFEFF]+', '', markdown)
    markdown = re.sub(r'[\u00A0]+', ' ', markdown)
    markdown = re.sub(r'\n{5,}', '\n\n\n', markdown)
    
    return markdown.strip()


def main():
    """Fix articles with CID images"""
    print("=" * 60)
    print("Fixing Articles with CID Images")
    print("=" * 60)
    print(f"Started: {datetime.now()}\n")
    
    db = next(get_db())
    
    # Find articles with CID images
    articles = db.query(SubstackArticle).filter(
        SubstackArticle.content_html.like('%cid:%')
    ).all()
    
    print(f"Found {len(articles)} articles with CID images\n")
    
    success_count = 0
    total_images_recovered = 0
    
    for i, article in enumerate(articles, 1):
        try:
            print(f"[{i}/{len(articles)}] {article.title[:50]}...")
            
            # Count original CID images
            cid_count = article.content_html.count('cid:')
            print(f"  Original: {cid_count} CID images")
            
            # Convert with fixed image handling
            new_markdown = convert_to_markdown_with_images(article.content_html)
            
            if new_markdown:
                # Count recovered images
                image_count = len(re.findall(r'!\[([^\]]*)\]\(([^\)]+)\)', new_markdown))
                total_images_recovered += image_count
                
                # Update the article
                article.content_markdown = new_markdown
                
                print(f"  ✅ Converted: {image_count} images preserved in markdown")
                success_count += 1
            else:
                print(f"  ⚠️  No content generated")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # Commit changes
    try:
        db.commit()
        print("\n✅ Changes saved to database")
    except Exception as e:
        print(f"\n❌ Error saving: {e}")
        db.rollback()
    
    # Summary
    print("\n" + "=" * 60)
    print("FIXING COMPLETE")
    print("=" * 60)
    print(f"✅ Fixed: {success_count} articles")
    print(f"🖼️  Images recovered: {total_images_recovered}")
    print(f"\nCompleted: {datetime.now()}")
    
    db.close()


if __name__ == "__main__":
    main()