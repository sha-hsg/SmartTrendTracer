"""
Debug test for Marker service integration
"""

import httpx
import asyncio
from pymongo import MongoClient
import time

async def test_marker_processing():
    # Get a paper with PDF
    client = MongoClient("mongodb://localhost:27017/")
    db = client.smarttrendtracer
    
    # Find a paper with a PDF
    paper = db.papers.find_one({"pdf_path": {"$exists": True, "$ne": None}})
    if not paper:
        print("No papers with PDF found")
        return
    
    paper_id = str(paper['_id'])
    print(f"\n=== TESTING MARKER PROCESSING ===")
    print(f"Paper: {paper.get('title', 'Unknown')}")
    print(f"Paper ID: {paper_id}")
    print(f"PDF Path: {paper.get('pdf_path')}")
    
    # Reset processing status
    db.papers.update_one(
        {'_id': paper['_id']},
        {'$set': {
            'processing_status': None,
            'processing_error': None
        }}
    )
    print("Reset processing status")
    
    # Start processing
    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"http://localhost:8000/api/papers/{paper_id}/process-with-marker"
        print(f"\nCalling: POST {url}")
        
        response = await client.post(url)
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {result}")
        else:
            print(f"Error: {response.text}")
            return
    
    # Monitor status
    print("\n=== MONITORING STATUS ===")
    for i in range(30):  # Check for 5 minutes
        time.sleep(10)  # Wait 10 seconds
        
        # Check status
        async with httpx.AsyncClient() as client:
            status_url = f"http://localhost:8000/api/papers/{paper_id}/processing-status"
            response = await client.get(status_url)
            if response.status_code == 200:
                status = response.json()
                print(f"\n[{i*10}s] Status: {status['status']}")
                if status['status'] == 'processing_with_marker':
                    print(f"  Elapsed: {status.get('elapsed_minutes', 0)} minutes")
                elif status['status'] == 'completed':
                    print(f"  ✅ Processing completed!")
                    print(f"  Processor: {status.get('processor_used')}")
                    if status.get('marker_metadata'):
                        print(f"  Metadata: {status['marker_metadata']}")
                    break
                elif status['status'] == 'failed':
                    print(f"  ❌ Processing failed!")
                    print(f"  Error: {status.get('error')}")
                    break
    
    # Check database directly
    print("\n=== FINAL DATABASE STATE ===")
    updated_paper = db.papers.find_one({'_id': paper['_id']})
    print(f"Processing status: {updated_paper.get('processing_status')}")
    print(f"Processed: {updated_paper.get('processed')}")
    print(f"Processor used: {updated_paper.get('processor_used')}")
    if updated_paper.get('content'):
        print(f"Content length: {len(updated_paper['content'])} chars")
    if updated_paper.get('processing_error'):
        print(f"Error: {updated_paper['processing_error']}")

if __name__ == "__main__":
    print("Starting Marker debug test...")
    print("Check the backend logs for detailed debug output!")
    print("=" * 50)
    asyncio.run(test_marker_processing())