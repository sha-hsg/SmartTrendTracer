#!/usr/bin/env python3
"""Debug image positioning in articles"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import SessionLocal, SubstackArticle, SubstackAuthor

def main():
    db = SessionLocal()
    
    print("🔍 DEBUGGING IMAGE POSITIONING IN ARTICLES")
    print("=" * 80)
    
    # Get sample articles from different authors
    test_authors = [
        ('Ethan Mollick from One Useful Thing', 'Direct subscription'),
        ('Nathan Lambert', 'Forwarded email'),
        ('Gary Marcus', 'Forwarded email')
    ]
    
    for author_name, article_type in test_authors:
        print(f"\n👤 {author_name.upper()} ({article_type}):")
        
        author = db.query(SubstackAuthor).filter_by(name=author_name).first()
        if not author:
            print(f"   ❌ Author not found")
            continue
        
        # Get an article with images
        articles_with_images = db.query(SubstackArticle).filter_by(author_id=author.id).all()
        
        # Find article with most images
        best_article = None
        max_images = 0
        
        for article in articles_with_images:
            if article.content_markdown:
                image_count = article.content_markdown.count('![')
                if image_count > max_images:
                    max_images = image_count
                    best_article = article
        
        if not best_article or max_images == 0:
            print(f"   ⚪ No articles with images found")
            continue
        
        print(f"   📄 Article: {best_article.title[:50]}...")
        print(f"   🖼️  Total images: {max_images}")
        print(f"   📝 Word count: {best_article.word_count}")
        
        # Analyze image positioning
        content = best_article.content_markdown
        if not content:
            print(f"   ❌ No content")
            continue
        
        # Split content into sections and find where images appear
        lines = content.split('\n')
        total_lines = len(lines)
        
        image_positions = []
        text_before_first_image = 0
        text_after_last_image = 0
        
        for i, line in enumerate(lines):
            if line.strip().startswith('!['):
                image_positions.append(i)
        
        if image_positions:
            # Calculate positioning metrics
            first_image_line = image_positions[0]
            last_image_line = image_positions[-1]
            
            text_before_first_image = first_image_line
            text_after_last_image = total_lines - last_image_line - 1
            
            # Calculate relative positions (as percentages)
            first_image_percent = (first_image_line / total_lines) * 100
            last_image_percent = (last_image_line / total_lines) * 100
            
            print(f"   📊 Image positioning analysis:")
            print(f"      First image at line {first_image_line}/{total_lines} ({first_image_percent:.1f}%)")
            print(f"      Last image at line {last_image_line}/{total_lines} ({last_image_percent:.1f}%)")
            print(f"      Text before first image: {text_before_first_image} lines")
            print(f"      Text after last image: {text_after_last_image} lines")
            
            # Show image distribution
            if len(image_positions) > 1:
                print(f"      Images distributed across {(last_image_percent - first_image_percent):.1f}% of article")
            
            # Flag if images seem clustered at the end
            if first_image_percent > 80:
                print(f"      ⚠️  ISSUE: Images start very late in article ({first_image_percent:.1f}%)")
            elif last_image_percent > 90 and len(image_positions) > 1:
                print(f"      ⚠️  ISSUE: Images seem clustered at end")
            else:
                print(f"      ✅ Images appear well-distributed")
        
        # Show first few images and their context
        print(f"\n   🔍 First 2 images and their context:")
        for i, line in enumerate(lines):
            if line.strip().startswith('!['):
                # Show context around this image
                start_context = max(0, i-2)
                end_context = min(total_lines, i+3)
                
                print(f"      Image at line {i}:")
                for j in range(start_context, end_context):
                    marker = ">>>>" if j == i else "    "
                    line_preview = lines[j][:80] + "..." if len(lines[j]) > 80 else lines[j]
                    print(f"      {marker} {line_preview}")
                print()
                
                # Only show first 2 images to keep output manageable
                if len([x for x in lines[:i+1] if x.strip().startswith('![')]) >= 2:
                    break
    
    db.close()

if __name__ == "__main__":
    main()