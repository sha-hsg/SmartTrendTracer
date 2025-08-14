#!/usr/bin/env python3
"""
Test image extraction from Substack articles
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import SessionLocal, SubstackArticle
from app.collectors.gmail_substack_collector import GmailSubstackCollector

def test_article(article_id):
    """Test extraction on a specific article"""
    db = SessionLocal()
    collector = GmailSubstackCollector()
    
    # Get article
    article = db.query(SubstackArticle).filter(SubstackArticle.id == article_id).first()
    
    if not article:
        print(f"Article {article_id} not found")
        return
    
    print(f"Testing: {article.title}")
    print(f"Original word count: {article.word_count}")
    
    # Re-extract with image preservation
    if article.content_html:
        result = collector._parse_substack_html(article.content_html)
        
        if result and result.get('content_markdown'):
            markdown = result['content_markdown']
            
            # Count images
            import re
            images = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', markdown)
            
            print(f"\n✅ Extraction successful!")
            print(f"   New word count: {len(markdown.split())}")
            print(f"   Images found: {len(images)}")
            
            if images:
                print("\n📸 Images:")
                for i, (alt, src) in enumerate(images[:5], 1):  # Show first 5
                    print(f"   {i}. Alt: '{alt[:50]}...' if len(alt) > 50 else '{alt}'")
                    print(f"      URL: {src[:80]}...")
            
            # Show preview with images
            print("\n📄 Preview (first 1000 chars):")
            print("-" * 50)
            print(markdown[:1000])
            print("-" * 50)
            
            # Save to file for inspection
            output_file = f"test_article_{article_id}.md"
            with open(output_file, 'w') as f:
                f.write(markdown)
            print(f"\n💾 Full markdown saved to: {output_file}")
    
    db.close()

def find_articles_with_images():
    """Find articles that likely have images"""
    db = SessionLocal()
    
    # Look for articles mentioning images, charts, or figures
    articles = db.query(SubstackArticle).filter(
        SubstackArticle.content_html.like('%<img%')
    ).limit(10).all()
    
    print("Articles with images in HTML:")
    for article in articles:
        # Count img tags
        import re
        img_count = len(re.findall(r'<img[^>]+>', article.content_html or ''))
        if img_count > 5:  # Has substantial images, not just tracking pixels
            print(f"  ID {article.id}: {article.title[:50]}... ({img_count} img tags)")
    
    db.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Test specific article
        test_article(int(sys.argv[1]))
    else:
        # Find articles with images
        find_articles_with_images()
        print("\nUsage: python test_image_extraction.py [article_id]")