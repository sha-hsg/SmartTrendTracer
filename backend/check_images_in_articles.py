#!/usr/bin/env python3
"""
Check what images are in Substack articles
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db
from app.models.substack import SubstackArticle
from bs4 import BeautifulSoup

def check_images_in_articles():
    """Check for images in articles"""
    
    db = next(get_db())
    
    # Get articles
    articles = db.query(SubstackArticle).filter(
        SubstackArticle.content_html.isnot(None)
    ).limit(5).all()
    
    print("=== Checking for Images in Articles ===\n")
    
    for article in articles:
        print(f"\n{'='*60}")
        print(f"Article: {article.title[:50]}...")
        print(f"Author: {article.author.name}")
        
        # Parse HTML to look for images
        soup = BeautifulSoup(article.content_html, 'html.parser')
        
        # Find all images
        images = soup.find_all('img')
        
        print(f"\nImages found: {len(images)}")
        
        if images:
            for i, img in enumerate(images[:10], 1):  # Show first 10 images
                src = img.get('src', 'No src')
                alt = img.get('alt', 'No alt')
                width = img.get('width', 'No width')
                height = img.get('height', 'No height')
                
                # Check if it's a tracking pixel or real content
                is_tracking = any(x in src.lower() for x in ['track', 'pixel', 'analytics', 'open', '1x1'])
                
                print(f"\n  Image {i}:")
                print(f"    Src: {src[:100]}...")
                print(f"    Alt: {alt[:50] if alt != 'No alt' else 'No alt'}")
                print(f"    Size: {width}x{height}")
                if is_tracking:
                    print(f"    ⚠️  Likely tracking pixel")
                else:
                    print(f"    ✅ Content image")
        
        # Check current markdown for images
        if article.content_markdown:
            md_images = article.content_markdown.count('![')
            print(f"\nImages in current markdown: {md_images}")
    
    db.close()

if __name__ == "__main__":
    check_images_in_articles()