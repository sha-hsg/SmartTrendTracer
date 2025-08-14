#!/usr/bin/env python3
"""
Test media preservation in Trafilatura + pypandoc conversion
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.document_converter import DocumentConverter

def test_media_preservation():
    """Test that media is preserved in the correct positions"""
    
    # Initialize converter
    converter = DocumentConverter()
    
    # Test HTML with media embedded in different positions
    test_html = """
    <html>
    <body>
    <h1>Article with Embedded Media</h1>
    
    <p>This is the introduction paragraph before any media.</p>
    
    <h2>YouTube Video Section</h2>
    <p>Here's an interesting video about AI:</p>
    <iframe width="560" height="315" src="https://www.youtube.com/embed/dQw4w9WgXcQ" frameborder="0" allowfullscreen></iframe>
    <p>That video shows something important.</p>
    
    <h2>Tweet Section</h2>
    <p>Check out this tweet:</p>
    <blockquote class="twitter-tweet">
        <p>Amazing AI breakthrough!</p>
        <a href="https://twitter.com/OpenAI/status/123456789">Original tweet</a>
    </blockquote>
    <p>The tweet highlights recent developments.</p>
    
    <h2>Image Section</h2>
    <p>Here's a diagram:</p>
    <img src="https://example.com/ai-diagram.png" alt="AI Architecture Diagram" />
    <p>The diagram shows the architecture.</p>
    
    <h2>Vimeo Video</h2>
    <iframe src="https://player.vimeo.com/video/123456789" width="640" height="360" frameborder="0"></iframe>
    
    <h2>Audio Clip</h2>
    <audio controls>
        <source src="https://example.com/podcast.mp3" type="audio/mpeg">
    </audio>
    
    <h2>Generic Embed</h2>
    <iframe src="https://example.com/interactive-demo" width="800" height="600"></iframe>
    
    <h2>Conclusion</h2>
    <p>That's all the media types we support.</p>
    
    <!-- Tracking pixel that should be removed -->
    <img src="https://track.example.com/pixel.gif" width="1" height="1" />
    </body>
    </html>
    """
    
    print("=== Testing Media Preservation ===\n")
    
    # Convert the HTML
    markdown = converter.html_to_markdown(test_html)
    
    print("=== Converted Markdown ===")
    print(markdown)
    print("\n=== Analysis ===")
    
    # Check if media is preserved in correct positions
    lines = markdown.split('\n')
    media_found = {
        'youtube': False,
        'tweet': False,
        'image': False,
        'vimeo': False,
        'audio': False,
        'generic': False
    }
    
    for i, line in enumerate(lines):
        if '📹 Watch on YouTube' in line:
            media_found['youtube'] = True
            print(f"✅ YouTube video found at line {i+1}")
        if '🐦 View Tweet' in line:
            media_found['tweet'] = True
            print(f"✅ Tweet found at line {i+1}")
        if 'AI Architecture Diagram' in line:
            media_found['image'] = True
            print(f"✅ Image found at line {i+1}")
        if '📹 Watch on Vimeo' in line:
            media_found['vimeo'] = True
            print(f"✅ Vimeo video found at line {i+1}")
        if '🎵 Audio' in line:
            media_found['audio'] = True
            print(f"✅ Audio found at line {i+1}")
        if '🔗 View Embedded Content' in line:
            media_found['generic'] = True
            print(f"✅ Generic embed found at line {i+1}")
        if 'pixel.gif' in line:
            print(f"❌ Tracking pixel was not removed!")
    
    print("\n=== Summary ===")
    all_found = all(media_found.values())
    if all_found:
        print("✅ All media types preserved in correct positions!")
    else:
        print("❌ Some media types missing:")
        for media_type, found in media_found.items():
            if not found:
                print(f"  - {media_type}")

if __name__ == "__main__":
    test_media_preservation()