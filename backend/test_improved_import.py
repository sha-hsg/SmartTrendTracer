#!/usr/bin/env python3
"""
Test improved URL import with better formatting preservation
"""

from app.models import get_db
from app.services.url_article_importer import URLArticleImporter
from app.models.substack import SubstackArticle

def test_improved_import():
    """Test importing with improved formatting"""
    
    # First, delete the old article to test fresh import
    db = next(get_db())
    
    try:
        # Delete the existing article with bad formatting
        old_article = db.query(SubstackArticle).filter_by(id=106).first()
        if old_article:
            print(f"Deleting old article: {old_article.title}")
            db.delete(old_article)
            db.commit()
        
        # Import with improved formatting
        url = "https://magazine.sebastianraschka.com/p/llm-research-papers-2025-list-one"
        print(f"\nImporting with improved formatting: {url}")
        print("-" * 60)
        
        importer = URLArticleImporter(db)
        result = importer.import_from_url(url)
        
        if result['success']:
            print(f"✅ Import successful!")
            print(f"Article ID: {result['article_id']}")
            
            # Fetch and display the beginning of the content
            article = db.query(SubstackArticle).filter_by(id=result['article_id']).first()
            if article:
                print(f"\nFirst 1000 characters of markdown content:")
                print("-" * 60)
                print(article.content_markdown[:1000])
                print("-" * 60)
                print(f"\nTotal length: {len(article.content_markdown)} characters")
        else:
            print(f"❌ Import failed: {result['error']}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_improved_import()