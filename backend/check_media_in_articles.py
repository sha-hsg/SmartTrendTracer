#!/usr/bin/env python3
"""
Check if articles have embedded media and test conversion
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db
from app.models.substack import SubstackArticle
from app.services.document_converter import DocumentConverter
from bs4 import BeautifulSoup

def check_media_in_articles():
    """Check for media in articles and test conversion"""
    
    db = next(get_db())
    converter = DocumentConverter()
    
    # Get articles with potential media
    articles = db.query(SubstackArticle).filter(
        SubstackArticle.content_html.isnot(None)
    ).limit(5).all()
    
    print("=== Checking for Media in Articles ===\n")
    
    for article in articles:
        print(f"\n{'='*60}")
        print(f"Article: {article.title[:50]}...")
        print(f"Author: {article.author.name}")
        
        # Parse HTML to look for media
        soup = BeautifulSoup(article.content_html, 'html.parser')
        
        # Check for different media types
        iframes = soup.find_all('iframe')
        videos = soup.find_all('video')
        tweets = soup.find_all('blockquote', class_='twitter-tweet')
        
        print(f"\nMedia found in HTML:")
        print(f"  - Iframes: {len(iframes)}")
        print(f"  - Videos: {len(videos)}")
        print(f"  - Tweets: {len(tweets)}")
        
        if iframes:
            for i, iframe in enumerate(iframes[:2], 1):
                src = iframe.get('src', 'No src')
                print(f"    Iframe {i}: {src[:80]}...")
        
        if videos:
            for i, video in enumerate(videos[:2], 1):
                src = video.get('src', 'No src')
                print(f"    Video {i}: {src[:80]}...")
        
        # Now convert and check if media is preserved
        if iframes or videos or tweets:
            print(f"\nConverting article with media...")
            new_markdown = converter.html_to_markdown(article.content_html)
            
            # Check for media links in markdown
            if '📹' in new_markdown:
                print("  ✅ Video links found in markdown")
            if '🐦' in new_markdown:
                print("  ✅ Tweet links found in markdown")
            if '🔗' in new_markdown:
                print("  ✅ Embedded content links found in markdown")
            if '[Watch' in new_markdown or '[View' in new_markdown:
                print("  ✅ Media links with descriptive text found")
            
            # Show a sample of the converted content with media
            lines = new_markdown.split('\n')
            for i, line in enumerate(lines):
                if any(x in line for x in ['📹', '🐦', '🔗', '[Watch', '[View']):
                    print(f"\n  Line {i+1}: {line[:100]}...")
                    
            # Check if current content has media links
            current_has_media = any(x in article.content_markdown for x in ['📹', '🐦', '🔗', '[Watch', '[View'])
            if not current_has_media:
                print(f"\n  ⚠️ Current markdown doesn't have media links - needs update!")
    
    db.close()

if __name__ == "__main__":
    check_media_in_articles()