#!/usr/bin/env python3
"""Test that ArXiv import saves PDFs to permanent directory"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.arxiv_import_service import ArXivImportService

def test_arxiv_import():
    """Test ArXiv import saves to correct directory"""
    
    # Initialize service
    service = ArXivImportService()
    
    # Test paper (a small one for quick download)
    test_arxiv_id = "2301.00001"  # Small paper
    
    print(f"Testing ArXiv import for paper: {test_arxiv_id}")
    print("-" * 50)
    
    # Test 1: Download without specifying directory (should use data/papers)
    print("\nTest 1: Download without directory specification")
    pdf_path = service.download_pdf(test_arxiv_id)
    
    if pdf_path:
        print(f"✅ PDF downloaded to: {pdf_path}")
        path_obj = Path(pdf_path)
        
        # Check it's in the right place
        if "data/papers" in str(path_obj):
            print("✅ PDF saved to permanent data/papers directory")
        else:
            print(f"❌ PDF saved to wrong location: {path_obj.parent}")
        
        # Check file exists and has content
        if path_obj.exists():
            size = path_obj.stat().st_size
            print(f"✅ PDF exists with size: {size:,} bytes")
        else:
            print("❌ PDF file doesn't exist")
            
        # Clean up test file
        if path_obj.exists():
            path_obj.unlink()
            print("🧹 Cleaned up test file")
    else:
        print("❌ Failed to download PDF")
    
    # Test 2: Download with explicit directory
    print("\nTest 2: Download with explicit arxiv directory")
    arxiv_dir = Path("data/papers/arxiv")
    arxiv_dir.mkdir(parents=True, exist_ok=True)
    
    pdf_path = service.download_pdf(test_arxiv_id, str(arxiv_dir))
    
    if pdf_path:
        print(f"✅ PDF downloaded to: {pdf_path}")
        path_obj = Path(pdf_path)
        
        # Check it's in the arxiv subdirectory
        if "data/papers/arxiv" in str(path_obj):
            print("✅ PDF saved to arxiv subdirectory")
        else:
            print(f"❌ PDF saved to wrong location: {path_obj.parent}")
            
        # Clean up
        if path_obj.exists():
            path_obj.unlink()
            print("🧹 Cleaned up test file")
    else:
        print("❌ Failed to download PDF")
    
    # Test 3: Full import_paper method
    print("\nTest 3: Full import_paper method")
    result = service.import_paper(test_arxiv_id, download_dir=str(arxiv_dir))
    
    if result['success']:
        print(f"✅ Import successful")
        print(f"   Title: {result['metadata']['title'][:60]}...")
        print(f"   PDF Path: {result['pdf_path']}")
        
        pdf_path = Path(result['pdf_path'])
        if pdf_path.exists():
            print(f"✅ PDF file exists at: {pdf_path}")
            if "data/papers/arxiv" in str(pdf_path):
                print("✅ PDF in correct permanent location")
            else:
                print(f"❌ PDF in wrong location: {pdf_path.parent}")
            
            # Clean up
            pdf_path.unlink()
            print("🧹 Cleaned up test file")
        else:
            print("❌ PDF file doesn't exist")
    else:
        print(f"❌ Import failed: {result.get('error')}")
    
    print("\n" + "=" * 50)
    print("Test complete!")

if __name__ == "__main__":
    test_arxiv_import()