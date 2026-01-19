#!/usr/bin/env python3
"""
Test script for GPT-5 enhancements
Tests:
1. Retry status updates via progress callback
2. Enhanced JSON extraction
3. Response file logging
"""

import json
from pathlib import Path
from app.services.gpt5_tag_reorganizer import GPT5TagReorganizer

def test_progress_callback():
    """Test that progress callbacks are properly invoked"""
    print("\n=== Testing Progress Callback ===")
    
    # Track callback messages
    messages = []
    
    def progress_callback(msg):
        messages.append(msg)
        print(f"Callback: {msg}")
    
    # Initialize reorganizer
    reorganizer = GPT5TagReorganizer()
    
    # Test with a small set of tags
    test_tags = [
        {'tag': 'machine-learning', 'count': 10},
        {'tag': 'artificial-intelligence', 'count': 8},
        {'tag': 'deep-learning', 'count': 5}
    ]
    
    print("Calling reorganize_tags with progress callback...")
    result = reorganizer.reorganize_tags(test_tags, progress_callback=progress_callback)
    
    print(f"\nReceived {len(messages)} progress messages")
    return messages, result

def test_json_extraction():
    """Test enhanced JSON extraction from various formats"""
    print("\n=== Testing JSON Extraction ===")
    
    reorganizer = GPT5TagReorganizer()
    
    # Test case 1: JSON with markdown
    test_text1 = """
    Here is the result:
    
    ```json
    {
        "concepts": [
            {"slug": "ml", "display_name": "Machine Learning"}
        ],
        "aliases": []
    }
    ```
    """
    
    result1 = reorganizer._extract_json_from_text(test_text1)
    print(f"Test 1 (markdown): {'PASS' if result1 else 'FAIL'}")
    
    # Test case 2: Malformed JSON (trailing comma)
    test_text2 = '{"concepts": [{"slug": "ai"},], "aliases": []}'
    result2 = reorganizer._extract_json_from_text(test_text2)
    print(f"Test 2 (trailing comma): {'PASS' if result2 else 'FAIL'}")
    
    # Test case 3: JSON with extra text
    test_text3 = 'Some text before {"concepts": [], "aliases": []} and after'
    result3 = reorganizer._extract_json_from_text(test_text3)
    print(f"Test 3 (extra text): {'PASS' if result3 else 'FAIL'}")
    
    return [result1, result2, result3]

def test_response_logging():
    """Test that responses are saved to files"""
    print("\n=== Testing Response File Logging ===")
    
    reorganizer = GPT5TagReorganizer()
    
    # Test saving different types of responses
    test_content = "This is a test response from GPT-5"
    
    # Save as success response
    filepath1 = reorganizer._save_response_to_file(test_content, 'success')
    print(f"Saved success response to: {filepath1}")
    
    # Save as error response
    error_content = "Error: 502 Bad Gateway"
    filepath2 = reorganizer._save_response_to_file(error_content, 'error')
    print(f"Saved error response to: {filepath2}")
    
    # Verify files exist
    log_dir = Path('data/gpt5_responses')
    files = list(log_dir.glob('gpt5_*.txt'))
    print(f"\nFound {len(files)} response files in {log_dir}")
    
    # Show recent files
    for file in sorted(files)[-5:]:
        print(f"  - {file.name}")
    
    return files

def main():
    print("GPT-5 Enhancement Test Suite")
    print("=" * 50)
    
    # Test 1: Progress callbacks
    try:
        messages, result = test_progress_callback()
        print(f"✓ Progress callback test completed")
    except Exception as e:
        print(f"✗ Progress callback test failed: {e}")
    
    # Test 2: JSON extraction
    try:
        results = test_json_extraction()
        success_count = sum(1 for r in results if r is not None)
        print(f"✓ JSON extraction: {success_count}/3 tests passed")
    except Exception as e:
        print(f"✗ JSON extraction test failed: {e}")
    
    # Test 3: Response logging
    try:
        files = test_response_logging()
        print(f"✓ Response logging test completed")
    except Exception as e:
        print(f"✗ Response logging test failed: {e}")
    
    print("\n" + "=" * 50)
    print("Enhancement tests completed!")
    print("\nNote: GPT-5 responses will be saved to:")
    print("  backend/data/gpt5_responses/gpt5_<type>_<timestamp>.txt")
    print("\nTypes include:")
    print("  - success: Successful GPT-5 responses")
    print("  - error: Error responses from API")
    print("  - json_extraction_attempt: Raw text when JSON extraction is attempted")
    print("  - fallback_error: Errors from fallback attempts")

if __name__ == "__main__":
    main()