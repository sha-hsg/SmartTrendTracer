"""
Test Marker service REST API integration
"""

import httpx
import asyncio
from pymongo import MongoClient

async def test_marker_api():
    # First check if Marker service is running
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8002/")
            print(f"Marker service status: {response.status_code}")
            if response.status_code == 200:
                print("Marker service is running!")
    except Exception as e:
        print(f"Marker service not available: {e}")
        return
    
    # Get a paper with PDF
    client = MongoClient("mongodb://localhost:27017/")
    db = client.smarttrendtracer
    
    paper = db.papers.find_one({"pdf_path": {"$exists": True, "$ne": None}})
    if not paper:
        print("No papers with PDF found")
        return
    
    paper_id = str(paper['_id'])
    print(f"\nTesting with paper: {paper.get('title', 'Unknown')}")
    print(f"Paper ID: {paper_id}")
    
    # Call our API endpoint to process with Marker
    async with httpx.AsyncClient(timeout=300.0) as client:
        url = f"http://localhost:8000/api/papers/{paper_id}/process-with-marker"
        print(f"\nCalling: POST {url}")
        
        try:
            response = await client.post(url)
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Success: {result['message']}")
                print(f"Content length: {result['content_length']} chars")
                print(f"Images found: {result.get('image_count', 0)}")
                print(f"Processing time: {result.get('processing_time', 0):.2f} seconds")
                
                # Check if paper was updated
                updated_paper = db.papers.find_one({"_id": paper['_id']})
                if updated_paper.get('processor_used') == 'marker_service':
                    print("\n✅ Paper successfully processed with Marker service!")
                    if updated_paper.get('marker_metadata'):
                        print(f"Marker metadata: {updated_paper['marker_metadata']}")
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Error calling API: {e}")

if __name__ == "__main__":
    asyncio.run(test_marker_api())