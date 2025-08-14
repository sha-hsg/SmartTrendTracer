import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.models import SessionLocal, SubstackArticle
from bs4 import BeautifulSoup

db = SessionLocal()
article = db.query(SubstackArticle).filter(SubstackArticle.id == 9).first()

if article:
    soup = BeautifulSoup(article.content_html, 'html.parser')
    
    # Find image tables (Substack's way of embedding images)
    image_tables = soup.find_all('table', class_='image-wrapper')
    print(f"Found {len(image_tables)} image wrapper tables")
    
    # Also check for direct img tags with substack-post-media
    content_images = soup.find_all('img', src=lambda x: x and 'substack-post-media' in x)
    print(f"Found {len(content_images)} content images")
    
    for i, img in enumerate(content_images[:3], 1):
        src = img.get('src', '')
        alt = img.get('alt', 'No alt text')
        print(f"\nImage {i}:")
        print(f"  Alt: {alt}")
        print(f"  URL: {src[:100]}...")

db.close()
