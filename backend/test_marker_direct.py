#!/usr/bin/env python3
"""
Direct test of Marker service at port 8002
Tests PDF processing with image extraction
"""
import requests
import time
import os
import re
import tempfile
import shutil
from pathlib import Path

def download_arxiv_pdf(arxiv_id: str) -> str:
    """Download PDF from ArXiv"""
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix="marker_test_")
    pdf_path = os.path.join(temp_dir, f"arxiv_{arxiv_id.replace('/', '_')}.pdf")
    
    print(f"Downloading PDF from {pdf_url}...")
    response = requests.get(pdf_url, stream=True)
    if response.status_code == 200:
        with open(pdf_path, 'wb') as f:
            shutil.copyfileobj(response.raw, f)
        print(f"✅ Downloaded to: {pdf_path}")
        print(f"   Size: {os.path.getsize(pdf_path):,} bytes")
        return pdf_path
    else:
        print(f"❌ Failed to download: {response.status_code}")
        return None

def test_marker_service_directly():
    """Test Marker service directly with detailed reporting"""
    
    # Initialize safe defaults
    content = ""
    image_refs, api_refs, local_refs = [], [], []
    
    # Test with Attention Is All You Need (has architecture diagrams)
    arxiv_id = "1706.03762"
    
    print("=" * 60)
    print("DIRECT MARKER SERVICE TEST")
    print("=" * 60)
    print(f"ArXiv ID: {arxiv_id}")
    print("Paper: 'Attention Is All You Need' (Transformer paper)")
    print("Expected: Multiple architecture diagrams and figures")
    print("-" * 60)
    
    # Step 1: Check Marker service health
    print("\n1. CHECKING MARKER SERVICE...")
    try:
        health = requests.get("http://localhost:8002/health", timeout=2)
        if health.status_code == 200:
            health_data = health.json()
            print(f"✅ Marker service is {health_data.get('status', 'unknown')}")
            print(f"   Marker: {health_data.get('marker', 'unknown')}")
        else:
            print(f"❌ Marker service returned: {health.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to Marker service: {e}")
        return
    
    # Check LLM configuration
    try:
        llm_health = requests.get("http://localhost:8002/llm_health", timeout=2)
        if llm_health.status_code == 200:
            llm_data = llm_health.json()
            print("\n   LLM Providers Available:")
            for provider in ['openai', 'anthropic', 'google_gemini']:
                if llm_data.get(provider):
                    print(f"   ✅ {provider}")
    except:
        pass
    
    # Step 2: Download the PDF
    print("\n2. DOWNLOADING PDF...")
    pdf_path = download_arxiv_pdf(arxiv_id)
    if not pdf_path:
        return
    
    # Step 3: Send to Marker service
    print("\n3. SENDING TO MARKER SERVICE...")
    print("   Configuration:")
    print("   - output_format: markdown")
    print("   - use_llm: true")
    print("   - skip_tables: false")
    print("   - llm_light: false")
    print("   - paper_id: 999 (test)")
    
    start_time = time.time()
    
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': (os.path.basename(pdf_path), f, 'application/pdf')}
            data = {
                'output_format': 'markdown',
                'use_llm': 'true',
                'skip_tables': 'false',
                'llm_light': 'false',
                'paper_id': '999'  # Test paper ID for image extraction
            }
            
            print("\n   Sending request to http://localhost:8002/convert...")
            print("   (This may take several minutes for a 15-page paper with LLM)")
            
            response = requests.post(
                "http://localhost:8002/convert",
                files=files,
                data=data,
                timeout=1200  # 20 minutes
            )
    except requests.exceptions.Timeout:
        elapsed = int(time.time() - start_time)
        print(f"❌ Request timed out after {elapsed} seconds")
        return
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return
    
    elapsed = int(time.time() - start_time)
    print(f"\n   Response received after {elapsed} seconds")
    print(f"   Status code: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Marker returned error: {response.status_code}")
        print(f"   Response: {response.text[:500]}")
        return
    
    # Step 4: Analyze response
    print("\n4. ANALYZING RESPONSE...")
    try:
        result = response.json()
    except:
        print("❌ Response is not valid JSON")
        print(f"   Response: {response.text[:500]}")
        return
    
    # Check success
    if not result.get('success'):
        print(f"❌ Marker processing failed")
        print(f"   Detail: {result.get('detail', 'Unknown error')}")
        return
    
    print(f"✅ Processing successful")
    
    # Get content
    content = result.get('content', '')
    print(f"\n   Content Statistics:")
    print(f"   - Length: {len(content):,} characters")
    print(f"   - Lines: {content.count(chr(10)):,}")
    
    # Check for image references
    image_refs = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', content)
    api_refs = [src for _, src in image_refs if src.startswith('/api/')]
    local_refs = [src for _, src in image_refs if not src.startswith('/api/')]
    print(f"   - Image references: {len(image_refs)}")
    
    # Analyze image references
    if image_refs:
        print("\n   Image References Found:")
        
        for i, (alt, src) in enumerate(image_refs[:10]):  # Show first 10
            ref_type = "API URL" if src.startswith('/api/') else "Local"
            alt_display = (alt[:30] + "...") if alt else "[empty]"
            print(f"   {i+1}. [{ref_type}] {src}")
            print(f"      Alt: {alt_display}")
        
        print(f"\n   Reference Summary:")
        print(f"   - Local files: {len(local_refs)}")
        print(f"   - API URLs: {len(api_refs)}")
    
    # Check metadata
    metadata = result.get('metadata', {})
    if metadata:
        print(f"\n   Metadata:")
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)):
                print(f"   - {key}: {value}")
    
    # Check image extraction info
    print(f"\n   Image Extraction:")
    print(f"   - images: {result.get('images', 0)}")
    print(f"   - images_extracted: {result.get('images_extracted', 0)}")
    print(f"   - tables_skipped: {result.get('tables_skipped', False)}")
    print(f"   - llm_used: {result.get('llm_used', False)}")
    
    # Step 5: Test image API access (the real contract)
    print("\n5. TESTING IMAGE API ACCESS...")
    successful_fetches = 0
    if api_refs:
        # Test first few API URLs
        test_count = min(3, len(api_refs))
        print(f"   Testing {test_count} API URLs...")
        
        for i, test_url in enumerate(api_refs[:test_count]):
            full_url = f"http://localhost:8000{test_url}"
            
            print(f"\n   [{i+1}] Testing: {test_url}")
            try:
                img_response = requests.get(full_url, timeout=5)
                if img_response.status_code == 200:
                    successful_fetches += 1
                    print(f"      ✅ Accessible ({len(img_response.content):,} bytes)")
                    content_type = img_response.headers.get('content-type', '')
                    if content_type:
                        print(f"      Content-Type: {content_type}")
                else:
                    print(f"      ❌ HTTP {img_response.status_code}")
                    if img_response.status_code == 404:
                        print(f"      Hint: Check backend's image serving route")
            except Exception as e:
                print(f"      ❌ Failed: {e}")
        
        if successful_fetches == test_count:
            print(f"\n   ✅ All {test_count} tested images are accessible")
        elif successful_fetches > 0:
            print(f"\n   ⚠️ Only {successful_fetches}/{test_count} images accessible")
        else:
            print(f"\n   ❌ No images accessible via API")
    else:
        print("   No API URLs to test - images not rewritten")
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("-" * 60)
    
    success_items = []
    failure_items = []
    
    # Check each aspect
    if response.status_code == 200 and result.get('success'):
        success_items.append("Marker processing successful")
    else:
        failure_items.append("Marker processing failed")
    
    if len(content) > 1000:
        success_items.append(f"Markdown generated ({len(content):,} chars)")
    else:
        failure_items.append("Insufficient markdown content")
    
    if len(image_refs) > 0:
        success_items.append(f"Found {len(image_refs)} image references")
    else:
        failure_items.append("No image references in markdown")
    
    if len(api_refs) > 0:
        success_items.append(f"Images rewritten to API URLs ({len(api_refs)})")
    elif len(local_refs) > 0:
        failure_items.append(f"Images not rewritten ({len(local_refs)} local refs)")
    
    if result.get('images_extracted', 0) > 0:
        success_items.append(f"Images extracted: {result.get('images_extracted')}")
    else:
        failure_items.append("No images extracted (may be vector graphics)")
    
    if api_refs and successful_fetches > 0:
        if successful_fetches == len(api_refs[:3]):
            success_items.append(f"Images accessible via API ({successful_fetches}/{successful_fetches})")
        else:
            failure_items.append(f"Some images not accessible ({successful_fetches}/{min(3, len(api_refs))} tested)")
    
    if result.get('llm_used'):
        success_items.append("LLM enhancement used")
    
    print("\n✅ SUCCESSES:")
    for item in success_items or ["None"]:
        print(f"   - {item}")
    
    if failure_items:
        print("\n❌ FAILURES:")
        for item in failure_items:
            print(f"   - {item}")
        
        print("\n📋 RECOMMENDATIONS:")
        failure_str = str(failure_items)
        
        if "No images extracted" in failure_str:
            print("   • Check if PDF has bitmap images vs vector graphics")
            print("   • Review Marker logs for 'Figure/Image processor present'")
            print("   • Verify output_dir and disable_image_extraction=False in config")
        
        if "not rewritten" in failure_str:
            print("   • Check ImageManager integration in render_to_payload")
            print("   • Verify paper_id is being passed and processed")
            print("   • Check Marker logs for 'Image collection summary'")
        
        if "not accessible" in failure_str:
            print("   • Check backend's /api/papers/{id}/images/{filename} route")
            print("   • Verify ImageManager saved files to correct path structure")
            print("   • Check file permissions on data/paper_images/")
    
    print("\n" + "=" * 60)
    
    # Cleanup
    if pdf_path and os.path.exists(os.path.dirname(pdf_path)):
        shutil.rmtree(os.path.dirname(pdf_path))
        print(f"\n✅ Cleaned up temp files")

if __name__ == "__main__":
    test_marker_service_directly()