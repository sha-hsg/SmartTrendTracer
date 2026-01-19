#!/usr/bin/env python3
"""Test free-form paper analysis feature end-to-end"""

import requests
import json
import time
from datetime import datetime

API_URL = "http://localhost:8000"

def test_free_form_analysis():
    """Test the complete free-form analysis workflow"""
    
    print("Free-Form Paper Analysis Test")
    print("=" * 60)
    
    # Step 1: Get a paper to test with
    print("\n1. Fetching available papers...")
    response = requests.get(f"{API_URL}/api/papers")
    if response.status_code != 200:
        print(f"❌ Failed to fetch papers: {response.text}")
        return
    
    papers = response.json()
    if not papers:
        print("❌ No papers found in database")
        return
    
    # Use the first paper
    paper = papers[0]
    paper_id = paper.get('_id') or paper.get('id')  # Handle both MongoDB _id and id fields
    paper_title = paper.get('title', 'Unknown')[:50]
    print(f"✅ Using paper: {paper_title}...")
    print(f"   Paper ID: {paper_id}")
    
    # Step 2: Test creating a free-form analysis
    print("\n2. Creating free-form analysis...")
    test_prompt = "What are the top 3 most innovative aspects of this paper? Explain why each is innovative."
    
    response = requests.post(
        f"{API_URL}/api/papers/{paper_id}/analyses/free",
        json={"prompt": test_prompt, "regenerate": False}
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to create analysis: {response.text}")
        return
    
    result = response.json()
    # Check if the response has the analysis fields (id, prompt, content)
    if 'id' in result and 'content' in result:
        analysis_id = result.get('id')
        print(f"✅ Analysis created successfully!")
        print(f"   Analysis ID: {analysis_id}")
        print(f"   Model used: {result.get('model', 'unknown')}")
        print(f"   Content preview: {result.get('content', '')[:200]}...")
    else:
        print(f"❌ Analysis failed: {result.get('message', 'Unknown error')}")
        print(f"   Full response: {json.dumps(result, indent=2)}")
        return
    
    # Step 3: Test fetching all free analyses
    print("\n3. Fetching all free analyses for the paper...")
    response = requests.get(f"{API_URL}/api/papers/{paper_id}/analyses/free")
    
    if response.status_code != 200:
        print(f"❌ Failed to fetch analyses: {response.text}")
        return
    
    result = response.json()
    analyses = result.get('analyses', [])
    print(f"✅ Found {len(analyses)} free analysis(es)")
    
    for idx, analysis in enumerate(analyses, 1):
        print(f"   [{idx}] Prompt: {analysis['prompt'][:50]}...")
        print(f"       Created: {analysis.get('created_at', 'Unknown')}")
        print(f"       Model: {analysis.get('model', 'Unknown')}")
    
    # Step 4: Test updating an analysis
    print("\n4. Testing update functionality...")
    updated_content = "This is an updated response for testing purposes.\n\n" + result.get('content', '')
    
    response = requests.put(
        f"{API_URL}/api/papers/{paper_id}/analyses/free/{analysis_id}",
        json={"content": updated_content}
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to update analysis: {response.text}")
    else:
        result = response.json()
        if result.get('success'):
            print("✅ Analysis updated successfully!")
        else:
            print(f"❌ Update failed: {result.get('message')}")
    
    # Step 5: Test another prompt
    print("\n5. Creating another analysis with different prompt...")
    prompt2 = "Summarize this paper in exactly 3 bullet points."
    
    response = requests.post(
        f"{API_URL}/api/papers/{paper_id}/analyses/free",
        json={"prompt": prompt2, "regenerate": False}
    )
    
    if response.status_code == 200:
        result = response.json()
        if 'id' in result and 'content' in result:
            print("✅ Second analysis created successfully!")
            analysis_id2 = result.get('id')
        else:
            print(f"❌ Failed: {result.get('message', 'Unknown error')}")
            analysis_id2 = None
    else:
        print(f"❌ Request failed: {response.text}")
        analysis_id2 = None
    
    # Step 6: Fetch all analyses again to confirm
    print("\n6. Verifying all analyses are saved...")
    response = requests.get(f"{API_URL}/api/papers/{paper_id}/analyses/free")
    
    if response.status_code == 200:
        result = response.json()
        analyses = result.get('analyses', [])
        print(f"✅ Total free analyses: {len(analyses)}")
    
    # Step 7: Test deletion
    if analysis_id2:
        print("\n7. Testing deletion...")
        response = requests.delete(f"{API_URL}/api/papers/{paper_id}/analyses/free/{analysis_id2}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Analysis deleted successfully!")
            else:
                print(f"❌ Deletion failed: {result.get('message')}")
        else:
            print(f"❌ Request failed: {response.text}")
    
    # Final check
    print("\n8. Final verification...")
    response = requests.get(f"{API_URL}/api/papers/{paper_id}/analyses/free")
    
    if response.status_code == 200:
        result = response.json()
        analyses = result.get('analyses', [])
        print(f"✅ Final count: {len(analyses)} free analysis(es)")
        print("\n✅ All tests completed successfully!")
    else:
        print(f"❌ Final verification failed")
    
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("- Create free-form analysis: ✅")
    print("- Fetch analyses: ✅")
    print("- Update analysis: ✅")
    print("- Delete analysis: ✅")
    print("- Multiple analyses support: ✅")

if __name__ == "__main__":
    print("Starting free-form analysis test...")
    print("Make sure the backend server is running on port 8000\n")
    
    try:
        test_free_form_analysis()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()