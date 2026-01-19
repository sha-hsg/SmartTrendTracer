#!/usr/bin/env python3
"""
Test that the Marker service works correctly after CLI command fix
"""
import requests
import time
import sys
import os

def test_marker_service():
    """Test the Marker service with a sample PDF"""
    
    # Check if service is running
    try:
        health_response = requests.get("http://localhost:8002/health")
        if health_response.status_code != 200:
            print("❌ Marker service is not healthy")
            return False
        print("✅ Marker service is healthy")
    except:
        print("❌ Marker service is not running on port 8002")
        print("   Please start it with: ./start_marker_service.sh")
        return False
    
    # Find a test PDF
    test_pdfs = [
        "documents/paper.pdf",
        "data/papers/arxiv/2408.09869v1.pdf",
        "data/paper_repository/00/00/01/paper.pdf",
        "data/paper_repository/00/00/02/paper.pdf",
    ]
    
    pdf_path = None
    for path in test_pdfs:
        if os.path.exists(path):
            pdf_path = path
            break
    
    if not pdf_path:
        print("❌ No test PDF found")
        return False
    
    print(f"📄 Using test PDF: {pdf_path}")
    
    # Test conversion
    print("🔄 Testing PDF conversion...")
    
    with open(pdf_path, "rb") as f:
        files = {"file": ("test.pdf", f, "application/pdf")}
        data = {"paper_id": "1"}  # Enable image persistence
        
        start_time = time.time()
        response = requests.post(
            "http://localhost:8002/convert",
            files=files,
            data=data,
            timeout=300  # 5 minutes timeout
        )
        elapsed = time.time() - start_time
    
    if response.status_code != 200:
        print(f"❌ Conversion failed with status {response.status_code}")
        print(f"   Error: {response.text}")
        return False
    
    result = response.json()
    
    # Check results
    print(f"✅ Conversion successful in {elapsed:.1f} seconds")
    print(f"   Success: {result.get('success')}")
    print(f"   Method: {result.get('method_used', 'unknown')}")
    print(f"   Markdown length: {len(result.get('content', ''))} characters")
    print(f"   Images extracted: {result.get('images_extracted', 0)}")
    print(f"   Processing time: {result.get('processing_time', 0):.2f}s")
    
    # Check if markdown has content
    if not result.get('content'):
        print("⚠️  Warning: No markdown content extracted")
    
    # Show a sample of the content
    content = result.get('content', '')
    if content:
        lines = content.split('\n')[:10]
        print("\n📝 First 10 lines of extracted content:")
        print("   " + "\n   ".join(lines))
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("Marker Service Test (After CLI Fix)")
    print("=" * 60)
    
    success = test_marker_service()
    
    print("=" * 60)
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Tests failed - please check the errors above")
        sys.exit(1)