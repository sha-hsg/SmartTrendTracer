#!/usr/bin/env python3
"""
Reprocess forwarded Substack articles with special handling
Forwarded emails often have different image structures and need more lenient processing
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from app.models import get_db
from app.models.substack import SubstackArticle, SubstackAuthor
from bs4 import BeautifulSoup
import html2text
import re


def is_forwarded_article(article):
    """
    Check if article is from a forwarded email
    """
    # Check known forwarded authors
    forwarded_authors = ['Nathan Lambert', 'Gary Marcus', 'Sebastian Raschka']
    
    if article.author and article.author.name in forwarded_authors:
        return True
    
    # Check for forwarding indicators in HTML
    if article.content_html and 'Forwarded' in article.content_html[:2000]:
        return True
        
    return False


def convert_forwarded_email_to_markdown(html_content: str) -> str:
    """
    Convert forwarded email HTML to markdown with special handling
    More lenient with images, different size thresholds
    """
    if not html_content:
        return ""
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove scripts and styles
    for element in soup.find_all(['script', 'style', 'meta', 'noscript']):
        element.decompose()
    
    # Remove CID images (email attachments that can't be displayed)
    for img in soup.find_all('img'):
        if img.get('src', '').startswith('cid:'):
            img.decompose()
    
    # Process remaining images with more lenient rules for forwarded emails
    content_images = []
    
    for img in list(soup.find_all('img')):
        src = img.get('src', '')
        width = img.get('width', '')
        height = img.get('height', '')
        
        # Skip empty src
        if not src:
            img.decompose()
            continue
            
        # Convert dimensions
        try:
            w = float(width) if width else 0
            h = float(height) if height else 0
        except:
            w = h = 0
        
        # For forwarded emails, be more lenient with image sizes
        # Only remove very small tracking pixels (1x1) and obvious trackers
        should_remove = False
        
        # Remove 1x1 tracking pixels
        if w == 1 and h == 1:
            should_remove = True
        
        # Remove known tracking domains
        tracking_domains = ['eotrx', 'track', 'pixel', 'analytics', 'doubleclick']
        if any(domain in src.lower() for domain in tracking_domains):
            should_remove = True
        
        # For forwarded emails, KEEP 18x18 images (often avatars/icons)
        # KEEP anything without dimensions (likely content images)
        # KEEP anything larger than 1x1 unless it's a known tracker
        
        if should_remove:
            parent = img.find_parent('a')
            if parent:
                parent.decompose()
            else:
                img.decompose()
        else:
            # This is likely a content image - preserve it!
            alt_text = img.get('alt', '')
            if not alt_text:
                # Generate alt text based on context
                if 'avatar' in src.lower() or w == 18:
                    alt_text = 'Profile image'
                elif 'logo' in src.lower():
                    alt_text = 'Logo'
                else:
                    alt_text = f'Article image {len(content_images) + 1}'
            
            # Store image data
            content_images.append({
                'src': src,
                'alt': alt_text,
                'width': w,
                'height': h
            })
            
            # Create a unique marker for this image
            marker_id = f'__IMG_MARKER_{len(content_images) - 1}__'
            marker = soup.new_tag('span')
            marker.string = marker_id
            
            # Remove parent link wrapper if it exists
            parent_link = img.find_parent('a')
            if parent_link and 'substack.com/redirect' in parent_link.get('href', ''):
                # This is a Substack redirect wrapper, remove it
                parent_link.replace_with(marker)
            else:
                img.replace_with(marker)
    
    # Configure html2text
    h = html2text.HTML2Text()
    h.body_width = 0
    h.ignore_links = False
    h.ignore_images = True  # We handle images manually
    h.ignore_tables = False  # Keep tables for layout
    h.unicode_snob = True
    h.wrap_links = False
    h.skip_internal_links = False
    
    # Convert to markdown
    markdown = h.handle(str(soup))
    
    # Replace image markers with proper markdown image syntax
    for i, img_data in enumerate(content_images):
        marker = f'__IMG_MARKER_{i}__'
        # For small images (avatars), add a note
        if img_data['width'] == 18 and img_data['height'] == 18:
            img_markdown = f"![{img_data['alt']}]({img_data['src']})"
        else:
            img_markdown = f"![{img_data['alt']}]({img_data['src']})"
        markdown = markdown.replace(marker, img_markdown)
    
    # Clean up artifacts
    markdown = re.sub(r'[\u00AD\u200B\u200C\u200D\uFEFF]+', '', markdown)
    markdown = re.sub(r'[\u00A0]+', ' ', markdown)
    markdown = re.sub(r'\n{5,}', '\n\n\n', markdown)
    
    # Remove table artifacts while preserving image tables
    lines = markdown.split('\n')
    cleaned_lines = []
    
    for i, line in enumerate(lines):
        # Skip pure separator lines unless they're part of image tables
        if ('---|' in line or line.strip() == '|' or line.strip() == '---'):
            # Check if previous or next line has an image
            has_image_context = False
            if i > 0 and '![' in lines[i-1]:
                has_image_context = True
            if i < len(lines) - 1 and '![' in lines[i+1]:
                has_image_context = True
            
            if not has_image_context:
                continue  # Skip this artifact
        
        cleaned_lines.append(line)
    
    markdown = '\n'.join(cleaned_lines)
    
    return markdown.strip()


def main():
    """Reprocess forwarded articles with special handling"""
    print("=" * 60)
    print("Reprocessing Forwarded Substack Articles")
    print("=" * 60)
    print(f"Started: {datetime.now()}\n")
    
    db = next(get_db())
    
    # Get all articles
    articles = db.query(SubstackArticle).filter(
        SubstackArticle.content_html.isnot(None)
    ).all()
    
    # Filter forwarded articles
    forwarded_articles = [a for a in articles if is_forwarded_article(a)]
    
    print(f"Found {len(forwarded_articles)} forwarded articles to reprocess\n")
    
    success_count = 0
    total_images_found = 0
    
    for i, article in enumerate(forwarded_articles, 1):
        try:
            print(f"[{i}/{len(forwarded_articles)}] {article.title[:50]}...")
            print(f"  Author: {article.author.name if article.author else 'Unknown'}")
            
            # Count original images in HTML
            orig_img_count = article.content_html.count('<img')
            cid_count = article.content_html.count('cid:')
            print(f"  Original HTML: {orig_img_count} images ({cid_count} CID)")
            
            # Convert with special handling
            new_markdown = convert_forwarded_email_to_markdown(article.content_html)
            
            if new_markdown:
                # Count images in new markdown
                image_matches = re.findall(r'!\[([^\]]*)\]\(([^\)]+)\)', new_markdown)
                image_count = len(image_matches)
                total_images_found += image_count
                
                # Update the article
                article.content_markdown = new_markdown
                
                # Show some image details
                if image_matches:
                    print(f"  ✅ Preserved {image_count} images:")
                    for j, (alt, src) in enumerate(image_matches[:3], 1):
                        print(f"     {j}. {alt[:30]} - {src[:50]}...")
                    if image_count > 3:
                        print(f"     ... and {image_count - 3} more")
                else:
                    print(f"  ℹ️  No displayable images found")
                
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
    print("REPROCESSING COMPLETE")
    print("=" * 60)
    print(f"✅ Processed: {success_count} forwarded articles")
    print(f"🖼️  Total images preserved: {total_images_found}")
    print(f"\nCompleted: {datetime.now()}")
    
    db.close()


if __name__ == "__main__":
    main()