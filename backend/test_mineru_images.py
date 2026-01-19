#!/usr/bin/env python3
"""
Test MinerU image extraction
"""
import requests
import sys
import os

def test_mineru_images():
    """Test if MinerU service extracts images correctly"""
    
    # Find a PDF with images to test
    pdf_path = None
    pdf_dir = "data/papers"
    
    # Look for a PDF file
    for filename in os.listdir(pdf_dir):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(pdf_dir, filename)
            break
    
    if not pdf_path:
        print("No PDF files found for testing")
        return
    
    print(f"Testing with PDF: {pdf_path}")
    print("-" * 60)
    
    # Test the MinerU service
    url = "http://localhost:8003/convert"
    
    with open(pdf_path, 'rb') as f:
        files = {'file': (os.path.basename(pdf_path), f, 'application/pdf')}
        data = {
            'output_format': 'markdown',
            'parse_tables': 'false',
            'paper_id': '999'  # Test paper ID
        }
        
        print("Sending request to MinerU service...")
        try:
            response = requests.post(url, files=files, data=data, timeout=180)
            
            if response.status_code == 200:
                result = response.json()
                print("✅ MinerU processing successful!")
                
                if result.get('success'):
                    metadata = result.get('metadata', {})
                    print(f"Images extracted: {metadata.get('images_extracted', 0)}")
                    
                    # Check for image references in content
                    content = result.get('content', '')
                    import re
                    image_refs = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', content)
                    print(f"Image references in markdown: {len(image_refs)}")
                    
                    if image_refs:
                        print("\nFirst 5 image references:")
                        for i, (alt, path) in enumerate(image_refs[:5], 1):
                            print(f"  {i}. Alt: '{alt}', Path: '{path}'")
                else:
                    print(f"❌ Processing failed: {result.get('detail', 'Unknown error')}")
            else:
                print(f"❌ HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to MinerU service")
            print("   Please start it with: cd mineru_service && ./start_mineru_service.sh")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_mineru_images()