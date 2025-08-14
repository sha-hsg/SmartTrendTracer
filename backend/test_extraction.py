#\!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import SessionLocal, SubstackArticle
from bs4 import BeautifulSoup

db = SessionLocal()

# Get an article with substantial HTML
article = db.query(SubstackArticle).filter(SubstackArticle.title.like('%Claude%mouse%')).first()

if article and article.content_html:
    print(f"Article: {article.title}")
    print(f"HTML length: {len(article.content_html)}")
    
    soup = BeautifulSoup(article.content_html, 'html.parser')
    
    # Find the content TD
    content_td = soup.find('td', class_='content', width='550')
    if content_td:
        print("Found content TD\!")
        text = content_td.get_text(strip=True)
        print(f"Text length: {len(text)}")
        print(f"First 500 chars: {text[:500]}")
    else:
        print("No content TD found")
        
        # Try any TD with width 550
        tds = soup.find_all('td', width='550')
        print(f"Found {len(tds)} TDs with width=550")
        
        for i, td in enumerate(tds[:3]):
            text = td.get_text(strip=True)
            if len(text) > 100:
                print(f"\nTD {i}: {len(text)} chars")
                print(f"Preview: {text[:200]}...")

db.close()
