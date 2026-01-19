#!/usr/bin/env python3
"""
Test actual LLM API calls to verify provider routing and logging
"""
import os
import sys
import json
import time
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Import the service
from app.services.llm_service import get_llm_service

def test_different_providers():
    """Test that each provider actually uses its own API"""
    
    service = get_llm_service()
    
    print("\n=== Testing Different LLM Providers ===\n")
    
    # Test 1: Anthropic model (tag_suggestion)
    print("1. Testing Anthropic (Claude) for tag suggestions...")
    try:
        # Directly call the tag suggestion which uses Anthropic
        test_text = "OpenAI just released GPT-5 with amazing capabilities for reasoning."
        result = service.suggest_tags(test_text, "test_user")
        print(f"   ✓ Anthropic call successful - Tags: {result}")
    except Exception as e:
        print(f"   ✗ Anthropic call failed: {e}")
    
    time.sleep(1)
    
    # Test 2: Try to call a summarization (uses Anthropic)
    print("\n2. Testing summarization (Anthropic)...")
    try:
        result = service.get_completion(
            'article_summarization',
            title="Test Article",
            content="This is a test article about AI and machine learning advances in 2025."
        )
        if result:
            print(f"   ✓ Summarization successful")
            print(f"   Response preview: {result[:100]}...")
        else:
            print(f"   ✗ Summarization returned None")
    except Exception as e:
        print(f"   ✗ Summarization failed: {e}")
    
    time.sleep(1)
    
    # Test 3: Read the log file to check what was logged
    print("\n3. Checking log entries...")
    log_file = Path("../logs/backend.log")
    if log_file.exists():
        with open(log_file, 'r') as f:
            lines = f.readlines()
            # Look for recent LLM_USAGE entries
            llm_entries = [line for line in lines[-50:] if 'LLM' in line]
            if llm_entries:
                print("   Recent LLM log entries found:")
                for entry in llm_entries[-5:]:  # Show last 5 LLM-related entries
                    print(f"   {entry.strip()}")
            else:
                print("   No LLM log entries found in recent logs")
    else:
        print("   Log file not found")
    
    print("\n=== Test Complete ===")
    print("Check ../logs/backend.log for detailed LLM usage entries")

if __name__ == "__main__":
    test_different_providers()