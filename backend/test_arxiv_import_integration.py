#!/usr/bin/env python3
"""
Integration test for ArXiv import functionality
Tests the complete import flow with both URL types
"""

import requests
import json
import time

def test_arxiv_import(url_or_id, description):
    """Test importing a paper from ArXiv"""
    
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"Input: {url_or_id}")
    print('='*60)
    
    # First validate the ID
    validation_url = f"http://localhost:8000/api/arxiv/validate/{url_or_id}"
    try:
        response = requests.get(validation_url)
        if response.status_code == 200:
            data = response.json()
            if data.get('valid'):
                print(f"✅ Validation successful")
                print(f"   ArXiv ID: {data.get('arxiv_id')}")
                print(f"   Title: {data.get('title', 'N/A')[:60]}...")
            else:
                print(f"❌ Validation failed: {data.get('error')}")
                return False
        else:
            print(f"❌ Validation request failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Validation error: {e}")
        print("   Note: Make sure the API server is running (python app/main.py)")
        return False
    
    # Now import the paper
    import_url = "http://localhost:8000/api/arxiv/import"
    payload = {
        "url_or_id": url_or_id,
        "process_pdf": False,  # Don't auto-process
        "add_to_database": False  # Don't add to DB for this test
    }
    
    print(f"\n📥 Importing paper...")
    try:
        response = requests.post(import_url, json=payload)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Import successful!")
                print(f"   Title: {data.get('title', 'N/A')[:60]}...")
                print(f"   Authors: {', '.join((data.get('authors', []))[:3])}")
                if len(data.get('authors', [])) > 3:
                    print(f"            +{len(data['authors']) - 3} more")
                print(f"   ArXiv ID: {data.get('arxiv_id')}")
                print(f"   PDF saved: {data.get('pdf_path', 'N/A')}")
                return True
            else:
                print(f"❌ Import failed: {data.get('error')}")
                return False
        else:
            print(f"❌ Import request failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Import error: {e}")
        print("   Note: Make sure the API server is running (python app/main.py)")
        return False

def main():
    """Run integration tests"""
    
    print("\n" + "="*60)
    print(" ArXiv Import Integration Test")
    print(" Testing the complete import flow")
    print("="*60)
    
    # Check if API is running
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("\n✅ API server is running")
            health = response.json()
            print(f"   Database: {health.get('database', 'Unknown')}")
            print(f"   Status: {health.get('status', 'Unknown')}")
        else:
            print("\n⚠️  API server returned unexpected status")
    except:
        print("\n❌ API server is not running!")
        print("   Please start it with: cd backend && python app/main.py")
        return 1
    
    # Test cases
    test_cases = [
        ("2508.17669", "Direct ArXiv ID"),
        ("https://arxiv.org/abs/2508.17669", "Abstract URL"),
        ("https://arxiv.org/pdf/2508.17669", "PDF URL"),
        ("arxiv.org/abs/2508.17669", "URL without protocol"),
    ]
    
    results = []
    for url_or_id, description in test_cases:
        success = test_arxiv_import(url_or_id, description)
        results.append((description, success))
        time.sleep(1)  # Be nice to the ArXiv API
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    for description, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {description}")
    
    all_passed = all(success for _, success in results)
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL INTEGRATION TESTS PASSED!")
        print("\nThe ArXiv import system successfully handles:")
        print("• Direct ArXiv IDs (e.g., 2508.17669)")
        print("• Abstract URLs (e.g., https://arxiv.org/abs/2508.17669)")
        print("• PDF URLs (e.g., https://arxiv.org/pdf/2508.17669)")
    else:
        print("❌ SOME TESTS FAILED")
        print("Please check the error messages above.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())