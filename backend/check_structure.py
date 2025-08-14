import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.models import SessionLocal, SubstackArticle
from bs4 import BeautifulSoup

db = SessionLocal()
article = db.query(SubstackArticle).filter(SubstackArticle.id == 9).first()

if article:
    soup = BeautifulSoup(article.content_html, 'html.parser')
    
    # Check if images are inside table structures
    for table in soup.find_all('table', class_='image-wrapper'):
        img = table.find('img')
        if img:
            src = img.get('src', '')
            alt = img.get('alt', '')
            if 'substack-post-media' in src:
                print(f"Found content image in table:")
                print(f"  Alt: '{alt}'")
                print(f"  URL: {src[:100]}...")
                
                # Check parent structure
                parent = table.parent
                if parent:
                    print(f"  Parent tag: {parent.name}")

db.close()
