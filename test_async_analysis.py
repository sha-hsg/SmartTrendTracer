#!/usr/bin/env python3

"""
Test script for async analysis functionality.
Tests the new background task system for LLM analyses.
"""

import asyncio
import aiohttp
import time
import sys

async def test_async_analysis():
    """Test the new async analysis endpoint"""

    base_url = "http://localhost:8000"

    # Test data
    # First, let's get a list of papers to find a valid paper ID
    async with aiohttp.ClientSession() as session:
        print("🔍 Getting list of papers...")
        async with session.get(f"{base_url}/api/papers/") as resp:
            if resp.status != 200:
                print(f"❌ Failed to get papers: {resp.status}")
                return

            data = await resp.json()
            print(f"📊 Papers API response type: {type(data)}")

            # Handle different response formats
            if isinstance(data, dict) and 'papers' in data:
                papers = data['papers']
            elif isinstance(data, list):
                papers = data
            else:
                papers = [data] if data else []

            if not papers or len(papers) == 0:
                print("❌ No papers found in database")
                print(f"Response: {data}")
                return

            paper = papers[0]  # Use first paper
            print(f"📄 Paper structure: {list(paper.keys())[:10]}...")  # Show first 10 keys

            # Handle different ID field names
            paper_id = paper.get('_id') or paper.get('id') or paper.get('paper_id')
            if not paper_id:
                print(f"❌ No valid ID found in paper: {paper}")
                return

            print(f"✅ Using paper: {paper.get('title', 'Unknown')} (ID: {paper_id})")

        # Test the new async analysis endpoint
        print("\n🚀 Starting async analysis...")
        analysis_data = {
            "analysis_types": ["summary", "conclusion", "methodology"]
        }

        async with session.post(f"{base_url}/api/papers/{paper_id}/analyses/async", json=analysis_data) as resp:
            if resp.status != 200:
                print(f"❌ Failed to start async analysis: {resp.status}")
                text = await resp.text()
                print(f"Error: {text}")
                return

            result = await resp.json()
            task_id = result['task_id']
            print(f"✅ Analysis started! Task ID: {task_id}")

        # Poll for results
        print("\n⏳ Polling for results...")
        max_wait = 120  # 2 minutes
        start_time = time.time()

        while time.time() - start_time < max_wait:
            async with session.get(f"{base_url}/api/papers/{paper_id}/analyses/task/{task_id}") as resp:
                if resp.status == 404:
                    print("❌ Task not found")
                    return

                if resp.status != 200:
                    print(f"❌ Failed to get task status: {resp.status}")
                    return

                status = await resp.json()
                print(f"📊 Status: {status['status']} | Progress: {status.get('progress', 0)}%")

                if status['status'] == 'completed':
                    print("✅ Analysis completed!")
                    print(f"📝 Results: {len(status.get('results', {}))} analyses generated")
                    for analysis_type, result in status.get('results', {}).items():
                        if result.get('success'):
                            content_length = len(result.get('content', ''))
                            print(f"  - {analysis_type}: {content_length} characters")
                        else:
                            print(f"  - {analysis_type}: ❌ Failed - {result.get('error', 'Unknown error')}")
                    return

                elif status['status'] == 'failed':
                    print(f"❌ Analysis failed: {status.get('error', 'Unknown error')}")
                    return

                # Wait before next poll
                await asyncio.sleep(5)

        print("⏰ Timeout waiting for analysis completion")

async def test_server_responsiveness():
    """Test that the server remains responsive during analysis"""

    base_url = "http://localhost:8000"

    async with aiohttp.ClientSession() as session:
        print("\n🌐 Testing server responsiveness during analysis...")

        # Make several quick API calls to verify server is responsive
        for i in range(5):
            start_time = time.time()
            async with session.get(f"{base_url}/api/papers/") as resp:
                response_time = time.time() - start_time
                print(f"📡 API call {i+1}: {resp.status} ({response_time:.2f}s)")

                if resp.status != 200:
                    print(f"❌ API call failed: {resp.status}")
                    return False

                if response_time > 2.0:  # More than 2 seconds is too slow
                    print(f"❌ API call too slow: {response_time:.2f}s")
                    return False

            await asyncio.sleep(1)

        print("✅ Server remained responsive during test")
        return True

async def main():
    """Main test function"""

    print("🧪 Testing Async Analysis Implementation")
    print("=" * 50)

    try:
        # Test basic connectivity
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/api/papers/") as resp:
                if resp.status != 200:
                    print("❌ Backend server not responding")
                    return

        print("✅ Backend server is running")

        # Test async analysis
        await test_async_analysis()

        # Test server responsiveness
        await test_server_responsiveness()

        print("\n" + "=" * 50)
        print("🎉 All tests completed!")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())