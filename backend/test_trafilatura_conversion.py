#!/usr/bin/env python3
"""
Test Trafilatura + pypandoc conversion with a sample Substack article
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.document_converter import DocumentConverter
from app.models import get_db
from app.models.substack import SubstackArticle

def test_trafilatura_conversion():
    """Test Trafilatura + pypandoc conversion with an existing Substack article"""
    
    # Get a sample article from the database
    db = next(get_db())
    article = db.query(SubstackArticle).filter(
        SubstackArticle.content_markdown.isnot(None)
    ).first()
    
    if not article:
        print("No articles found in database")
        return
    
    print(f"\n=== Testing Trafilatura + pypandoc conversion ===")
    print(f"Article: {article.title}")
    print(f"Author: {article.author.name}")
    print(f"Date: {article.published_at}")
    
    # Initialize converter (will use Trafilatura + pypandoc)
    converter = DocumentConverter()
    
    # Test with a sample HTML that includes media
    sample_html_with_media = """
    <html>
    <body>
    <h1>Test Article with Media</h1>
    <p>This is a <strong>test paragraph</strong> with some <em>italic text</em> and a <a href="https://example.com">link</a>.</p>
    
    <h2>Embedded Video</h2>
    <iframe width="560" height="315" src="https://www.youtube.com/embed/dQw4w9WgXcQ" frameborder="0" allowfullscreen></iframe>
    
    <h2>Tweet Embed</h2>
    <blockquote class="twitter-tweet">
        <p>Test tweet content</p>
        <a href="https://twitter.com/user/status/123456789">Tweet link</a>
    </blockquote>
    
    <h2>Code Section</h2>
    <pre><code class="language-python">
def hello_world():
    print("Hello, World!")
    return 42
    </code></pre>
    
    <h3>Image Section</h3>
    <p><img src="https://example.com/image.jpg" alt="Example Image" /></p>
    
    <h2>Table Example</h2>
    <table>
        <thead>
            <tr>
                <th>Name</th>
                <th>Value</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Item 1</td>
                <td>100</td>
            </tr>
            <tr>
                <td>Item 2</td>
                <td>200</td>
            </tr>
        </tbody>
    </table>
    
    <p>© 2025 Test Author. All rights reserved.</p>
    <p>Start writing on Substack</p>
    </body>
    </html>
    """
    
    print(f"\n=== Converting Sample HTML with Media ===")
    
    # Convert the HTML
    markdown_result = converter.html_to_markdown(sample_html_with_media)
    
    print(f"\n=== Converted Markdown ===")
    print(markdown_result)
    
    # Test with a real article's HTML if available
    if article.content_html:
        print(f"\n=== Converting Real Article HTML ===")
        real_markdown = converter.html_to_markdown(article.content_html)
        
        print(f"\n=== Real Article Markdown Preview (first 1500 chars) ===")
        print(real_markdown[:1500])
        
        # Compare with original stored content
        print(f"\n=== Comparison ===")
        print(f"Original content length: {len(article.content_markdown) if article.content_markdown else 0}")
        print(f"New Trafilatura+pypandoc content length: {len(real_markdown)}")
        
        # Check for media extraction
        if "Embedded Media" in real_markdown:
            print("✅ Media links extracted and preserved")
        
        # Save the new conversion for comparison
        output_file = f"trafilatura_test_{article.id}.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(real_markdown)
        print(f"\nNew conversion saved to: {output_file}")
        
        # Also save original for comparison
        original_file = f"original_{article.id}.md"
        with open(original_file, 'w', encoding='utf-8') as f:
            f.write(article.content_markdown or "")
        print(f"Original content saved to: {original_file}")

if __name__ == "__main__":
    test_trafilatura_conversion()