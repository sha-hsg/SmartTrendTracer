#!/usr/bin/env python3
"""Test PDF processor availability and functionality"""

from app.services.pdf_processor_service import PDFProcessorService
import sys
import os

def test_processors():
    """Test PDF processor availability"""
    print("="*60)
    print("🔍 PDF PROCESSOR TEST")
    print("="*60)
    
    # Initialize the service
    service = PDFProcessorService()
    
    print("\n📊 Processor Availability:")
    print(f"  ⭐ Marker: {service.marker_available}")
    print(f"  ⛏️  MinerU: {service.mineru_available}")
    print(f"  🍫 Nougat: {service.nougat_available}")
    print(f"  🖼️  Pix2Text: {service.pix2text_available}")
    print(f"  📄 Basic (pypdfium2): {service.fallback_available}")
    print("="*60)
    
    # Test with a PDF if available
    pdf_path = "documents/Schmidgall et al. - 2025 - Agent Laboratory Using LLM Agents as Research Assistants.pdf"
    
    if os.path.exists(pdf_path):
        print(f"\n📄 Testing with: {os.path.basename(pdf_path)}")
        print("="*60)
        
        # Process the PDF
        result = service.process_pdf(pdf_path, prefer_method="auto")
        
        print("\n📊 Processing Results:")
        print(f"  ✅ Success: {result['success']}")
        print(f"  🔧 Method used: {result.get('method_used', 'None')}")
        print(f"  ⏱️  Processing time: {result.get('processing_time', 0):.2f} seconds")
        print(f"  📝 Content length: {len(result.get('markdown', ''))} characters")
        
        if result.get('error'):
            print(f"  ❌ Error: {result['error'][:200]}")
        
        # Show first 500 characters of content
        if result.get('markdown'):
            print("\n📝 First 500 characters of extracted content:")
            print("-"*40)
            print(result['markdown'][:500])
            print("-"*40)
    else:
        print(f"\n⚠️  Test PDF not found: {pdf_path}")
    
    print("\n✅ Test complete!")

if __name__ == "__main__":
    test_processors()
