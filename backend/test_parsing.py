import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.collectors.gmail_substack_collector import GmailSubstackCollector
from app.models import SessionLocal, SubstackArticle

db = SessionLocal()
article = db.query(SubstackArticle).filter(SubstackArticle.id == 9).first()

if article:
    print(f"Testing article: {article.title}")
    
    collector = GmailSubstackCollector()
    result = collector._parse_substack_html(article.content_html)
    
    if result and result.get('content_markdown'):
        markdown = result['content_markdown']
        
        # Count images in markdown
        import re
        images = re.findall(r'\!\[([^\]]*)\]\(([^)]+)\)', markdown)
        
        print(f"\n✅ Found {len(images)} images in markdown")
        
        for i, (alt, url) in enumerate(images[:10], 1):
            print(f"\n{i}. Alt: '{alt}'")
            if 'substack-post-media' in url:
                print("   Type: CONTENT IMAGE")
            else:
                print("   Type: Other")
            print(f"   URL: {url[:100]}...")

db.close()
