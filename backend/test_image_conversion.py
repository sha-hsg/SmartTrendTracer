#!/usr/bin/env python3
"""
Test image preservation in conversion
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db
from app.models.substack import SubstackArticle
from app.services.document_converter import DocumentConverter

def test_image_conversion():
    """Test that images are preserved in conversion"""
    
    db = next(get_db())
    converter = DocumentConverter()
    
    # Get an article with images
    article = db.query(SubstackArticle).filter(
        SubstackArticle.title.like('%recent history of AI%')
    ).first()
    
    if not article:
        print("Article not found")
        return
    
    print(f"=== Testing Image Preservation ===")
    print(f"Article: {article.title}")
    print(f"Author: {article.author.name}\n")
    
    # Convert the HTML
    new_markdown = converter.html_to_markdown(article.content_html)
    
    # Count images in the markdown
    image_count = new_markdown.count('![')
    print(f"Images in converted markdown: {image_count}")
    
    # Show first few images
    lines = new_markdown.split('\n')
    image_lines = []
    for i, line in enumerate(lines):
        if '![' in line:
            image_lines.append((i+1, line))
    
    print(f"\nFirst 5 images in markdown:")
    for line_num, line in image_lines[:5]:
        # Extract just the image markdown
        if '![' in line:
            start = line.find('![')
            end = line.find(')', start) + 1
            if end > start:
                img_md = line[start:end]
                print(f"  Line {line_num}: {img_md[:100]}...")
    
    # Save for inspection
    with open('test_image_output.md', 'w') as f:
        f.write(new_markdown)
    print(f"\nFull output saved to test_image_output.md")
    
    # Compare with current
    current_images = article.content_markdown.count('![') if article.content_markdown else 0
    print(f"\nComparison:")
    print(f"  Current markdown images: {current_images}")
    print(f"  New markdown images: {image_count}")
    
    if image_count > current_images:
        print(f"  ✅ Improvement: +{image_count - current_images} images preserved!")
    
    db.close()

if __name__ == "__main__":
    test_image_conversion()