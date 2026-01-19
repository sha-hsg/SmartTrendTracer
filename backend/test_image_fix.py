"""
Test the image fixing on a single article first
"""

from fix_and_localize_article_images import *

# Test on one article
article = db.articles.find_one({'title': {'$regex': 'Building A GPT-Style'}})

if article:
    print(f"Testing on: {article.get('title')}")
    print(f"URL: {article.get('url')}")
    
    # Process this article
    success = process_article(article)
    
    if success:
        print("\n✅ Successfully processed!")
        
        # Check the updated article
        updated = db.articles.find_one({'_id': article['_id']})
        if updated.get('images'):
            print(f"Images metadata saved: {len(updated['images'])} images")
            for img in updated['images'][:2]:
                print(f"  - {img['filename']}: {img['size']} bytes")
    else:
        print("\n❌ Processing failed or no changes needed")
else:
    print("Article not found")