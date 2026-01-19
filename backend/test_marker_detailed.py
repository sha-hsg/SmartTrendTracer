#!/usr/bin/env python3
"""
Detailed test of Marker service with image extraction
Tests a paper known to have many figures
"""
import requests
import json
import time
import os
from pathlib import Path

def test_arxiv_import_with_images():
    """Test importing a paper with lots of images"""
    
    # Use a well-known computer vision paper with many figures
    # "Attention Is All You Need" - has architecture diagrams
    arxiv_id = "1706.03762"
    
    print("=" * 60)
    print("MARKER IMAGE EXTRACTION TEST")
    print("=" * 60)
    print(f"ArXiv ID: {arxiv_id}")
    print("Paper: 'Attention Is All You Need' (Transformer paper)")
    print("Expected: Multiple architecture diagrams and figures")
    print("-" * 60)
    
    # Step 1: Import the paper
    print("\n1. IMPORTING PAPER FROM ARXIV...")
    import_response = requests.post(
        "http://localhost:8000/api/arxiv/import",
        json={
            "url_or_id": arxiv_id,
            "processor": "marker"
        }
    )
    
    if import_response.status_code != 200:
        print(f"❌ Import failed: {import_response.status_code}")
        print(f"   Response: {import_response.text}")
        return
    
    result = import_response.json()
    paper_id = result.get("paper_id")
    print(f"✅ Paper imported with ID: {paper_id}")
    print(f"   Title: {result.get('title', 'N/A')}")
    
    # Step 2: Wait for processing
    print("\n2. WAITING FOR PROCESSING...")
    max_wait = 600  # 10 minutes
    check_interval = 10
    elapsed = 0
    
    while elapsed < max_wait:
        # Check if paper is processed
        paper_response = requests.get(f"http://localhost:8000/api/papers/{paper_id}")
        if paper_response.status_code == 200:
            paper_data = paper_response.json()
            if paper_data.get("processed"):
                print(f"✅ Processing complete after {elapsed} seconds")
                break
        
        print(f"   Processing... ({elapsed}s elapsed)")
        time.sleep(check_interval)
        elapsed += check_interval
    else:
        print(f"⚠️ Processing timed out after {max_wait} seconds")
    
    # Step 3: Check paper content
    print("\n3. ANALYZING PAPER CONTENT...")
    paper_response = requests.get(f"http://localhost:8000/api/papers/{paper_id}")
    if paper_response.status_code != 200:
        print(f"❌ Failed to get paper: {paper_response.status_code}")
        return
    
    paper_data = paper_response.json()
    
    # Get markdown content directly from database
    import sqlite3
    conn = sqlite3.connect("data/tweets.db")
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM papers WHERE id = ?", (paper_id,))
    content = cursor.fetchone()
    conn.close()
    
    if content and content[0]:
        markdown = content[0]
        print(f"   Markdown length: {len(markdown)} characters")
        
        # Count image references
        import re
        image_refs = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', markdown)
        print(f"   Image references found: {len(image_refs)}")
        
        if image_refs:
            print("\n   First 5 image references:")
            for i, (alt, src) in enumerate(image_refs[:5]):
                print(f"   {i+1}. Alt: '{alt[:50]}...' if alt else '[empty]'")
                print(f"      Src: {src}")
        
        # Check what type of references they are
        local_refs = [src for alt, src in image_refs if not src.startswith('/api/')]
        api_refs = [src for alt, src in image_refs if src.startswith('/api/')]
        
        print(f"\n   Reference types:")
        print(f"   - Local references: {len(local_refs)}")
        print(f"   - API references: {len(api_refs)}")
    else:
        print("   ❌ No markdown content found")
    
    # Step 4: Check actual image files
    print("\n4. CHECKING IMAGE FILES...")
    
    # Check paper_images directory
    paper_image_dir = Path(f"data/paper_images/{str(paper_id).zfill(6)[:2]}/{str(paper_id).zfill(6)[2:4]}/{str(paper_id).zfill(6)[4:]}")
    
    if paper_image_dir.exists():
        image_files = list(paper_image_dir.glob("*"))
        print(f"   Image directory: {paper_image_dir}")
        print(f"   Images saved: {len(image_files)}")
        
        if image_files:
            print("\n   Saved image files:")
            for i, img_file in enumerate(image_files[:5]):
                size = img_file.stat().st_size
                print(f"   {i+1}. {img_file.name} ({size:,} bytes)")
    else:
        print(f"   ❌ No image directory found at: {paper_image_dir}")
    
    # Step 5: Test image API access
    print("\n5. TESTING IMAGE API ACCESS...")
    
    if image_refs and len(api_refs) > 0:
        # Test first API reference
        test_url = api_refs[0]
        if test_url.startswith('/api/'):
            full_url = f"http://localhost:8000{test_url}"
            img_response = requests.get(full_url)
            print(f"   Testing: {test_url}")
            print(f"   Status: {img_response.status_code}")
            if img_response.status_code == 200:
                print(f"   ✅ Image accessible ({len(img_response.content):,} bytes)")
            else:
                print(f"   ❌ Image not accessible: {img_response.text[:100]}")
    elif image_refs and len(local_refs) > 0:
        print("   ⚠️ Images have local references, not API URLs")
        print("   This means ImageManager didn't process them")
    else:
        print("   ❌ No image references to test")
    
    # Step 6: Marker service logs
    print("\n6. MARKER SERVICE STATUS...")
    try:
        health = requests.get("http://localhost:8002/health", timeout=1)
        if health.status_code == 200:
            print(f"   ✅ Marker service is healthy")
        else:
            print(f"   ⚠️ Marker service status: {health.status_code}")
    except:
        print("   ❌ Marker service not responding")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("-" * 60)
    
    success_items = []
    failure_items = []
    
    if paper_id:
        success_items.append("Paper imported successfully")
    else:
        failure_items.append("Paper import failed")
    
    if paper_data.get("processed"):
        success_items.append("Paper processed by Marker")
    else:
        failure_items.append("Paper not processed")
    
    if markdown and len(markdown) > 0:
        success_items.append(f"Markdown generated ({len(markdown):,} chars)")
    else:
        failure_items.append("No markdown content")
    
    if len(image_refs) > 0:
        success_items.append(f"Found {len(image_refs)} image references")
    else:
        failure_items.append("No image references in markdown")
    
    if len(api_refs) > 0:
        success_items.append(f"Images rewritten to API URLs ({len(api_refs)})")
    else:
        failure_items.append("Images not rewritten to API URLs")
    
    if paper_image_dir.exists() and len(list(paper_image_dir.glob("*"))) > 0:
        success_items.append(f"Images saved to disk ({len(list(paper_image_dir.glob('*')))})")
    else:
        failure_items.append("No images saved to disk")
    
    print("\n✅ SUCCESSES:")
    for item in success_items:
        print(f"   - {item}")
    
    if failure_items:
        print("\n❌ FAILURES:")
        for item in failure_items:
            print(f"   - {item}")
    
    print("\n" + "=" * 60)
    
    return {
        "paper_id": paper_id,
        "processed": paper_data.get("processed", False),
        "markdown_length": len(markdown) if markdown else 0,
        "image_refs": len(image_refs),
        "api_refs": len(api_refs),
        "local_refs": len(local_refs),
        "saved_images": len(list(paper_image_dir.glob("*"))) if paper_image_dir.exists() else 0
    }

if __name__ == "__main__":
    test_arxiv_import_with_images()