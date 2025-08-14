#!/usr/bin/env python3
"""
Update Substack article URLs based on subdomain and article titles
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db
from app.models.substack import SubstackArticle, SubstackAuthor
import re
from datetime import datetime

def generate_slug(title):
    """Generate a URL slug from a title"""
    # Convert to lowercase
    slug = title.lower()
    # Replace special characters with hyphens
    slug = re.sub(r'[^\w\s-]', '', slug)
    # Replace spaces with hyphens
    slug = re.sub(r'[-\s]+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    # Limit length
    if len(slug) > 50:
        slug = slug[:50].rsplit('-', 1)[0]
    return slug

def update_article_urls():
    """Update article URLs using subdomain and title-based slugs"""
    
    print("=== Updating Substack Article URLs ===")
    print(f"Time: {datetime.now()}")
    
    db = next(get_db())
    
    try:
        # Get all articles with their authors
        articles = db.query(SubstackArticle).join(SubstackAuthor).all()
        
        updated_count = 0
        skipped_count = 0
        
        for article in articles:
            if article.url:
                skipped_count += 1
                continue
            
            # Generate URL based on subdomain and slug
            if article.author.subdomain:
                # Generate slug from title
                slug = generate_slug(article.title)
                
                # Construct the URL
                # Format: https://subdomain.substack.com/p/slug
                article.url = f"https://{article.author.subdomain}.substack.com/p/{slug}"
                article.slug = slug
                
                updated_count += 1
                print(f"✅ Updated: {article.title[:50]}...")
                print(f"   URL: {article.url}")
            else:
                print(f"⚠️  No subdomain for: {article.title[:50]}...")
        
        # Commit changes
        db.commit()
        
        print(f"\n=== Summary ===")
        print(f"Total articles: {len(articles)}")
        print(f"✅ Updated: {updated_count}")
        print(f"⏭️  Skipped (already had URL): {skipped_count}")
        print(f"❌ Failed: {len(articles) - updated_count - skipped_count}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()
        print(f"\nCompleted at: {datetime.now()}")

if __name__ == "__main__":
    update_article_urls()