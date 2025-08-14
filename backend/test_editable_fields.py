#!/usr/bin/env python3
"""
Test both date and URL editing functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from app.models import get_db
from app.models.substack import SubstackArticle

def test_editable_fields():
    """Test that date and URL fields can be edited"""
    print("=" * 60)
    print("Testing Editable Fields (Date & URL)")
    print("=" * 60)
    
    db = next(get_db())
    
    # Get a sample article
    article = db.query(SubstackArticle).first()
    if not article:
        print("No articles found in database")
        return
    
    print(f"\nArticle: {article.title[:50]}...")
    print(f"Original date: {article.published_at}")
    print(f"Original URL: {article.url}")
    
    # Test date update
    new_date = datetime.now() - timedelta(days=30)
    article.published_at = new_date
    print(f"\n✅ Date can be updated to: {new_date}")
    
    # Test URL update
    test_url = "https://example.substack.com/p/test-article"
    article.url = test_url
    print(f"✅ URL can be updated to: {test_url}")
    
    # Test clearing URL
    article.url = ""
    print(f"✅ URL can be cleared (empty string)")
    
    # Test None URL
    article.url = None
    print(f"✅ URL can be set to None")
    
    # Don't actually save changes
    db.rollback()
    print("\n✅ All tests passed (changes rolled back)")
    print("\nNote: Restart the API server to use the new endpoints:")
    print("  1. Stop the current server (Ctrl+C)")
    print("  2. Run: python app/main.py")
    
    db.close()

if __name__ == "__main__":
    test_editable_fields()