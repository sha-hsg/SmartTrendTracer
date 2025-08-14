#!/usr/bin/env python3
"""
Test the enhanced document converter with better libraries
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.document_converter import DocumentConverter
from app.models import get_db
from app.models.substack import SubstackArticle


def test_html_to_markdown():
    """Test HTML to Markdown conversion"""
    converter = DocumentConverter()
    
    # Sample HTML content (typical Substack newsletter)
    html_content = """
    <div>
        <h1>AI Progress in 2025</h1>
        <p>By <strong>Test Author</strong> • January 11, 2025</p>
        
        <h2>Introduction</h2>
        <p>This is a <em>test article</em> about <code>AI progress</code>.</p>
        
        <blockquote>
            <p>"The future is already here — it's just not evenly distributed."</p>
        </blockquote>
        
        <h3>Key Points</h3>
        <ul>
            <li>First point about <a href="https://example.com">machine learning</a></li>
            <li>Second point with <code>inline code</code></li>
            <li>Third point with an image:</li>
        </ul>
        
        <img src="https://example.com/image.jpg" alt="AI Diagram" />
        
        <pre><code>def hello_world():
    print("Hello, AI World!")
    return True</code></pre>
        
        <p>© 2025 Test Author. All rights reserved.</p>
        <p>Start writing on Substack</p>
    </div>
    """
    
    # Convert to markdown
    markdown = converter.html_to_markdown(html_content)
    
    print("=" * 60)
    print("HTML TO MARKDOWN CONVERSION")
    print("=" * 60)
    print(markdown)
    print("=" * 60)
    
    # Validate the markdown
    issues = converter.validate_markdown(markdown)
    if issues:
        print("\nValidation Issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n✅ Markdown is valid!")
    
    # Extract images
    images = converter.extract_images_from_markdown(markdown)
    if images:
        print("\nExtracted Images:")
        for img in images:
            print(f"  - {img['alt']}: {img['url']}")
    
    return markdown


def test_markdown_to_pdf(markdown_text: str):
    """Test Markdown to PDF conversion"""
    converter = DocumentConverter()
    
    print("\n" + "=" * 60)
    print("MARKDOWN TO PDF CONVERSION")
    print("=" * 60)
    print(f"Using method: {converter.pdf_method}")
    
    # Metadata for the PDF
    metadata = {
        'title': 'AI Progress Report 2025',
        'author': 'Test Author',
        'date': 'January 11, 2025'
    }
    
    try:
        # Convert to PDF
        output_path = "test_output.pdf"
        pdf_bytes = converter.markdown_to_pdf(
            markdown_text,
            output_path=output_path,
            metadata=metadata
        )
        
        print(f"✅ PDF created: {output_path}")
        print(f"   Size: {len(pdf_bytes):,} bytes")
        
        # For comparison, also test with a real article if available
        test_real_article()
        
    except Exception as e:
        print(f"❌ PDF conversion failed: {e}")
        print("\nYou may need to install additional dependencies:")
        print("  - For pandoc: brew install pandoc")
        print("  - For weasyprint: brew install python-cairo pango")
        print("  - For wkhtmltopdf: brew install wkhtmltopdf")


def test_real_article():
    """Test with a real Substack article from the database"""
    converter = DocumentConverter()
    
    try:
        db = next(get_db())
        
        # Get a recent article with content
        article = db.query(SubstackArticle).filter(
            SubstackArticle.content_markdown.isnot(None)
        ).first()
        
        if article:
            print(f"\nTesting with real article: {article.title[:50]}...")
            
            # Convert to PDF
            metadata = {
                'title': article.title,
                'author': article.author.name if article.author else 'Unknown',
                'date': article.published_at.strftime('%B %d, %Y') if article.published_at else ''
            }
            
            output_path = f"article_{article.id}.pdf"
            pdf_bytes = converter.markdown_to_pdf(
                article.content_markdown,
                output_path=output_path,
                metadata=metadata
            )
            
            print(f"✅ Real article PDF created: {output_path}")
            print(f"   Size: {len(pdf_bytes):,} bytes")
        else:
            print("\nNo articles found in database for testing")
            
    except Exception as e:
        print(f"\n❌ Real article test failed: {e}")
    finally:
        db.close()


def compare_conversion_methods():
    """Compare different conversion methods"""
    print("\n" + "=" * 60)
    print("LIBRARY COMPARISON")
    print("=" * 60)
    
    html = "<h1>Test</h1><p>This is <strong>bold</strong> and <em>italic</em> text.</p>"
    
    # Test html2text (our enhanced method)
    from app.services.document_converter import DocumentConverter
    converter = DocumentConverter()
    result1 = converter.html_to_markdown(html)
    print("html2text result:")
    print(result1)
    print()
    
    # Test markdownify (current method)
    try:
        from markdownify import markdownify
        result2 = markdownify(html)
        print("markdownify result:")
        print(result2)
        print()
    except ImportError:
        print("markdownify not installed")
    
    # Test BeautifulSoup + manual conversion (basic)
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        result3 = soup.get_text()
        print("BeautifulSoup text extraction:")
        print(result3)
    except ImportError:
        print("BeautifulSoup not installed")


if __name__ == "__main__":
    print("Testing Enhanced Document Converter")
    print("=" * 60)
    
    # Test HTML to Markdown
    markdown = test_html_to_markdown()
    
    # Test Markdown to PDF
    test_markdown_to_pdf(markdown)
    
    # Compare methods
    compare_conversion_methods()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("""
Better libraries for document processing:

1. HTML to Markdown:
   - html2text (recommended) - More features, better handling
   - markdownify (current) - Simple but limited
   - BeautifulSoup + custom - Most control but more work

2. Markdown to PDF:
   - pypandoc (best) - Professional quality, requires pandoc binary
   - weasyprint (good) - Great CSS support, pure Python
   - md2pdf (simple) - Easy to use, limited features
   - reportlab (current) - Manual but flexible

3. Markdown Processing:
   - mistune - Fast and extensible
   - markdown-it-py - Feature-rich with plugins
   - python-markdown - Standard library

To install the better libraries:
pip install -r requirements_enhanced.txt

For best PDF quality, also install:
- macOS: brew install pandoc cairo pango
- Linux: apt-get install pandoc libcairo2 libpango-1.0-0
    """)