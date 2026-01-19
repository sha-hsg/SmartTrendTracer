#!/usr/bin/env python3
"""
Detailed test of MinerU service image extraction
"""
import requests
import json
import re

def test_mineru_service():
    """Test MinerU service with detailed output"""
    
    # Use a specific PDF that should have images
    pdf_path = "data/papers/20250820_210655_063c556c_2025.acl-long.423.pdf"
    
    print("=" * 60)
    print("TESTING MINERU SERVICE IMAGE EXTRACTION")
    print("=" * 60)
    print(f"PDF: {pdf_path}")
    
    url = "http://localhost:8003/convert"
    
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': ('test.pdf', f, 'application/pdf')}
            data = {
                'output_format': 'markdown',
                'parse_tables': 'false',
                'paper_id': '999'
            }
            
            print("\nSending request to MinerU service...")
            response = requests.post(url, files=files, data=data, timeout=300)
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"✅ Success: {result.get('success')}")
                
                # Check metadata
                metadata = result.get('metadata', {})
                print(f"\nMetadata:")
                print(f"  - Images extracted: {metadata.get('images_extracted', 0)}")
                print(f"  - Page count: {metadata.get('page_count', 'N/A')}")
                print(f"  - Processor: {metadata.get('processor', 'N/A')}")
                
                # Check content for image references
                content = result.get('content', '')
                
                # Find all image references
                img_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
                images = re.findall(img_pattern, content)
                
                print(f"\nImage references in markdown: {len(images)}")
                if images:
                    print("\nFirst 10 image references:")
                    for i, (alt, path) in enumerate(images[:10], 1):
                        alt_preview = alt[:50] + "..." if len(alt) > 50 else alt
                        print(f"  {i}. Alt: '{alt_preview}'")
                        print(f"     Path: {path}")
                
                # Check if paths were updated
                api_paths = [path for alt, path in images if path.startswith('/api/papers/')]
                print(f"\nProcessed API paths: {len(api_paths)}")
                if api_paths:
                    print("Sample API paths:")
                    for path in api_paths[:5]:
                        print(f"  - {path}")
                
                # Save the markdown for inspection
                with open('/tmp/mineru_test_output.md', 'w') as f:
                    f.write(content)
                print("\n✅ Saved markdown to /tmp/mineru_test_output.md")
                
            else:
                print(f"❌ Error {response.status_code}: {response.text[:500]}")
                
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_mineru_service()