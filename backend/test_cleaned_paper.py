#!/usr/bin/env python3
"""
Test that paper processing properly cleans content
"""
import asyncio
from app.services.async_pdf_processor import get_async_pdf_processor

async def test_cleaned_processing():
    """Test that the async processor cleans content"""
    
    # Create a mock response that would come from Marker
    # Simulate what happens when we process the response
    from app.utils.content_cleaner import clean_markdown_content
    
    mock_markdown = """
# Test Paper

<answer>This is an answer that should be cleaned</answer>

Regular content here.

<solution>This solution tag should also be removed</solution>
"""
    
    print("Mock Markdown (before cleaning):")
    print("-" * 40)
    print(mock_markdown)
    
    cleaned = clean_markdown_content(mock_markdown)
    
    print("\nCleaned Markdown (after cleaning):")
    print("-" * 40)
    print(cleaned)
    
    # Verify no problematic tags remain
    problematic_tags = ['<answer>', '</answer>', '<solution>', '</solution>']
    issues_found = []
    
    for tag in problematic_tags:
        if tag.lower() in cleaned.lower():
            issues_found.append(tag)
    
    print("\nVerification:")
    print("-" * 40)
    if issues_found:
        print(f"❌ Found problematic tags: {issues_found}")
        return False
    else:
        print("✅ All problematic tags removed successfully")
        return True

if __name__ == "__main__":
    success = asyncio.run(test_cleaned_processing())
    exit(0 if success else 1)