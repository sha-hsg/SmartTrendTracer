#!/usr/bin/env python3
"""
Test MarkItDown conversion with a sample Substack article
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.document_converter import DocumentConverter
from app.models import get_db
from app.models.substack import SubstackArticle

def test_markitdown_conversion():
    """Test MarkItDown conversion with an existing Substack article"""
    
    # Get a sample article from the database
    db = next(get_db())
    article = db.query(SubstackArticle).filter(
        SubstackArticle.content_markdown.isnot(None)
    ).first()
    
    if not article:
        print("No articles found in database")
        return
    
    print(f"\n=== Testing MarkItDown conversion ===")
    print(f"Article: {article.title}")
    print(f"Author: {article.author.name}")
    print(f"Date: {article.published_at}")
    
    # Initialize converter (will use MarkItDown)
    converter = DocumentConverter()
    
    # Get original content preview
    original_preview = article.content_markdown[:500] if article.content_markdown else "No content"
    print(f"\n=== Original Content Preview (first 500 chars) ===")
    print(original_preview)
    
    # Now re-convert the HTML if we have it
    # For testing, let's create a sample HTML content
    sample_html = """
    <html>
    <body>
    <h1>Test Article Title</h1>
    <p>This is a <strong>test paragraph</strong> with some <em>italic text</em> and a <a href="https://example.com">link</a>.</p>
    
    <h2>Section with List</h2>
    <ul>
        <li>First item</li>
        <li>Second item with <code>inline code</code></li>
        <li>Third item</li>
    </ul>
    
    <blockquote>
        <p>This is a blockquote with some quoted text.</p>
    </blockquote>
    
    <pre><code>
    def hello_world():
        print("Hello, World!")
    </code></pre>
    
    <h3>Image Section</h3>
    <p><img src="https://example.com/image.jpg" alt="Example Image" /></p>
    
    <p>© 2025 Test Author. All rights reserved.</p>
    <p>Start writing on Substack</p>
    </body>
    </html>
    """
    
    print(f"\n=== Converting Sample HTML with MarkItDown ===")
    
    # Convert the HTML
    markdown_result = converter.html_to_markdown(sample_html)
    
    print(f"\n=== Converted Markdown ===")
    print(markdown_result)
    
    # Test with a real article's HTML if available
    if article.content_html:
        print(f"\n=== Converting Real Article HTML ===")
        real_markdown = converter.html_to_markdown(article.content_html)
        
        print(f"\n=== Real Article Markdown Preview (first 1000 chars) ===")
        print(real_markdown[:1000])
        
        # Compare with original stored content
        print(f"\n=== Comparison ===")
        print(f"Original content length: {len(article.content_markdown) if article.content_markdown else 0}")
        print(f"New MarkItDown content length: {len(real_markdown)}")
        
        # Save the new conversion for comparison
        output_file = f"markitdown_test_{article.id}.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(real_markdown)
        print(f"\nNew conversion saved to: {output_file}")

if __name__ == "__main__":
    test_markitdown_conversion()