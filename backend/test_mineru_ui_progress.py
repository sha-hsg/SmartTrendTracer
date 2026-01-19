#!/usr/bin/env python3
"""Test MinerU processing with UI progress updates"""

import requests
import asyncio
import time
import json
from pathlib import Path

async def test_mineru_with_progress():
    """Test MinerU processing and monitor progress updates"""
    
    # Configuration
    API_URL = "http://localhost:8000"
    PAPER_ID = "68ab70fe3e0caac2fd0ef9e6"  # MongoDB ObjectId
    
    print("MinerU UI Progress Test")
    print("=" * 60)
    
    # Step 1: Check paper status
    print("\n1. Checking paper status...")
    response = requests.get(f"{API_URL}/api/papers/{PAPER_ID}")
    if response.status_code != 200:
        print(f"❌ Paper not found: {PAPER_ID}")
        return
    
    paper = response.json()
    print(f"✅ Found paper: {paper.get('title', 'Unknown')[:50]}...")
    print(f"   Current processor: {paper.get('processor_used', 'None')}")
    print(f"   Processing status: {paper.get('processing_status', 'Not set')}")
    
    # Step 2: Start MinerU processing
    print("\n2. Starting MinerU processing...")
    response = requests.post(f"{API_URL}/api/papers/{PAPER_ID}/process-with-mineru")
    if response.status_code != 200:
        print(f"❌ Failed to start MinerU: {response.text}")
        return
    
    result = response.json()
    print(f"✅ MinerU processing started: {result}")
    
    # Step 3: Monitor progress
    print("\n3. Monitoring progress (this will take 15-20 minutes)...")
    print("   Progress updates should appear below:")
    print("-" * 40)
    
    last_status = None
    last_progress = 0
    start_time = time.time()
    
    while True:
        try:
            # Check processing status
            response = requests.get(f"{API_URL}/api/papers/{PAPER_ID}/processing-status")
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                progress_msg = data.get('progress_message', '')
                progress_pct = data.get('progress_percentage', 0)
                elapsed = data.get('elapsed_minutes', 0)
                
                # Show updates when something changes
                if status != last_status or progress_pct != last_progress:
                    current_time = time.strftime("%H:%M:%S")
                    
                    if status != last_status:
                        print(f"\n[{current_time}] Status: {status}")
                        last_status = status
                    
                    if progress_msg:
                        bar_width = 30
                        filled = int(bar_width * progress_pct / 100)
                        bar = '█' * filled + '░' * (bar_width - filled)
                        print(f"[{current_time}] {bar} {progress_pct:3.0f}% - {progress_msg}")
                        last_progress = progress_pct
                    
                    if elapsed:
                        print(f"             Elapsed: {elapsed} minutes")
                
                # Check if completed or failed
                if status in ['completed', 'failed', 'cancelled']:
                    print("-" * 40)
                    print(f"\n✅ Processing {status}!")
                    
                    if status == 'completed':
                        # Fetch updated paper data
                        response = requests.get(f"{API_URL}/api/papers/{PAPER_ID}")
                        if response.status_code == 200:
                            paper = response.json()
                            print(f"   Processor used: {paper.get('processor_used', 'Unknown')}")
                            
                            # Check if markdown content is available
                            if paper.get('markdown_content'):
                                content_len = len(paper['markdown_content'])
                                print(f"   Markdown content: {content_len} characters")
                            
                            # Check metadata
                            metadata = paper.get('metadata', {})
                            if metadata:
                                images = metadata.get('images_extracted', 0)
                                print(f"   Images extracted: {images}")
                    
                    break
                
            # Wait before next check
            await asyncio.sleep(5)  # Check every 5 seconds
            
        except KeyboardInterrupt:
            print("\n\n⚠️ Test interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Error checking status: {e}")
            break
    
    total_time = (time.time() - start_time) / 60
    print(f"\nTotal time: {total_time:.1f} minutes")
    print("=" * 60)

if __name__ == "__main__":
    print("Starting MinerU UI Progress Test...")
    print("This will process a paper with MinerU and show progress updates")
    print("Press Ctrl+C to stop monitoring\n")
    
    # Run the async test
    asyncio.run(test_mineru_with_progress())