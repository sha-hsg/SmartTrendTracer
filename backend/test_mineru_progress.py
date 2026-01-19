#!/usr/bin/env python3
"""Test script to verify MinerU progress reporting with callbacks"""

import requests
import time
import json
from pathlib import Path

def test_mineru_progress():
    """Test MinerU progress reporting by processing a PDF"""
    
    # Test configuration
    MINERU_URL = "http://localhost:8003"
    TEST_PDF = "data/papers/20250825_095946_cc8127cf_test.pdf"
    PAPER_ID = 4245617126  # Integer ID for file storage
    MONGO_ID = "68ab70fe3e0caac2fd0ef9e6"  # MongoDB ID for callback URL
    
    # Check if MinerU service is running
    try:
        health = requests.get(f"{MINERU_URL}/health", timeout=2)
        if health.status_code != 200:
            print("❌ MinerU service is not running!")
            print("Start it with: cd mineru_service && python mineru_server.py")
            return
        print("✅ MinerU service is healthy")
    except:
        print("❌ Cannot connect to MinerU service at", MINERU_URL)
        return
    
    # Check if test PDF exists
    pdf_path = Path(TEST_PDF)
    if not pdf_path.exists():
        print(f"❌ Test PDF not found: {TEST_PDF}")
        print("Using first available PDF...")
        pdfs = list(Path("data/papers").glob("*.pdf"))
        if not pdfs:
            print("❌ No PDFs found in data/papers/")
            return
        pdf_path = pdfs[0]
        print(f"📄 Using: {pdf_path}")
    
    # Process the PDF with callback URL
    print("\n📤 Sending PDF to MinerU with progress callback...")
    print(f"   Paper ID: {PAPER_ID} (for file storage)")
    print(f"   MongoDB ID: {MONGO_ID} (for callback URL)")
    
    with open(pdf_path, 'rb') as f:
        files = {'file': (pdf_path.name, f, 'application/pdf')}
        data = {
            'parse_tables': 'false',
            'output_format': 'markdown',
            'paper_id': str(PAPER_ID),
            'callback_url': f'http://localhost:8000/api/papers/{MONGO_ID}/progress-callback'
        }
        
        print("\n⏳ Processing (this may take a while)...")
        print("   Progress callbacks should be sent to the API endpoint")
        print("   Check the MinerU server logs for progress updates\n")
        
        try:
            response = requests.post(
                f"{MINERU_URL}/convert",
                files=files,
                data=data,
                timeout=300
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Processing complete!")
                print(f"   Success: {result.get('success', False)}")
                print(f"   Images extracted: {result.get('metadata', {}).get('images_extracted', 0)}")
                print(f"   Content length: {len(result.get('content', ''))}")
                
                # Check if images were saved
                if result.get('metadata', {}).get('images_extracted', 0) > 0:
                    image_dir = Path(f"data/paper_repository/{PAPER_ID}/images")
                    if image_dir.exists():
                        images = list(image_dir.rglob("*"))
                        print(f"   Images saved: {len(images)} files in {image_dir}")
                    else:
                        print(f"   ⚠️ Image directory not found: {image_dir}")
                
            else:
                print(f"❌ Processing failed with status {response.status_code}")
                print(f"   Error: {response.text[:500]}")
                
        except requests.exceptions.Timeout:
            print("❌ Request timed out after 300 seconds")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("MinerU Progress Reporting Test")
    print("=" * 50)
    test_mineru_progress()