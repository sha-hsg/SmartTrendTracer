#!/usr/bin/env python3
"""
Reprocess all Substack articles with image preservation
Uses the approach that keeps table structure to maintain image positions
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


def convert_with_images_preserved(html_content: str) -> str:
    """
    Convert HTML to markdown preserving images at correct positions
    Keeps table structure as trade-off for image preservation
    """
    if not html_content:
        return ""
    
    # Parse HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove scripts and styles
    for element in soup.find_all(['script', 'style', 'meta', 'noscript']):
        element.decompose()
    
    # Process images and collect them
    content_images = []
    image_markers = {}
    
    for img in list(soup.find_all('img')):  # Use list() to avoid modifying while iterating
        width = img.get('width', '')
        height = img.get('height', '')
        src = img.get('src', '')
        
        # Convert dimensions
        try:
            w = float(width) if width else 0
            h = float(height) if height else 0
        except:
            w = h = 0
        
        # Remove tracking pixels and small icons
        if (w <= 50 and h <= 50) or 'eotrx' in src.lower() or 'track' in src.lower():
            # Remove the image and its parent link if exists
            parent = img.find_parent('a')
            if parent:
                parent.decompose()
            else:
                img.decompose()
        else:
            # This is a content image - preserve it!
            alt_text = img.get('alt', f'Article image {len(content_images) + 1}')
            
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
    
    # Configure html2text (images will be handled separately)
    h = html2text.HTML2Text()
    h.body_width = 0  # Don't wrap
    h.ignore_links = False
    h.ignore_images = True  # We'll handle images manually
    h.ignore_tables = False  # Keep tables for layout
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
    
    # Clean up the worst artifacts
    # Remove invisible characters
    markdown = re.sub(r'[\u00AD\u200B\u200C\u200D\uFEFF]+', '', markdown)
    markdown = re.sub(r'[\u00A0]+', ' ', markdown)
    
    # Remove excessive blank lines
    markdown = re.sub(r'\n{5,}', '\n\n\n', markdown)
    
    # Clean up excessive spaces in tables
    markdown = re.sub(r'\|\s{10,}\|', '|  |', markdown)
    
    return markdown.strip()


def main():
    """Reprocess all Substack articles with image preservation"""
    print("=" * 60)
    print("Reprocessing Substack Articles with Image Preservation")
    print("=" * 60)
    print(f"Started: {datetime.now()}")
    print("\nThis will preserve images at their correct positions")
    print("Trade-off: Table structure will be kept (some artifacts)")
    print("-" * 60)
    
    db = next(get_db())
    
    # Get all articles with HTML content
    articles = db.query(SubstackArticle).filter(
        SubstackArticle.content_html.isnot(None)
    ).all()
    
    print(f"\nFound {len(articles)} articles to reprocess\n")
    
    success_count = 0
    error_count = 0
    images_found_total = 0
    
    for i, article in enumerate(articles, 1):
        try:
            print(f"[{i}/{len(articles)}] {article.title[:50]}...")
            
            # Convert with image preservation
            new_markdown = convert_with_images_preserved(article.content_html)
            
            if new_markdown:
                # Count images
                image_count = new_markdown.count('![')
                images_found_total += image_count
                
                # Update the article
                article.content_markdown = new_markdown
                
                # Show stats
                old_len = len(article.content_markdown) if article.content_markdown else 0
                new_len = len(new_markdown)
                
                print(f"  ✅ Success: {new_len:,} chars, {image_count} images")
                
                if image_count > 0:
                    print(f"  🖼️  Found {image_count} images!")
                
                success_count += 1
            else:
                print(f"  ⚠️  No content generated")
                error_count += 1
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            error_count += 1
    
    # Commit changes
    try:
        db.commit()
        print("\n✅ Changes saved to database")
    except Exception as e:
        print(f"\n❌ Error saving to database: {e}")
        db.rollback()
    
    # Summary
    print("\n" + "=" * 60)
    print("REPROCESSING COMPLETE")
    print("=" * 60)
    print(f"✅ Successful: {success_count} articles")
    print(f"🖼️  Total images found: {images_found_total}")
    print(f"❌ Errors: {error_count} articles")
    print(f"Success rate: {success_count/len(articles)*100:.1f}%")
    print(f"\nCompleted: {datetime.now()}")
    
    db.close()


if __name__ == "__main__":
    main()