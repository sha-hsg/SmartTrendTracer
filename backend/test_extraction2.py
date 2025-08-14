#\!/usr/bin/env python3
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import SessionLocal, SubstackArticle
from bs4 import BeautifulSoup

db = SessionLocal()
article = db.query(SubstackArticle).filter(SubstackArticle.title.like('%Claude%mouse%')).first()

if article and article.content_html:
    soup = BeautifulSoup(article.content_html, 'html.parser')
    
    # Find all paragraphs
    paragraphs = soup.find_all('p')
    print(f"Found {len(paragraphs)} paragraphs")
    
    # Show first few non-empty paragraphs
    count = 0
    for p in paragraphs:
        text = p.get_text(strip=True)
        if text and len(text) > 50:
            print(f"\nParagraph {count}: {text[:200]}...")
            count += 1
            if count >= 3:
                break
    
    # Check for content in specific styled paragraphs
    styled_ps = soup.find_all('p', style=True)
    print(f"\nFound {len(styled_ps)} styled paragraphs")
    
    for p in styled_ps[:2]:
        text = p.get_text(strip=True)
        if text and len(text) > 50:
            print(f"Styled P: {text[:150]}...")

db.close()
