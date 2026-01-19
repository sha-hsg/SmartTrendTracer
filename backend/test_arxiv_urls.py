#!/usr/bin/env python3
"""
Test ArXiv import with different URL formats
Tests that both abstract and PDF URLs are properly handled
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.arxiv_import_service import ArXivImportService
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_arxiv_url_extraction():
    """Test that we can extract ArXiv IDs from various URL formats"""
    
    print("\n" + "="*60)
    print("Testing ArXiv URL/ID Extraction")
    print("="*60)
    
    service = ArXivImportService()
    
    # Test cases with the requested paper ID
    test_cases = [
        # Direct IDs
        ("2508.17669", "Direct ID (new format)"),
        ("2508.17669v2", "Direct ID with version"),
        ("cs.AI/0701123", "Direct ID (old format)"),
        
        # Abstract URLs
        ("https://arxiv.org/abs/2508.17669", "Abstract URL"),
        ("http://arxiv.org/abs/2508.17669", "Abstract URL (http)"),
        ("arxiv.org/abs/2508.17669", "Abstract URL (no protocol)"),
        ("https://arxiv.org/abs/2508.17669v3", "Abstract URL with version"),
        
        # PDF URLs
        ("https://arxiv.org/pdf/2508.17669", "PDF URL"),
        ("http://arxiv.org/pdf/2508.17669", "PDF URL (http)"),
        ("arxiv.org/pdf/2508.17669", "PDF URL (no protocol)"),
        ("https://arxiv.org/pdf/2508.17669v2", "PDF URL with version"),
        
        # Old format URLs
        ("https://arxiv.org/abs/cs.AI/0701123", "Old format abstract URL"),
        ("https://arxiv.org/pdf/cs.AI/0701123", "Old format PDF URL"),
        
        # Invalid formats (should return None)
        ("not-an-arxiv-id", "Invalid format"),
        ("https://example.com/2508.17669", "Wrong domain"),
        ("2508", "Incomplete ID"),
    ]
    
    results = []
    for url_or_id, description in test_cases:
        extracted_id = service.extract_arxiv_id(url_or_id)
        status = "✅" if extracted_id else "❌"
        
        results.append({
            'input': url_or_id,
            'description': description,
            'extracted_id': extracted_id,
            'status': status
        })
        
        print(f"\n{status} {description}")
        print(f"   Input:     {url_or_id}")
        print(f"   Extracted: {extracted_id}")
    
    # Summary
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    
    successful = [r for r in results if r['status'] == "✅"]
    failed = [r for r in results if r['status'] == "❌"]
    
    print(f"✅ Successful extractions: {len(successful)}/{len(results)}")
    print(f"❌ Failed extractions: {len(failed)}/{len(results)}")
    
    # Check that both requested URLs work
    abstract_url_works = any(r['input'] == "https://arxiv.org/abs/2508.17669" and r['extracted_id'] == "2508.17669" for r in results)
    pdf_url_works = any(r['input'] == "https://arxiv.org/pdf/2508.17669" and r['extracted_id'] == "2508.17669" for r in results)
    
    print("\n" + "="*60)
    print("Requested URL Support")
    print("="*60)
    print(f"Abstract URL (https://arxiv.org/abs/2508.17669): {'✅ SUPPORTED' if abstract_url_works else '❌ NOT SUPPORTED'}")
    print(f"PDF URL (https://arxiv.org/pdf/2508.17669):      {'✅ SUPPORTED' if pdf_url_works else '❌ NOT SUPPORTED'}")
    
    return abstract_url_works and pdf_url_works

def test_metadata_fetch():
    """Test fetching metadata for a specific paper"""
    
    print("\n" + "="*60)
    print("Testing Metadata Fetch")
    print("="*60)
    
    service = ArXivImportService()
    
    # Test with the requested paper
    arxiv_id = "2508.17669"
    print(f"\nFetching metadata for ArXiv ID: {arxiv_id}")
    
    metadata = service.fetch_metadata(arxiv_id)
    
    if metadata:
        print("✅ Successfully fetched metadata:")
        print(f"   Title:    {metadata.get('title', 'N/A')[:80]}...")
        print(f"   Authors:  {', '.join(metadata.get('authors', [])[:3])}")
        if len(metadata.get('authors', [])) > 3:
            print(f"             +{len(metadata['authors']) - 3} more authors")
        print(f"   Abstract: {metadata.get('abstract', 'N/A')[:100]}...")
        print(f"   PDF URL:  {metadata.get('pdf_url', 'N/A')}")
        print(f"   Categories: {', '.join(metadata.get('categories', []))}")
        return True
    else:
        print("❌ Failed to fetch metadata")
        return False

def main():
    """Run all tests"""
    
    print("\n" + "="*60)
    print(" ArXiv Import URL Support Test")
    print(" Testing both abstract and PDF URL formats")
    print("="*60)
    
    # Test URL extraction
    url_test_passed = test_arxiv_url_extraction()
    
    # Test metadata fetching
    metadata_test_passed = test_metadata_fetch()
    
    # Final summary
    print("\n" + "="*60)
    print("Final Results")
    print("="*60)
    
    if url_test_passed and metadata_test_passed:
        print("✅ ALL TESTS PASSED")
        print("Both abstract URLs and PDF URLs are properly supported!")
    else:
        print("❌ SOME TESTS FAILED")
        if not url_test_passed:
            print("   - URL extraction needs fixing")
        if not metadata_test_passed:
            print("   - Metadata fetching needs fixing")
    
    return 0 if (url_test_passed and metadata_test_passed) else 1

if __name__ == "__main__":
    sys.exit(main())