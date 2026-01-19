#!/usr/bin/env python
"""
Debug script to examine HTML content of articles and find URL patterns
"""
import re
from bs4 import BeautifulSoup
from app.models import get_db
from app.models.substack import SubstackArticle
from sqlalchemy import or_

def analyze_html_content():
    db = next(get_db())
    
    # Get a few articles without URLs
    articles = db.query(SubstackArticle).filter(
        or_(
            SubstackArticle.deleted == False,
            SubstackArticle.deleted.is_(None)
        ),
        SubstackArticle.url.is_(None)
    ).limit(3).all()
    
    for i, article in enumerate(articles, 1):
        print(f"\n{'='*60}")
        print(f"Article {i}: {article.title[:50]}...")
        print(f"HTML Length: {len(article.content_html)}")
        print(f"Author: {article.author.name if article.author else 'Unknown'}")
        print("-"*60)
        
        # Parse HTML
        soup = BeautifulSoup(article.content_html, 'html.parser')
        
        # Look for any links
        all_links = soup.find_all('a', href=True)
        print(f"Total links found: {len(all_links)}")
        
        # Check for Substack-related links
        substack_links = []
        for link in all_links:
            href = link['href']
            if 'substack' in href.lower():
                substack_links.append(href)
        
        if substack_links:
            print(f"\nSubstack links found ({len(substack_links)}):")
            for link in substack_links[:5]:  # Show first 5
                print(f"  - {link[:100]}...")
        
        # Look for any text containing 'substack.com'
        text_content = soup.get_text()
        if 'substack.com' in text_content.lower():
            # Find context around 'substack.com'
            idx = text_content.lower().find('substack.com')
            context = text_content[max(0, idx-50):idx+100]
            print(f"\nFound 'substack.com' in text:")
            print(f"  Context: ...{context}...")
        
        # Check for View in Browser or similar patterns
        view_browser_links = []
        for link in all_links:
            text = link.get_text(strip=True).lower()
            if any(phrase in text for phrase in ['view in browser', 'read online', 'view post', 'web version']):
                view_browser_links.append((text, link['href']))
        
        if view_browser_links:
            print(f"\n'View in browser' type links found:")
            for text, href in view_browser_links[:3]:
                print(f"  - '{text}': {href[:80]}...")
        
        # Check first 1000 chars of HTML for clues
        print(f"\nFirst 500 chars of HTML:")
        print(article.content_html[:500])
    
    db.close()

if __name__ == "__main__":
    analyze_html_content()