#!/usr/bin/env python3
"""Test ArXiv import for paper 2508.10880"""

import requests
import json
import time

# Test the ArXiv import
url = "http://localhost:8000/api/arxiv/import"
data = {
    "url_or_id": "2508.10880",
    "process_pdf": True,
    "add_to_database": True
}

print("Testing ArXiv import for: 2508.10880")
print(f"Request data: {json.dumps(data, indent=2)}")

response = requests.post(url, json=data)
print(f"Response status: {response.status_code}")
print(f"Response data: {json.dumps(response.json(), indent=2)}")

if response.status_code == 200:
    result = response.json()
    if result.get('success'):
        paper_id = result.get('paper_id')
        print(f"\n✅ Paper imported successfully with ID: {paper_id}")
        
        # Wait for processing
        print("Waiting for processing to complete...")
        time.sleep(10)
        
        # Check paper status
        if paper_id:
            paper_url = f"http://localhost:8000/api/papers/{paper_id}"
            paper_response = requests.get(paper_url)
            if paper_response.status_code == 200:
                paper_data = paper_response.json()
                print(f"\nPaper status:")
                print(f"  - Processed: {paper_data.get('processed')}")
                print(f"  - Processor used: {paper_data.get('processor_used')}")
                print(f"  - Content length: {len(paper_data.get('content', ''))}")
                print(f"  - PDF path: {paper_data.get('pdf_path')}")
            else:
                print(f"Failed to get paper details: {paper_response.status_code}")
    else:
        print(f"❌ Import failed: {result.get('error')}")
else:
    print(f"❌ Request failed: {response.text}")