import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.models import SessionLocal, SubstackArticle
from bs4 import BeautifulSoup

db = SessionLocal()
article = db.query(SubstackArticle).filter(SubstackArticle.id == 9).first()

if article:
    soup = BeautifulSoup(article.content_html, 'html.parser')
    
    # Find ALL images
    all_images = soup.find_all('img')
    print(f"Total images: {len(all_images)}")
    
    # Categorize them
    for i, img in enumerate(all_images, 1):
        src = img.get('src', '')
        alt = img.get('alt', '')
        width = img.get('width', '')
        height = img.get('height', '')
        
        # Check if it's a content image
        is_content = 'substack-post-media' in src and 'substackcdn.com/image/fetch' in src
        is_small = width and height and int(width) <= 50 and int(height) <= 50
        
        if is_content:
            print(f"\n✅ CONTENT Image {i}:")
            print(f"   Alt: '{alt}'")
            print(f"   Size: {width}x{height}")
            print(f"   URL: {src[:100]}...")
        elif is_small:
            print(f"\n❌ SMALL Image {i}: {width}x{height}")
        elif 'open?token=' in src:
            print(f"\n❌ TRACKING Image {i}")
        else:
            print(f"\n⚠️  OTHER Image {i}:")
            print(f"   Alt: '{alt}'")
            print(f"   Size: {width}x{height}")
            print(f"   URL: {src[:80]}...")

db.close()
