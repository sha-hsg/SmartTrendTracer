#!/usr/bin/env python3
"""
Test script for URL article import
"""

import sys
from app.models import get_db
from app.services.url_article_importer import URLArticleImporter

def test_import():
    """Test importing Sebastian Raschka's article"""
    
    url = "https://magazine.sebastianraschka.com/p/llm-research-papers-2025-list-one"
    print(f"Testing import of: {url}")
    print("-" * 60)
    
    db = next(get_db())
    
    try:
        importer = URLArticleImporter(db)
        result = importer.import_from_url(url)
        
        if result['success']:
            print(f"✅ SUCCESS!")
            print(f"Article ID: {result['article_id']}")
            print(f"Title: {result['title']}")
            print(f"Author: {result['author']}")
            print(f"Word Count: {result['word_count']}")
        else:
            print(f"❌ FAILED!")
            print(f"Error: {result['error']}")
            if 'article_id' in result:
                print(f"Article already exists with ID: {result['article_id']}")
                
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_import()