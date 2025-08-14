#!/usr/bin/env python3
"""Test PDF export functionality"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import get_db, SubstackArticle
from app.services.pdf_export_service import PDFExportService

def test_pdf_export():
    """Test PDF export for articles"""
    print("=" * 60)
    print("Testing PDF Export Functionality")
    print("=" * 60)
    
    # Get database session
    db = next(get_db())
    
    # Get a sample article
    article = db.query(SubstackArticle).first()
    
    if not article:
        print("No articles found in database. Please collect some articles first.")
        return
    
    print(f"\n1. Found article: {article.title}")
    print(f"   Author: {article.author.name if article.author else 'Unknown'}")
    print(f"   Word count: {article.word_count}")
    
    # Test single article export
    print("\n2. Testing single article PDF export...")
    pdf_service = PDFExportService(db)
    
    try:
        pdf_bytes = pdf_service.export_article_to_pdf(article.id)
        
        # Save to file for inspection
        output_file = f"test_article_{article.id}.pdf"
        with open(output_file, 'wb') as f:
            f.write(pdf_bytes)
        
        print(f"   ✅ PDF exported successfully!")
        print(f"   File size: {len(pdf_bytes):,} bytes")
        print(f"   Saved to: {output_file}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test multiple articles export
    print("\n3. Testing multiple articles PDF export...")
    articles = db.query(SubstackArticle).limit(3).all()
    
    if len(articles) >= 2:
        article_ids = [a.id for a in articles]
        try:
            pdf_bytes = pdf_service.export_multiple_articles_to_pdf(
                article_ids=article_ids,
                title="Test Collection",
                include_toc=True
            )
            
            output_file = "test_collection.pdf"
            with open(output_file, 'wb') as f:
                f.write(pdf_bytes)
            
            print(f"   ✅ Collection PDF exported successfully!")
            print(f"   Articles included: {len(articles)}")
            print(f"   File size: {len(pdf_bytes):,} bytes")
            print(f"   Saved to: {output_file}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("   Not enough articles for collection test")
    
    print("\n" + "=" * 60)
    print("PDF Export test complete!")
    print("Check the generated PDF files to verify the output.")
    print("=" * 60)

if __name__ == "__main__":
    test_pdf_export()