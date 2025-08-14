#!/usr/bin/env python3
"""
Test MarkItDown conversion directly with HTML content
"""
from markitdown import MarkItDown
from io import BytesIO

def test_markitdown_direct():
    """Test MarkItDown with direct HTML content"""
    
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
    
    # Initialize MarkItDown
    markitdown = MarkItDown()
    
    # Try converting from a BytesIO stream
    stream = BytesIO(sample_html.encode('utf-8'))
    result = markitdown.convert_stream(stream, file_extension='.html')
    
    print("=== MarkItDown Direct Conversion ===")
    print(result.text_content)
    
    # Also test if we can use markdownify directly
    try:
        import markdownify
        
        # Configure markdownify for better output
        markdown_text = markdownify.markdownify(
            sample_html,
            heading_style="ATX",  # Use # style headings
            bullets="*-+",  # Bullet characters for lists
            strong_em_symbol="*",  # Use * for bold/emphasis
            strip=['script', 'style', 'meta', 'link', 'noscript'],
            wrap=False,  # Don't wrap lines
            escape_asterisks=False,
            escape_underscores=False,
            escape_misc=False,
            default_title=True,
            exclude_styles=True,
        )
        
        print("\n=== Markdownify Direct Conversion ===")
        print(markdown_text)
        
    except ImportError:
        print("Markdownify not available")

if __name__ == "__main__":
    test_markitdown_direct()