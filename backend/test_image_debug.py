#!/usr/bin/env python3
"""
Debug why images are not being preserved
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bs4 import BeautifulSoup
from trafilatura import extract

def test_image_preservation():
    """Test image preservation at each step"""
    
    test_html = """
    <html>
    <body>
    <h2>Image Section</h2>
    <p>Here's a diagram:</p>
    <img src="https://example.com/ai-diagram.png" alt="AI Architecture Diagram" />
    <p>The diagram shows the architecture.</p>
    </body>
    </html>
    """
    
    print("=== Original HTML ===")
    print(test_html)
    
    # Step 1: Check preprocessing
    from app.services.document_converter import DocumentConverter
    converter = DocumentConverter()
    
    preprocessed = converter._preprocess_html_for_media(test_html)
    print("\n=== After Preprocessing ===")
    print(preprocessed)
    
    # Step 2: Check Trafilatura extraction
    article_html = extract(
        preprocessed, 
        include_images=True,  # This should keep images
        output_format='html'
    )
    print("\n=== After Trafilatura ===")
    print(article_html)
    
    # Step 3: Check pypandoc conversion
    import pypandoc
    markdown = pypandoc.convert_text(
        article_html or preprocessed,
        'gfm',
        format='html',
        extra_args=['--wrap=none']
    )
    print("\n=== Final Markdown ===")
    print(markdown)

if __name__ == "__main__":
    test_image_preservation()